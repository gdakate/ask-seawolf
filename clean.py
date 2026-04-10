"""
CampusIQ - Data Cleaner
Strategy:
  1. Trim nav prefix: cut everything up to (and including) the nav-end anchor
  2. Remove footer boilerplate via phrases and regex
"""

import json
import re
import sys

# ── URL-based category remap (applied before whitelist check) ─────────────────
# Fixes misclassification when pages are discovered from a different seed category.
URL_CATEGORY_REMAP = [
    ("/commcms/mealplan/",       "dining"),
    ("/commcms/dining/",         "dining"),
    ("/mobility-and-parking/",   "parking"),
    ("/transportation/",         "parking"),
]

# ── Per-category nav-end anchors ──────────────────────────────────────────────
# Everything up to and including the anchor is removed as nav prefix.
# Anchors are tried in order; first match wins.
PREFIX_CUT_ANCHORS = {
    "academic_calendar": [
        "SBU Student ID Help Systems Access Contact",
        "Professional Licensing SBU Student ID Help Systems",
    ],
    "registrar": [
        "SBU Student ID Help Systems Access Contact",
    ],
    "tuition_financial_aid": [
        "Tuition Liability Appeal Form",                    # bursar nav end
        "Contact Us FAQ",                                   # sfs nav end
        "Withdrawals Eligibility Maintain Eligibility",     # finaid nav end
        "Preparatory Course Work Re-Evaluation Withdrawals Eligibility",
    ],
    "library": [
        # library.stonybrook.edu — secondary nav ends before page content
        "Health Sciences Library and Resource Center",
        "Branch Library Websites Health Sciences",
        "View All Libraries & Hours Branch Library",
        # guides.library subdomain
        "Stony Brook University Libraries Research & Subject Guides",
        # answers.library subdomain — FAQ knowledge base
        "Toggle menu visibility",
        # commons / exhibits subdomains
        "Stony Brook University Libraries",
    ],
    "housing": [
        # nav ends with "...Student Opportunities Contact Us Residential Community Contact"
        "Student Opportunities Contact Us Residential Community Contact",
        "Professional Opportunities Student Opportunities Contact Us",
    ],
    "faq": [
        "Contact Us Concern for a Student",
    ],
    "building_hours": [
        "Cancellation, Billing, & Fees Contact Us",
    ],
    "clubs": [
        "Club & Org Reporting Contact Us Campus Connect",
        "OEA Report Form Club & Org Reporting Contact Us",
    ],
    "departments": [
        "Close Departments",
        "Close Topics",
        "View all experts Featured Experts",
        "View all experts Close",
    ],
    "dining": [
        # mealplan pages nav end
        "Report Lost/Stolen Nutrislice Dining →",
        "Nutrislice Dining →",
        # dining pages nav end
        "Feedback Dining Guide",
        "Catering Feedback Dining Guide",
    ],
    "it_help": [
        # it.stonybrook.edu nav end (note: "TIcket" typo is in the actual page)
        "Submit a TIcket System Status Close",
        "Submit a Ticket System Status Close",
    ],
    "parking": [
        # parking nav repeats twice; second block ends with this
        "Citations FAQs East Campus Contact",
        "Parking Map Citations FAQs",
    ],
}

# ── Footer boilerplate phrases ────────────────────────────────────────────────
FOOTER_PHRASES = [
    "Skip Navigation",
    "Search Text",
    "Select Search Scope",
    "Search This Site",
    "Just This Site",
    "SBU Website",
    "Search Home",
    "Search Search",
    "Discrimination Sexual Misconduct Accessibility Barrier",
    "Admin Login",
    "Title IX Accessibility Privacy Policy Sustainability Diversity",
    "Stony Brook Union, Suite 206",
    "Stony Brook Union",
    "Stony Brook, NY 11794",
    "Phone: (631)",
    "Fax: (631)",
    # Library subdomain nav bar remnants
    "↓ Skip to Main Content SBU Home My Library Account Course Reserves Suggestion Box",
    "Skip to Main Content SBU Home My Library Account",
    # Housing nav remnant (for anchor-miss pages)
    "Why Live With Us Senior Leadership Housing Apply to Housing",
]

# ── URL-based skip filter ─────────────────────────────────────────────────────
SKIP_URL_PATTERNS = [
    "student-admission", "student-profile", "undergraduate-admissions",
    "login", "logout", "admin",
]

