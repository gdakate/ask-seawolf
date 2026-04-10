"""
CampusIQ - SBU Targeted Crawler
Crawls specific seed URLs and their direct subpages only.
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import json
import time
import logging
from typing import Optional
from collections import Counter

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# ── Seed URLs by category ─────────────────────────────────────────────────────
SEED_URLS = {
    "academic_calendar": [
        "https://www.stonybrook.edu/commcms/registrar/calendars/academic_calendars",
    ],
    "registrar": [
        "https://www.stonybrook.edu/commcms/registrar/",
        "https://www.stonybrook.edu/commcms/registrar/registration/schedules.php",
        "https://www.stonybrook.edu/commcms/registrar/registration/exams.php",
    ],
    "tuition_financial_aid": [
        "https://www.stonybrook.edu/bursar/tuition/",
        "https://www.stonybrook.edu/sfs/",
    ],
    "library": [
        "https://library.stonybrook.edu/",
    ],
    "housing": [
        "https://www.stonybrook.edu/commcms/studentaffairs/res/housing/",
    ],
    "dining": [
        "https://www.stonybrook.edu/commcms/dining/",
        "https://www.stonybrook.edu/commcms/mealplan/plans.php",
    ],
    "it_help": [
        "https://it.stonybrook.edu/",
    ],
    "faq": [
        "https://www.stonybrook.edu/commcms/studentaffairs/studentsupport/faq.php",
    ],
    "building_hours": [
        "https://www.stonybrook.edu/commcms/studentaffairs/for/about/hours.php",
    ],
    "parking": [
        "https://www.stonybrook.edu/mobility-and-parking/transportation/",
    ],
    "clubs": [
        "https://www.stonybrook.edu/commcms/studentaffairs/sac/club_and_orgs/",
    ],
    "departments": [
        "https://www.stonybrook.edu/experts/departments/",
    ],
}

# ── Config ────────────────────────────────────────────────────────────────────
ALLOWED_DOMAINS = {"stonybrook.edu", "library.stonybrook.edu", "it.stonybrook.edu"}
MAX_DEPTH       = 2        # seed(0) → children(1) → grandchildren(2)
DELAY_SECONDS   = 0.3
OUTPUT_FILE     = "sbu_crawl.json"
TIMEOUT         = 10

SKIP_EXTENSIONS = {
    ".pdf", ".doc", ".docx", ".ppt", ".pptx",
    ".jpg", ".jpeg", ".png", ".gif", ".svg",
    ".zip", ".tar", ".gz", ".mp4", ".mp3",
    ".css", ".js", ".ico",
}
SKIP_PATTERNS = ["mailto:", "tel:", "javascript:", "#"]
# ─────────────────────────────────────────────────────────────────────────────


def is_valid_url(url: str) -> bool:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return False
    if not any(d in parsed.netloc for d in ALLOWED_DOMAINS):
        return False
    path = parsed.path.lower()
    if any(path.endswith(ext) for ext in SKIP_EXTENSIONS):
        return False
    if any(pat in url.lower() for pat in SKIP_PATTERNS):
        return False
    return True


def normalize_url(url: str) -> str:
    return urlparse(url)._replace(fragment="").geturl()


def fetch_page(url: str, session: requests.Session) -> Optional[dict]:
    try:
        resp = session.get(url, timeout=TIMEOUT)
        if resp.status_code != 200:
            return None
        if "text/html" not in resp.headers.get("Content-Type", ""):
            return None

        soup = BeautifulSoup(resp.text, "html.parser")
        title = soup.title.string.strip() if soup.title and soup.title.string else ""

        for tag in soup(["script", "style", "nav", "footer", "header", "noscript"]):
            tag.decompose()
        for tag in soup.find_all(class_=["navWrap", "sitenav", "sidebar", "side-nav", "breadcrumb", "breadcrumbs"]):
            tag.decompose()

        text = " ".join(soup.get_text(separator=" ").split())

        links = []
        for a in soup.find_all("a", href=True):
            href = normalize_url(urljoin(url, a["href"]))
            if is_valid_url(href):
                links.append(href)

        return {"title": title, "text": text, "links": links}

    except Exception as e:
        logger.warning(f"Failed: {url} — {e}")
        return None


def crawl_category(category: str, seeds: list, session: requests.Session, visited: set) -> list:
    results = []
    queue = [(url, 0) for url in seeds]

    while queue:
        url, depth = queue.pop(0)
        url = normalize_url(url)

        if url in visited or depth > MAX_DEPTH:
            continue
        visited.add(url)

        logger.info(f"[{category}] depth={depth} {url}")
        page = fetch_page(url, session)
        if not page:
            continue

        results.append({
            "url": url,
            "category": category,
            "title": page["title"],
            "text": page["text"],
        })

        if depth < MAX_DEPTH:
            for link in page["links"]:
                if link not in visited:
                    queue.append((link, depth + 1))

        time.sleep(DELAY_SECONDS)

    return results


def main():
    session = requests.Session()
    session.headers.update({"User-Agent": "CampusIQ-Crawler/1.0 (student research project)"})

    visited = set()
    all_results = []

    for category, seeds in SEED_URLS.items():
        logger.info(f"\n{'='*50}\nCrawling category: {category}\n{'='*50}")
        results = crawl_category(category, seeds, session, visited)
        all_results.extend(results)
        logger.info(f"  → {len(results)} pages collected for [{category}]")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)

    logger.info(f"\nDone! {len(all_results)} total pages saved to {OUTPUT_FILE}")

    counts = Counter(r["category"] for r in all_results)
    print("\n── Category Summary ──")
    for cat, count in counts.most_common():
        print(f"  {cat}: {count} pages")


if __name__ == "__main__":
    main()
