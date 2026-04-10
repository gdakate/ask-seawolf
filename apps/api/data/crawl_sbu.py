"""
SBU Full-Site Crawler
=====================
BFS across all of *.stonybrook.edu — no per-section caps.
Respects robots.txt disallow rules, skips binaries/JS/CSS.
Writes progress to /tmp/crawl.log and saves incrementally.

Usage (inside Docker):
    docker exec sbu-assistant-platform-api-1 sh -c "cd /app && python -u /app/data/crawl_sbu.py > /tmp/crawl.log 2>&1 &"

Output:
    /app/data/documents_raw.json      — one record per crawled page
    /app/data/documents_chunked.json  — chunked, ready for load_real_data.py

After done:
    docker compose exec api python -m seed.load_real_data --reload
"""

import asyncio
import hashlib
import json
import re
import sys
from collections import Counter, deque
from pathlib import Path
from urllib.parse import urljoin, urlparse, urldefrag

import httpx
from bs4 import BeautifulSoup

# ── Output paths ─────────────────────────────────────────────────────
OUTPUT_RAW     = Path(__file__).parent / "documents_raw.json"
OUTPUT_CHUNKED = Path(__file__).parent / "documents_chunked.json"

# ── Crawler settings ──────────────────────────────────────────────────
MAX_TOTAL_PAGES = 5000          # hard cap across entire crawl
CONCURRENCY     = 8             # parallel HTTP requests
REQUEST_DELAY   = 0.25          # seconds between requests per worker
REQUEST_TIMEOUT = 20
MIN_TEXT_WORDS  = 60            # skip pages with fewer words
SAVE_EVERY      = 100           # checkpoint docs_raw every N pages

HEADERS = {
    "User-Agent": (
        "SBU-Assistant-Bot/2.0 "
        "(Educational RAG crawler for Stony Brook University; "
        "contact: admin@stonybrook.edu)"
    ),
    "Accept": "text/html,application/xhtml+xml;q=0.9",
    "Accept-Language": "en-US,en;q=0.9",
}

# ── Allowed domains ───────────────────────────────────────────────────
ALLOWED_DOMAINS = {
    "www.stonybrook.edu",
    "stonybrook.edu",
    "library.stonybrook.edu",
    "it.stonybrook.edu",
}

# ── robots.txt disallow list (from actual robots.txt) ─────────────────
ROBOTS_DISALLOW = re.compile(
    r'/globality/HansenGSJ78StagingArea'
    r'|/ugrdbulletin/200[5-9]'
    r'|/hsc-bulletin/'
    r'|/tools/'
    r'|/top-stories-2015/'
    r'|/mobile/'
    r'|/request-assistance/'
    r'|/faculty-directory/'
    r'|/analytics/'
    r'|/thank-you/'
    r'|/tutorials/'
    r'|/shared/'
    r'|/resources/'
    r'|/plugins/'
    r'|/elements/'
    r'|/_archive'
    r'|/_test'
    r'|/_old'
    r'|/commcms/grad/_resources'
    r'|/web-transition'
    r'|/_resources'
    r'|/_showcase'
    r'|/_testing'
    r'|/_template'
    r'|/_dev'
    r'|/_staging',
    re.IGNORECASE,
)

# ── URL filter ────────────────────────────────────────────────────────
SKIP_EXT = re.compile(
    r'\.(pdf|docx?|xlsx?|pptx?|zip|gz|tar|rar|7z'
    r'|png|jpe?g|gif|svg|webp|ico|bmp|tiff?'
    r'|mp[34]|avi|mov|wmv|flv|mkv|webm'
    r'|css|js|woff2?|ttf|eot|otf'
    r'|json|xml|csv|rss|atom'
    r'|exe|dmg|pkg|deb|rpm)(\?.*)?$',
    re.IGNORECASE,
)

