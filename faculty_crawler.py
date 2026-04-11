"""
SBU Faculty Crawler
Crawls faculty/people pages across all Stony Brook University departments.
Output: faculty_raw.json

Run:
    python3 faculty_crawler.py

Then merge into the main dataset:
    python3 merge_faculty.py
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

# ── All SBU department faculty/people seed URLs ───────────────────────────────
FACULTY_SEEDS = {
    # ── Arts & Sciences ───────────────────────────────────────────────────────
    "dept_applied_math_stats": [
        "https://www.stonybrook.edu/commcms/ams/people/faculty/",
        "https://www.stonybrook.edu/commcms/ams/people/",
    ],
    "dept_biochemistry": [
        "https://www.stonybrook.edu/commcms/biochem/people/",
        "https://www.stonybrook.edu/commcms/biochem/people/faculty/",
    ],
    "dept_biology": [
        "https://www.stonybrook.edu/commcms/biology/people/faculty/",
        "https://www.stonybrook.edu/commcms/biology/people/",
    ],
    "dept_chemistry": [
        "https://chemistry.stonybrook.edu/people/faculty/",
        "https://chemistry.stonybrook.edu/people/",
    ],
    "dept_computer_science": [
        "https://www.cs.stonybrook.edu/people/faculty",
        "https://www.cs.stonybrook.edu/people",
        "https://www.cs.stonybrook.edu/people/research-faculty",
        "https://www.cs.stonybrook.edu/people/emeritus-faculty",
        "https://www.cs.stonybrook.edu/people/adjunct-faculty",
    ],
    "dept_earth_space_sciences": [
        "https://www.stonybrook.edu/commcms/ess/people/faculty/",
        "https://www.stonybrook.edu/commcms/ess/people/",
    ],
    "dept_economics": [
        "https://www.stonybrook.edu/commcms/economics/people/faculty/",
        "https://www.stonybrook.edu/commcms/economics/people/",
    ],
    "dept_english": [
        "https://www.stonybrook.edu/commcms/english/people/faculty/",
        "https://www.stonybrook.edu/commcms/english/people/",
    ],
    "dept_history": [
        "https://www.stonybrook.edu/commcms/history/people/faculty/",
        "https://www.stonybrook.edu/commcms/history/people/",
    ],
    "dept_linguistics": [
        "https://www.stonybrook.edu/commcms/linguistics/people/faculty/",
        "https://www.stonybrook.edu/commcms/linguistics/people/",
    ],
    "dept_mathematics": [
        "https://www.math.stonybrook.edu/people",
        "https://www.math.stonybrook.edu/faculty",
    ],
    "dept_philosophy": [
        "https://www.stonybrook.edu/commcms/philosophy/people/faculty/",
        "https://www.stonybrook.edu/commcms/philosophy/people/",
    ],
    "dept_physics_astronomy": [
        "https://www.physics.stonybrook.edu/people/faculty/",
        "https://www.physics.stonybrook.edu/people/",
    ],
    "dept_political_science": [
        "https://www.stonybrook.edu/commcms/polsci/people/faculty/",
        "https://www.stonybrook.edu/commcms/polsci/people/",
    ],
    "dept_psychology": [
        "https://www.stonybrook.edu/commcms/psychology/people/faculty/",
        "https://www.stonybrook.edu/commcms/psychology/people/",
    ],
    "dept_sociology": [
        "https://www.stonybrook.edu/commcms/sociology/people/faculty/",
        "https://www.stonybrook.edu/commcms/sociology/people/",
    ],
    "dept_womens_gender_studies": [
        "https://www.stonybrook.edu/commcms/wgss/people/faculty/",
        "https://www.stonybrook.edu/commcms/wgss/people/",
    ],
    "dept_africana_studies": [
        "https://www.stonybrook.edu/commcms/africana/people/faculty/",
        "https://www.stonybrook.edu/commcms/africana/people/",
    ],
    "dept_hispanic_languages": [
        "https://www.stonybrook.edu/commcms/hispanic/people/faculty/",
        "https://www.stonybrook.edu/commcms/hispanic/people/",
    ],
    "dept_european_languages": [
        "https://www.stonybrook.edu/commcms/esl/people/faculty/",
        "https://www.stonybrook.edu/commcms/esl/people/",
    ],
    "dept_comparative_literature": [
        "https://www.stonybrook.edu/commcms/complit/people/faculty/",
        "https://www.stonybrook.edu/commcms/complit/people/",
    ],
    "dept_asian_asian_american_studies": [
        "https://www.stonybrook.edu/commcms/asian/people/faculty/",
        "https://www.stonybrook.edu/commcms/asian/people/",
    ],

    # ── College of Engineering & Applied Sciences ─────────────────────────────
    "dept_biomedical_engineering": [
        "https://www.stonybrook.edu/commcms/bme/people/faculty/",
        "https://www.stonybrook.edu/commcms/bme/people/",
    ],
    "dept_chemical_engineering": [
        "https://www.stonybrook.edu/commcms/cme/people/faculty/",
        "https://www.stonybrook.edu/commcms/cme/people/",
        "https://www.stonybrook.edu/commcms/che/people/faculty/",
        "https://www.stonybrook.edu/commcms/che/people/",
    ],
    "dept_civil_engineering": [
        "https://www.stonybrook.edu/commcms/cee/people/faculty/",
        "https://www.stonybrook.edu/commcms/cee/people/",
    ],
    "dept_electrical_computer_engineering": [
        "https://www.stonybrook.edu/commcms/ece/people/faculty/",
        "https://www.stonybrook.edu/commcms/ece/people/",
    ],
    "dept_mechanical_engineering": [
        "https://www.stonybrook.edu/commcms/me/people/faculty/",
        "https://www.stonybrook.edu/commcms/me/people/",
    ],
    "dept_materials_science": [
        "https://www.stonybrook.edu/commcms/mse/people/faculty/",
        "https://www.stonybrook.edu/commcms/mse/people/",
    ],
    "dept_technology_society": [
        "https://www.stonybrook.edu/commcms/est/people/faculty/",
        "https://www.stonybrook.edu/commcms/est/people/",
    ],

    # ── College of Business ───────────────────────────────────────────────────
    "dept_business": [
        "https://www.stonybrook.edu/commcms/business/people/faculty/",
        "https://www.stonybrook.edu/commcms/business/people/",
        "https://www.stonybrook.edu/commcms/business/faculty/",
    ],

    # ── Health Sciences ───────────────────────────────────────────────────────
    "dept_nursing": [
        "https://www.stonybrook.edu/commcms/nursing/people/faculty/",
        "https://www.stonybrook.edu/commcms/nursing/people/",
    ],
    "dept_social_welfare": [
        "https://www.stonybrook.edu/commcms/socialwelfare/people/faculty/",
        "https://www.stonybrook.edu/commcms/socialwelfare/people/",
    ],
    "dept_public_health": [
        "https://www.stonybrook.edu/commcms/publichealth/people/faculty/",
        "https://www.stonybrook.edu/commcms/publichealth/people/",
        "https://publichealth.stonybrook.edu/people/faculty/",
    ],
    "dept_health_technology": [
        "https://www.stonybrook.edu/commcms/htech/people/faculty/",
        "https://www.stonybrook.edu/commcms/htech/people/",
    ],

    # ── Marine & Atmospheric Sciences ────────────────────────────────────────
    "dept_marine_atmospheric_sciences": [
        "https://www.stonybrook.edu/commcms/msb/people/faculty/",
        "https://www.stonybrook.edu/commcms/msb/people/",
        "https://marine.stonybrook.edu/people/faculty/",
    ],

    # ── Arts ─────────────────────────────────────────────────────────────────
    "dept_art": [
        "https://www.stonybrook.edu/commcms/art/people/faculty/",
        "https://www.stonybrook.edu/commcms/art/people/",
    ],
    "dept_music": [
        "https://www.stonybrook.edu/commcms/music/people/faculty/",
        "https://www.stonybrook.edu/commcms/music/people/",
    ],
    "dept_theatre_arts": [
        "https://www.stonybrook.edu/commcms/theatrearts/people/faculty/",
        "https://www.stonybrook.edu/commcms/theatrearts/people/",
    ],

    # ── Education & Professional Studies ─────────────────────────────────────
    "dept_education": [
        "https://www.stonybrook.edu/commcms/education/people/faculty/",
        "https://www.stonybrook.edu/commcms/education/people/",
    ],
    "dept_information_systems": [
        "https://www.stonybrook.edu/commcms/informationsystems/people/faculty/",
    ],

    # ── Interdisciplinary / Research Centers ──────────────────────────────────
    "dept_iacs": [
        "https://www.stonybrook.edu/iacs/people/",
        "https://www.stonybrook.edu/iacs/faculty/",
    ],
    "dept_ai_institute": [
        "https://www.stonybrook.edu/commcms/ai/people/",
        "https://www.stonybrook.edu/commcms/ai/faculty/",
    ],

    # ── General faculty directory ─────────────────────────────────────────────
    "faculty_directory": [
        "https://www.stonybrook.edu/experts/",
        "https://www.stonybrook.edu/experts/departments/",
    ],
}

# ── Config ────────────────────────────────────────────────────────────────────
ALLOWED_DOMAINS = {
    "stonybrook.edu",
    "cs.stonybrook.edu",
    "chemistry.stonybrook.edu",
    "math.stonybrook.edu",
    "physics.stonybrook.edu",
    "medicine.stonybrook.edu",
    "marine.stonybrook.edu",
    "publichealth.stonybrook.edu",
}
MAX_DEPTH       = 2       # seed → list page → individual profile
DELAY_SECONDS   = 0.4
OUTPUT_FILE     = "faculty_raw.json"
TIMEOUT         = 12

SKIP_EXTENSIONS = {
    ".pdf", ".doc", ".docx", ".ppt", ".pptx",
    ".jpg", ".jpeg", ".png", ".gif", ".svg",
    ".zip", ".tar", ".gz", ".mp4", ".mp3",
    ".css", ".js", ".ico",
}
SKIP_PATTERNS = ["mailto:", "tel:", "javascript:", "#"]

# URL fragments that indicate non-faculty pages — skip at depth > 0
SKIP_URL_FRAGMENTS = [
    "/news/", "/events/", "/research/", "/courses/",
    "/about/", "/contact/", "/calendar/", "/admissions/",
    "/graduate/", "/undergraduate/", "/giving/", "/alumni/",
    "login", "search", "sitemap",
]
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


def is_likely_faculty_url(url: str, depth: int) -> bool:
    """At depth > 0, only follow URLs that look like faculty/people pages."""
    if depth == 0:
        return True
    lower = url.lower()
    # Allow people/faculty/profile/staff pages
    if any(kw in lower for kw in ["/people/", "/faculty/", "/profile/", "/staff/", "/directory/", "/person/"]):
        return True
    # Skip obviously irrelevant sections when following links
    if any(kw in lower for kw in SKIP_URL_FRAGMENTS):
        return False
    return True


def normalize_url(url: str) -> str:
    return urlparse(url)._replace(fragment="").geturl()


def clean_text(soup: BeautifulSoup) -> str:
    for tag in soup(["script", "style", "nav", "footer", "header", "noscript"]):
        tag.decompose()
    for tag in soup.find_all(class_=[
        "navWrap", "sitenav", "sidebar", "side-nav",
        "breadcrumb", "breadcrumbs", "menu", "navigation",
    ]):
        tag.decompose()
    return " ".join(soup.get_text(separator=" ").split())


def fetch_page(url: str, session: requests.Session) -> Optional[dict]:
    try:
        resp = session.get(url, timeout=TIMEOUT)
        if resp.status_code != 200:
            return None
        if "text/html" not in resp.headers.get("Content-Type", ""):
            return None

        soup = BeautifulSoup(resp.text, "html.parser")
        title = soup.title.string.strip() if soup.title and soup.title.string else ""
        text = clean_text(soup)

        links = []
        for a in soup.find_all("a", href=True):
            href = normalize_url(urljoin(url, a["href"]))
            if is_valid_url(href):
                links.append(href)

        return {"title": title, "text": text, "links": links}

    except Exception as e:
        logger.warning(f"Failed: {url} — {e}")
        return None


def crawl_department(dept: str, seeds: list, session: requests.Session, visited: set) -> list:
    results = []
    queue = [(url, 0) for url in seeds]

    while queue:
        url, depth = queue.pop(0)
        url = normalize_url(url)

        if url in visited or depth > MAX_DEPTH:
            continue
        visited.add(url)

        if not is_likely_faculty_url(url, depth):
            logger.debug(f"[{dept}] skipping non-faculty URL at depth {depth}: {url}")
            continue

        logger.info(f"[{dept}] depth={depth} {url}")
        page = fetch_page(url, session)
        if not page:
            continue

        # Only save pages that likely have faculty content
        text_lower = page["text"].lower()
        has_faculty_content = any(kw in text_lower for kw in [
            "professor", "faculty", "ph.d", "phd", "research", "associate",
            "assistant professor", "lecturer", "instructor", "emeritus",
            "office:", "email:", "phone:", "lab:", "office hours",
        ])

        if has_faculty_content or depth == 0:
            results.append({
                "url"      : url,
                "category" : "faculty",
                "department": dept,
                "title"    : page["title"],
                "clean_text": page["text"],
            })

        if depth < MAX_DEPTH:
            for link in page["links"]:
                if link not in visited:
                    queue.append((link, depth + 1))

        time.sleep(DELAY_SECONDS)

    return results


def main():
    session = requests.Session()
    session.headers.update({
        "User-Agent": "SBU-AskSeawolves-Crawler/1.0 (student research project; contact: sbu-assistant)",
    })

    visited: set = set()
    all_results: list = []

    for dept, seeds in FACULTY_SEEDS.items():
        logger.info(f"\n{'='*55}\nCrawling: {dept}\n{'='*55}")
        results = crawl_department(dept, seeds, session, visited)
        all_results.extend(results)
        logger.info(f"  → {len(results)} pages collected for [{dept}]")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)

    logger.info(f"\nDone! {len(all_results)} total faculty pages saved to {OUTPUT_FILE}")

    counts = Counter(r["department"] for r in all_results)
    print("\n── Department Summary ──")
    for dept, count in counts.most_common():
        print(f"  {dept:45s}: {count} pages")


if __name__ == "__main__":
    main()
