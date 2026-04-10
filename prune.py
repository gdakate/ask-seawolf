"""
CampusIQ - Pruner
Reads documents_v5.json, applies per-category pruning rules,
outputs documents_v5_pruned.json.
"""

import json
import re
import sys
from collections import Counter

# ── academic_calendar: URL segments that indicate non-calendar pages ──────────
ACADEMIC_PRUNE_URL = [
    "/transcripts/", "ordertranscript",
    "/forms/",
    "/graduation/", "diploma",
    "/rematric", "timeoff", "taking_time_off",
    "majorminor", "major_minor",
    "preferredname", "preferred_name",
    "/ferpa",
    "/records/",
    "change-of-address", "degree-verification", "enrollment-verification",
    "professional-licensing", "student-id",
    "cross-registration",
]

# academic_calendar: title phrases that indicate non-calendar pages
ACADEMIC_PRUNE_TITLE = [
    "Graduation Application",
    "Diploma Information",
    "Taking Time Off",
    "Preferred Name",
    "FERPA",
    "Major Minor",
    "Professional Licensing",
    "Student ID",
    "Enrollment Verification",
    "Degree Verification",
    "Change of Address",
    "Cross Registration",
]

# ── library: keep only student-facing service pages ───────────────────────────
# Remove if URL contains any of these
LIBRARY_PRUNE_URL = [
    "strategic-plan", "strategic_plan",
    "endowment", "giving", "gift",
    "leadership", "faculty-staff-directory",
    "memberships", "partnerships",
    "/news/", "/events/", "/exhibits/",
    "commons.library",          # internal commons subdomain
    "search.library",           # dynamic discovery search
]

# Remove if clean_text contains these phrases (low-value / empty FAQ pages)
LIBRARY_PRUNE_TEXT = [
    "0 Answers",
    "No FAQs were found",
    "No results were found",
    "Loading...",
]

# ── Breadcrumb / trailing boilerplate fixes per category ──────────────────────
def fix_academic_calendar_text(text: str) -> str:
    # Remove leading "Home Calendars ..." breadcrumb
    text = re.sub(
        r'^Home Calendars\b.{0,300}?(?=[A-Z][a-z]{2,} [A-Z]|[A-Z][a-z]{2,}:)',
        '', text, flags=re.DOTALL
    ).strip()
    # Remove trailing "print Office of the Registrar" footer fragments
    text = re.sub(
        r'print Office of the Registrar.*$', '', text, flags=re.DOTALL | re.IGNORECASE
    ).strip()
    return re.sub(r'\s+', ' ', text).strip()


def should_prune(doc: dict) -> tuple[bool, str]:
    """Returns (should_prune, reason)."""
    url      = doc.get("url", "").lower()
    title    = doc.get("title", "")
    category = doc.get("category", "")
    text     = doc.get("clean_text", "")

    # ── departments: exclude entirely from this release ──────────────────────
    if category == "departments":
        return True, "departments excluded (MVP)"

    # ── academic_calendar ────────────────────────────────────────────────────
    if category == "academic_calendar":
        for pat in ACADEMIC_PRUNE_URL:
            if pat in url:
                return True, f"academic URL prune: {pat}"
        for phrase in ACADEMIC_PRUNE_TITLE:
            if phrase.lower() in title.lower():
                return True, f"academic title prune: {phrase}"

    # ── library ──────────────────────────────────────────────────────────────
    if category == "library":
        for pat in LIBRARY_PRUNE_URL:
            if pat in url:
                return True, f"library URL prune: {pat}"
        for phrase in LIBRARY_PRUNE_TEXT:
            if phrase in text:
                return True, f"library text prune: {phrase}"
        # Remove very short pages (listing-only, nearly empty)
        if len(text) < 200:
            return True, "library too short"

    return False, ""


def prune(input_path: str, output_path: str):
    with open(input_path, encoding="utf-8") as f:
        data = json.load(f)

    kept = []
    prune_log = Counter()

    for doc in data:
        pruned, reason = should_prune(doc)
        if pruned:
            prune_log[reason.split(":")[0].strip()] += 1
            continue

        # Post-process text for specific categories
        if doc["category"] == "academic_calendar":
            doc["clean_text"] = fix_academic_calendar_text(doc["clean_text"])
            if len(doc["clean_text"]) < 100:
                prune_log["academic too short after fix"] += 1
                continue

        kept.append(doc)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(kept, f, ensure_ascii=False, indent=2)

    counts = Counter(d["category"] for d in kept)
    print(f"✅ Pruned → {output_path}")
    print(f"   input : {len(data)}")
    print(f"   kept  : {len(kept)}")
    print(f"   pruned: {len(data) - len(kept)}")
    print()
    print("── Category counts ──")
    for cat, cnt in counts.most_common():
        print(f"  {cat:25s}: {cnt:4d}")
    print()
    print("── Prune reasons ──")
    for reason, cnt in prune_log.most_common():
        print(f"  {cnt:4d}  {reason}")


if __name__ == "__main__":
    input_file  = sys.argv[1] if len(sys.argv) > 1 else "documents_v5.json"
    output_file = sys.argv[2] if len(sys.argv) > 2 else "documents_v5_pruned.json"
    prune(input_file, output_file)
