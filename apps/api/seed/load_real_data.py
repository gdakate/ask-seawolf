"""Load real SBU crawled data from documents_chunked.json into the database.

Generates embeddings using fastembed (local, no API key needed).
Run: python -m seed.load_real_data
"""
import asyncio
import hashlib
import json
import os
from pathlib import Path
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session
from app.models.models import Source, Document, Chunk, SourceCategory, DocumentStatus, ContentType

DATA_FILE = Path(__file__).parent.parent / "data" / "documents_chunked.json"
BATCH_SIZE = 64  # chunks to embed at once


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


async def load(db: AsyncSession):
    print(f"Loading data from {DATA_FILE}...")
    with open(DATA_FILE, encoding="utf-8") as f:
        chunks_data = json.load(f)

    print(f"  {len(chunks_data)} chunks across dataset")

    # Check if already loaded
    result = await db.execute(
        select(Source).where(Source.name == "SBU Crawled Dataset")
    )
    if result.scalar_one_or_none():
        print("Real data already loaded. Skipping.")
        return

    # Load embedding model
    model = get_embedding_model()

    # Group chunks by category → source, and by URL → document
    sources: dict[str, Source] = {}
    documents: dict[str, Document] = {}

    # Create one Source per category
    category_names = {
        "academic_calendar": "Academic Calendar",
        "building_hours": "Building Hours",
        "clubs": "Student Clubs & Organizations",
        "dining": "Dining Services",
        "faq": "SBU FAQ",
        "housing": "Campus Housing",
        "it_help": "IT Help & Services",
        "library": "University Libraries",
        "parking": "Parking & Transportation",
        "tuition_financial_aid": "Tuition & Financial Aid",
    }

    for cat, display_name in category_names.items():
        src = Source(
            name=display_name,
            url=f"https://www.stonybrook.edu/{cat}/",
            category=safe_category(cat),
            office=cat,
            authority_score=1.0,
            is_active=True,
        )
        db.add(src)
        sources[cat] = src

    await db.flush()
    print(f"  Created {len(sources)} sources")

    # Create Documents (one per unique URL)
    for item in chunks_data:
        url = item["url"]
        if url in documents:
            continue
        cat = item["category"]
        src = sources.get(cat, sources.get("faq"))
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
    all_items = chunks_data
    total = len(all_items)
    created = 0

    for batch_start in range(0, total, BATCH_SIZE):
        batch = all_items[batch_start: batch_start + BATCH_SIZE]
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
    async with async_session() as db:
        await load(db)


if __name__ == "__main__":
    asyncio.run(main())