# ── Category URL whitelist ────────────────────────────────────────────────────
CATEGORY_URL_WHITELIST = {
    "academic_calendar":   ["registrar", "calendar", "academic", "exam", "session", "schedule"],
    "registrar":           ["registrar", "enrollment", "transcript", "diploma", "ferpa"],
    "tuition_financial_aid": ["bursar", "tuition", "sfs", "financial", "aid"],
    "library":             ["library"],
    "housing":             ["housing", "res/", "residential"],
    "dining":              ["dining", "mealplan"],
    "it_help":             ["it.stonybrook", "ithelp", "service-desk"],
    "faq":                 ["faq", "studentsupport"],
    "building_hours":      ["hours", "building"],
    "parking":             ["parking", "mobility", "transportation"],
    "clubs":               ["club", "org", "sac"],
    "departments":         ["department", "experts"],
}


def trim_prefix(text: str, category: str) -> str:
    """Remove nav prefix by cutting up to and including the nav-end anchor."""
    # Normalize non-breaking spaces before anchor matching
    text = text.replace('\xa0', ' ')
    for anchor in PREFIX_CUT_ANCHORS.get(category, []):
        idx = text.find(anchor)
        if idx != -1:
            return text[idx + len(anchor):].strip()
    return text


def remove_footer(text: str) -> str:
    """Remove footer boilerplate, phone numbers, emails, copyright lines."""
    text = text.replace('\xa0', ' ')

    # Copyright lines (encoding-independent)
    text = re.sub(r'[©\xa9]\s*\d{4}[^\n]*', '', text)
    # Email addresses
    text = re.sub(r'\S+@\S+\.\S+', '', text)
    # Phone numbers (full and fragments like -3221, 632-6175)
    text = re.sub(r'\(?\d{3}\)?[\s.\-]?\d{3}[\s.\-]?\d{4}', '', text)
    text = re.sub(r'\b\d{3}-\d{4}\b', '', text)
    text = re.sub(r'-\d{4}\b', '', text)
    # Address fragments
    text = re.sub(r'Stony Brook,?\s*NY\s*\d*', '', text)
    text = re.sub(r'Suite\s*\d+', '', text)
    text = re.sub(r'\bNY\s+\d{5}', '', text)
    # Library/springshare widget remnants
    text = re.sub(r'(?:Search )?Powered by Springshare[^\n]*', '', text)
    text = re.sub(r'Search Terms\s+Search\s+Loading', '', text)
    # Phrase removal
    for phrase in FOOTER_PHRASES:
        text = text.replace(phrase, "")
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def is_relevant_url(url: str, category: str) -> bool:
    url_lower = url.lower()
    if any(pat in url_lower for pat in SKIP_URL_PATTERNS):
        return False
    allowed = CATEGORY_URL_WHITELIST.get(category, [])
    if allowed and not any(pat in url_lower for pat in allowed):
        return False
    return True


def is_meaningful(text: str, min_length: int = 100) -> bool:
    return len(text.strip()) >= min_length


def clean_file(input_path: str, output_path: str):
    with open(input_path, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    documents = []
    skipped = 0
    anchor_misses = {}  # track categories where anchor wasn't found

    for item in raw_data:
        url      = item.get("url", "")
        category = item.get("category", "")
        title    = item.get("title", "")
        text     = item.get("text", "")

        # URL-based category remap (fix misclassification from seed crawl)
        for pattern, new_cat in URL_CATEGORY_REMAP:
            if pattern in url:
                category = new_cat
                break

        if not is_relevant_url(url, category):
            skipped += 1
            continue

        # Step 1: trim nav prefix
        trimmed = trim_prefix(text, category)
        if trimmed == text and category in PREFIX_CUT_ANCHORS:
            anchor_misses[category] = anchor_misses.get(category, 0) + 1

        # Step 2: remove footer boilerplate
        clean_text = remove_footer(trimmed)

        if not is_meaningful(clean_text):
            skipped += 1
            continue

        documents.append({
            "url": url,
            "title": title,
            "category": category,
            "clean_text": clean_text,
        })

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(documents, f, ensure_ascii=False, indent=2)

    print(f"✅ Done!")
    print(f"   kept   : {len(documents)}")
    print(f"   skipped: {skipped}")
    print(f"   saved  : {output_path}")
    if anchor_misses:
        print(f"\n⚠️  Anchor miss counts (prefix NOT trimmed):")
        for cat, count in sorted(anchor_misses.items()):
            print(f"   {cat}: {count} pages")


if __name__ == "__main__":
    input_file  = sys.argv[1] if len(sys.argv) > 1 else "sbu_crawl.json"
    output_file = sys.argv[2] if len(sys.argv) > 2 else "documents.json"
    clean_file(input_file, output_file)