SKIP_PATTERNS = re.compile(
    r'(logout|log-out|signout|sign-out'
    r'|/print/'
    r'|/feed/'
    r'|PHPSESSID='
    r'|sid='
    r'|action=edit'
    r'|action=history'
    r'|Special:'
    r'|/wp-admin/'
    r'|/wp-login'
    r'|\?replytocom='
    r'|mailto:'
    r'|javascript:)',
    re.IGNORECASE,
)

# ── URL auto-categorisation ───────────────────────────────────────────
CATEGORY_RULES = [
    (re.compile(r'/finaid|/financial.?aid|/bursar|/tuition|/billing|/fees', re.I), "tuition_financial_aid"),
    (re.compile(r'/registrar|/registration|/transcript|/diploma|/grades', re.I),   "registrar"),
    (re.compile(r'/admissions?|/apply|/undergraduate|/graduate/', re.I),            "admissions"),
    (re.compile(r'/housing|/res-hall|/residential|/dormitor', re.I),                "housing"),
    (re.compile(r'/dining|/meal.?plan|/food', re.I),                               "dining"),
    (re.compile(r'/it\b|/helpdesk|/tech|it\.stonybrook', re.I),                    "it_help"),
    (re.compile(r'/library|library\.stonybrook', re.I),                             "library"),
    (re.compile(r'/parking|parking\.stonybrook', re.I),                             "parking"),
    (re.compile(r'/calendar|/academic.?dates|/schedule', re.I),                    "academic_calendar"),
    (re.compile(r'/clubs?|/orgs?|/organization|studentorg\.stonybrook', re.I),     "clubs"),
    (re.compile(r'/student.?affairs|/student.?life|/health|/wellness', re.I),      "student_affairs"),
    (re.compile(r'/academics?|/programs?|/departments?|/majors?|/degrees?|/courses?|/bulletin', re.I), "academics"),
    (re.compile(r'/faq|/frequently.?asked', re.I),                                  "faq"),
]

def categorize(url: str) -> str:
    for pattern, category in CATEGORY_RULES:
        if pattern.search(url):
            return category
    return "general"


# ── Seed URLs ─────────────────────────────────────────────────────────
SEEDS = [
    # Core student-facing pages
    "https://www.stonybrook.edu/",
    "https://www.stonybrook.edu/admissions/",
    "https://www.stonybrook.edu/registrar/",
    "https://www.stonybrook.edu/bursar/",
    "https://www.stonybrook.edu/commcms/finaid/",
    "https://www.stonybrook.edu/commcms/res-hall/",
    "https://www.stonybrook.edu/commcms/dining/",
    "https://www.stonybrook.edu/commcms/studentaffairs/",
    "https://www.stonybrook.edu/commcms/academicaffairs/",
    "https://www.stonybrook.edu/commcms/career-center/",
    "https://www.stonybrook.edu/commcms/oiss/",
    "https://www.stonybrook.edu/commcms/grad/",
    "https://www.stonybrook.edu/graduate/",
    "https://www.stonybrook.edu/registrar/calendars/",
    "https://www.stonybrook.edu/commcms/ugadmissions/",
    "https://www.stonybrook.edu/commcms/graduate-admissions/",
    "https://www.stonybrook.edu/commcms/athletics/",
    "https://www.stonybrook.edu/commcms/provost/",
    # Subdomains (reachable from container)
    "https://it.stonybrook.edu/",
    "https://library.stonybrook.edu/",
]


