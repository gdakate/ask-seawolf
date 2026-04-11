"""Load real SBU crawled data from documents_chunked.json into the database.

Generates embeddings using fastembed (local, no API key needed).

Usage:
    python -m seed.load_real_data           # skip if already loaded
    python -m seed.load_real_data --reload  # clear and reload fresh
"""
import asyncio
import hashlib
import json
import sys
from pathlib import Path
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session
from app.models.models import Source, Document, Chunk, SourceCategory, DocumentStatus, ContentType

DATA_FILE = Path(__file__).parent.parent / "data" / "documents_chunked.json"
BATCH_SIZE = 20  # chunks per batch (kept small to avoid Bedrock throttling)


def category_names_map() -> dict[str, str]:
    return {
        "academic_calendar":        "Academic Calendar",
        "academics":                "Academic Programs",
        "admissions":               "Admissions",
        "building_hours":           "Building Hours",
        "clubs":                    "Student Clubs & Organizations",
        "dining":                   "Dining Services",
        "faq":                      "SBU FAQ",
        "housing":                  "Campus Housing",
        "it_help":                  "IT Help & Services",
        "library":                  "University Libraries",
        "parking":                  "Parking & Transportation",
        "registrar":                "Registrar",
        "student_affairs":          "Student Affairs",
        "tuition_financial_aid":    "Tuition & Financial Aid",
        # ── Faculty ──────────────────────────────────────────────────────────
        "faculty":                  "Faculty & Staff Directory",
        "dept_applied_math_stats":  "Dept: Applied Math & Statistics",
        "dept_biochemistry":        "Dept: Biochemistry",
        "dept_biology":             "Dept: Biology",
        "dept_chemistry":           "Dept: Chemistry",
        "dept_computer_science":    "Dept: Computer Science",
        "dept_earth_space_sciences":"Dept: Earth & Space Sciences",
        "dept_economics":           "Dept: Economics",
        "dept_english":             "Dept: English",
        "dept_history":             "Dept: History",
        "dept_linguistics":         "Dept: Linguistics",
        "dept_mathematics":         "Dept: Mathematics",
        "dept_philosophy":          "Dept: Philosophy",
        "dept_physics_astronomy":   "Dept: Physics & Astronomy",
        "dept_political_science":   "Dept: Political Science",
        "dept_psychology":          "Dept: Psychology",
        "dept_sociology":           "Dept: Sociology",
        "dept_womens_gender_studies":"Dept: Women's & Gender Studies",
        "dept_africana_studies":    "Dept: Africana Studies",
        "dept_hispanic_languages":  "Dept: Hispanic Languages",
        "dept_european_languages":  "Dept: European Languages",
        "dept_comparative_literature":"Dept: Comparative Literature",
        "dept_asian_asian_american_studies":"Dept: Asian & Asian American Studies",
        "dept_biomedical_engineering":"Dept: Biomedical Engineering",
        "dept_chemical_engineering": "Dept: Chemical Engineering",
        "dept_civil_engineering":    "Dept: Civil Engineering",
        "dept_electrical_computer_engineering":"Dept: Electrical & Computer Engineering",
        "dept_mechanical_engineering":"Dept: Mechanical Engineering",
        "dept_materials_science":   "Dept: Materials Science",
        "dept_technology_society":  "Dept: Technology & Society",
        "dept_business":            "Dept: Business",
        "dept_nursing":             "Dept: Nursing",
        "dept_social_welfare":      "Dept: Social Welfare",
        "dept_public_health":       "Dept: Public Health",
        "dept_health_technology":   "Dept: Health Technology",
        "dept_marine_atmospheric_sciences":"Dept: Marine & Atmospheric Sciences",
        "dept_art":                 "Dept: Art",
        "dept_music":               "Dept: Music",
        "dept_theatre_arts":        "Dept: Theatre Arts",
        "dept_education":           "Dept: Education",
        "dept_information_systems": "Dept: Information Systems",
        "dept_iacs":                "Dept: IACS",
        "dept_ai_institute":        "Dept: AI Institute",
        "faculty_directory":        "Faculty Directory",
        # ── New categories ────────────────────────────────────────────────────
        "brightspace":              "Brightspace LMS",
        "solar":                    "SOLAR Student Portal",
        "undergraduate_admissions": "Undergraduate Admissions",
        "graduate_admissions":      "Graduate Admissions",
        "health_wellness":          "Health & Wellness",
        "career_center":            "Career Center",
        "international_students":   "International Student Services",
        "disability_support":       "Disability Support Services",
        "academic_support":         "Academic Support",
        "campus_life":              "Campus Life",
        "athletics_recreation":     "Athletics & Recreation",
        "campus_map_transit":       "Campus Map & Transit",
        "safety_emergency":         "Safety & Emergency",
        "research":                 "Research",
        "graduation":               "Graduation & Commencement",
        "sbu_general":              "About Stony Brook University",
    }


