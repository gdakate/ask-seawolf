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
BATCH_SIZE = 64  # chunks to embed at once


def category_names_map() -> dict[str, str]:
    return {
        "academic_calendar":  "Academic Calendar",
        "academics":          "Academic Programs",
        "admissions":         "Admissions",
        "building_hours":     "Building Hours",
        "clubs":              "Student Clubs & Organizations",
        "dining":             "Dining Services",
        "faq":                "SBU FAQ",
        "housing":            "Campus Housing",
        "it_help":            "IT Help & Services",
        "library":            "University Libraries",
        "parking":            "Parking & Transportation",
        "registrar":          "Registrar",
        "student_affairs":    "Student Affairs",
        "tuition_financial_aid": "Tuition & Financial Aid",
    }


def get_embedding_model():
    from fastembed import TextEmbedding
    from app.core.config import get_settings
    settings = get_settings()
    print(f"  Loading embedding model: {settings.local_embedding_model}")
    return TextEmbedding(settings.local_embedding_model)


def embed_batch(model, texts: list[str]) -> list[list[float]]:
    return [emb.tolist() for emb in model.embed(texts)]


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

    if existing and reload:
        print("Reload requested — clearing existing crawled data...")
        names = list(category_names_map().values())
        result2 = await db.execute(select(Source).where(Source.name.in_(names)))
        for src in result2.scalars().all():
            # Delete documents and chunks belonging to this source first
            docs_result = await db.execute(select(Document).where(Document.source_id == src.id))
            for doc in docs_result.scalars().all():
                await db.delete(doc)
            await db.delete(src)
        await db.flush()
        print("  Cleared old sources/documents/chunks.")

    # Load embedding model
    model = get_embedding_model()

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
        embeddings = embed_batch(model, texts)

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