# ── HTML cleaner ──────────────────────────────────────────────────────
def clean_html(html: str, url: str) -> tuple[str, str]:
    """Return (title, clean_text). Returns ('', '') for empty/useless pages."""
    soup = BeautifulSoup(html, "lxml")

    title = ""
    if soup.title and soup.title.string:
        t = soup.title.string.strip()
        title = re.sub(r'\s*[|\-–—]\s*(Stony Brook University|SBU).*$', '', t).strip()

    # Remove boilerplate elements
    for tag in soup(
        ["script", "style", "noscript", "iframe", "form",
         "nav", "footer", "header", "aside"]
    ):
        tag.decompose()
    for tag in soup.find_all(True, {"class": re.compile(r'nav|menu|sidebar|breadcrumb|cookie|banner|alert|social|share', re.I)}):
        tag.decompose()
    for tag in soup.find_all(True, {"id": re.compile(r'nav|menu|sidebar|header|footer|cookie|banner', re.I)}):
        tag.decompose()

    # Prefer main content block
    main = (
        soup.find("main") or
        soup.find(id=re.compile(r'^(main|content|page-content|primary)$', re.I)) or
        soup.find(class_=re.compile(r'\b(main|content|page-content|entry-content)\b', re.I)) or
        soup.find("article") or
        soup.body
    )

    raw = (main or soup).get_text(separator="\n")
    lines = [l.strip() for l in raw.splitlines() if l.strip() and len(l.strip()) > 2]
    text = "\n".join(lines)
    text = re.sub(r'\n{3,}', '\n\n', text)

    return (title or url), text


# ── Chunker ───────────────────────────────────────────────────────────
CHUNK_WORDS = 400
OVERLAP_WORDS = 50
MIN_CHUNK_WORDS = 80