MAX_EMBED_CHARS = 30000  # Titan v2 limit ~8192 tokens ≈ 30k chars


async def embed_batch(texts: list[str]) -> list[list[float]]:
    from app.services.ai_providers import get_embedding_provider
    provider = get_embedding_provider()
    # Truncate oversized chunks so Titan doesn't reject them
    safe_texts = [t[:MAX_EMBED_CHARS] for t in texts]
    return await provider.embed(safe_texts)


def safe_category(cat: str) -> SourceCategory:
    try:
        return SourceCategory(cat)
    except ValueError:
        return SourceCategory.GENERAL


async def load(db: AsyncSession, reload: bool = False):
    print(f"Loading data from {DATA_FILE}...")
    with open(DATA_FILE, encoding="utf-8") as f:
        chunks_data = json.load(f)

    print(f"  {len(chunks_data)} chunks across dataset")

    # Check if already loaded
    result = await db.execute(
        select(Source).where(Source.name == "Academic Calendar")
    )
    existing = result.scalar_one_or_none()

    if existing and not reload:
        print("Real data already loaded. Skipping. (use --reload to force reload)")
        return

    if reload:
        print("Reload requested — truncating all data...")
        from sqlalchemy import text
        await db.execute(text("TRUNCATE TABLE chunks, documents, sources RESTART IDENTITY CASCADE"))
        await db.flush()
        print("  Cleared all sources/documents/chunks.")

    from app.core.config import get_settings
    print(f"  Using AI provider: {get_settings().ai_provider}")

    # Create one Source per category
    cat_map = category_names_map()
    sources: dict[str, Source] = {}
    documents: dict[str, Document] = {}

    for cat, display_name in cat_map.items():
        # Use a unique placeholder URL that won't clash with seed data
        placeholder_url = f"https://www.stonybrook.edu/_crawled/{cat}/"
        # Check if a source with this name already exists (e.g. from a partial run)
        existing_src = (await db.execute(
            select(Source).where(Source.name == display_name)
        )).scalar_one_or_none()
        if existing_src:
            sources[cat] = existing_src
        else:
            src = Source(
                name=display_name,
                url=placeholder_url,
                category=safe_category(cat),
                office=cat,
                authority_score=1.0,
                is_active=True,
            )
            db.add(src)
            sources[cat] = src

    await db.flush()
    print(f"  Created/reused {len(sources)} sources")

    # Create Documents (one per unique URL)
    for item in chunks_data:
        url = item["url"]
        if url in documents:
            continue
        cat = item["category"]
        # Fall back to faq source if category isn't in our map
        src = sources.get(cat) or sources.get("faq") or list(sources.values())[0]
        content_hash = hashlib.sha256(url.encode()).hexdigest()
        doc = Document(
            source_id=src.id,
            title=item["title"],
            source_url=url,
            content_type=ContentType.HTML,
            status=DocumentStatus.INDEXED,
            content_hash=content_hash,
            last_seen_at=datetime.now(timezone.utc),
        )
        db.add(doc)
        documents[url] = doc

    await db.flush()
    print(f"  Created {len(documents)} documents")

    # Create Chunks with embeddings in batches
    total = len(chunks_data)
    created = 0

    for batch_start in range(0, total, BATCH_SIZE):
        batch = chunks_data[batch_start: batch_start + BATCH_SIZE]
        texts = [item["text"] for item in batch]
        embeddings = await embed_batch(texts)

        for item, embedding in zip(batch, embeddings):
            doc = documents[item["url"]]
            chunk = Chunk(
                document_id=doc.id,
                chunk_index=item["chunk_index"],
                content=item["text"],
                heading=item.get("title", ""),
                token_count=len(item["text"].split()),
                embedding=embedding,
            )
            db.add(chunk)
            created += 1

        await db.flush()
        pct = min(100, int((batch_start + BATCH_SIZE) / total * 100))
        print(f"  Embedded {min(batch_start + BATCH_SIZE, total)}/{total} chunks ({pct}%)...")

    await db.commit()
    print(f"\nDone! Loaded {created} chunks from real SBU data.")


async def main():
    reload = "--reload" in sys.argv
    async with async_session() as db:
        await load(db, reload=reload)


if __name__ == "__main__":
    asyncio.run(main())