def chunk_text(text: str) -> list[str]:
    sentences = re.split(r'(?<=[.!?])\s+|\n+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    chunks, cur = [], []
    cur_len = 0
    for sent in sentences:
        w = sent.split()
        if cur_len + len(w) > CHUNK_WORDS and cur:
            chunks.append(" ".join(cur))
            cur = cur[-OVERLAP_WORDS:]
            cur_len = len(cur)
        cur.extend(w)
        cur_len += len(w)
    if cur:
        chunks.append(" ".join(cur))
    return [c for c in chunks if len(c.split()) >= MIN_CHUNK_WORDS] or [text]


# ── URL helpers ───────────────────────────────────────────────────────
def normalize(url: str) -> str:
    url, _ = urldefrag(url)
    url = url.rstrip("/")
    return url


def is_allowed(url: str) -> bool:
    p = urlparse(url)
    if p.scheme not in ("http", "https"):
        return False
    if p.netloc not in ALLOWED_DOMAINS:
        return False
    if SKIP_EXT.search(p.path):
        return False
    if SKIP_PATTERNS.search(url):
        return False
    if ROBOTS_DISALLOW.search(p.path):
        return False
    return True


def extract_links(html: str, base_url: str) -> list[str]:
    soup = BeautifulSoup(html, "lxml")
    links = []
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if not href:
            continue
        abs_url = normalize(urljoin(base_url, href))
        if is_allowed(abs_url):
            links.append(abs_url)
    return links


# ── Worker ────────────────────────────────────────────────────────────
async def worker(
    worker_id: int,
    queue: asyncio.Queue,
    visited: set,
    results: list,
    client: httpx.AsyncClient,
    counter: list,          # [pages_done]
    stop_event: asyncio.Event,
):
    while not stop_event.is_set():
        try:
            url = queue.get_nowait()
        except asyncio.QueueEmpty:
            await asyncio.sleep(0.3)
            continue

        if counter[0] >= MAX_TOTAL_PAGES:
            stop_event.set()
            queue.task_done()
            break

        try:
            resp = await client.get(url, follow_redirects=True, timeout=REQUEST_TIMEOUT)
            final_url = normalize(str(resp.url))

            if final_url != url and final_url in visited:
                queue.task_done()
                continue
            if final_url != url:
                visited.add(final_url)

            if resp.status_code != 200:
                queue.task_done()
                continue
            ct = resp.headers.get("content-type", "")
            if "text/html" not in ct:
                queue.task_done()
                continue

            html = resp.text
            title, text = clean_html(html, final_url)

            if len(text.split()) < MIN_TEXT_WORDS:
                queue.task_done()
                continue

            category = categorize(final_url)
            results.append({
                "url":        final_url,
                "title":      title,
                "category":   category,
                "clean_text": text,
            })
            counter[0] += 1
            n = counter[0]
            print(f"  [{n:4d}] [{category:22s}] {final_url[:85]}", flush=True)

            # Checkpoint
            if n % SAVE_EVERY == 0:
                _save_raw(results)
                print(f"  ── checkpoint saved ({n} pages) ──", flush=True)

            # Enqueue new links
            for link in extract_links(html, final_url):
                if link not in visited:
                    visited.add(link)
                    await queue.put(link)

        except Exception as e:
            print(f"  [err] {url[:80]}: {e}", flush=True)
        finally:
            queue.task_done()
            await asyncio.sleep(REQUEST_DELAY)


# ── Save helpers ──────────────────────────────────────────────────────
def _save_raw(docs: list):
    with open(OUTPUT_RAW, "w", encoding="utf-8") as f:
        json.dump(docs, f, ensure_ascii=False, indent=2)


def _build_and_save_chunks(docs: list):
    all_chunks = []
    cat_counts: Counter = Counter()
    for doc in docs:
        parts = chunk_text(doc["clean_text"])
        slug = hashlib.md5(doc["url"].encode()).hexdigest()[:8]
        for idx, text_part in enumerate(parts):
            all_chunks.append({
                "chunk_id":     f"{doc['category']}__{slug}__{idx:03d}",
                "url":          doc["url"],
                "title":        doc["title"],
                "category":     doc["category"],
                "chunk_index":  idx,
                "total_chunks": len(parts),
                "text":         text_part,
            })
            cat_counts[doc["category"]] += 1

    with open(OUTPUT_CHUNKED, "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, ensure_ascii=False, indent=2)

    return all_chunks, cat_counts


# ── Main ──────────────────────────────────────────────────────────────
async def main():
    print("=" * 65, flush=True)
    print("SBU Full-Site Crawler", flush=True)
    print(f"Target: up to {MAX_TOTAL_PAGES} pages | {CONCURRENCY} workers | {REQUEST_DELAY}s delay", flush=True)
    print("=" * 65, flush=True)

    visited: set = set()
    queue: asyncio.Queue = asyncio.Queue()
    results: list = []
    counter = [0]
    stop_event = asyncio.Event()

    # Seed the queue
    for url in SEEDS:
        norm = normalize(url)
        visited.add(norm)
        await queue.put(norm)

    async with httpx.AsyncClient(headers=HEADERS, follow_redirects=True) as client:
        workers = [
            asyncio.create_task(
                worker(i, queue, visited, results, client, counter, stop_event)
            )
            for i in range(CONCURRENCY)
        ]
        await asyncio.gather(*workers, return_exceptions=True)

    print(f"\n{'='*65}", flush=True)
    print(f"Crawl complete. {len(results)} pages collected.", flush=True)

    # Save raw
    _save_raw(results)
    print(f"Saved raw  → {OUTPUT_RAW}", flush=True)

    # Chunk and save
    all_chunks, cat_counts = _build_and_save_chunks(results)
    print(f"Saved chunks → {OUTPUT_CHUNKED}", flush=True)

    print(f"\n── Summary {'─'*50}", flush=True)
    print(f"  Pages  : {len(results)}", flush=True)
    print(f"  Chunks : {len(all_chunks)}", flush=True)
    print(f"  Avg chunks/page: {len(all_chunks)/max(len(results),1):.1f}", flush=True)
    print(f"\n── Chunks per category {'─'*40}", flush=True)
    for cat, cnt in cat_counts.most_common():
        print(f"  {cat:28s}: {cnt:5d}", flush=True)
    print(f"\nNext step:", flush=True)
    print(f"  docker compose exec api python -m seed.load_real_data --reload", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
