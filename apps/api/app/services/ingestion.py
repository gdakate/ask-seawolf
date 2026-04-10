"""Ingestion service: crawling, HTML cleaning, chunking, embedding."""
import hashlib
import re
import uuid
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.models import (
    Source, Document, Chunk, CrawlJob, IndexJob,
    DocumentStatus, JobStatus, ContentType,
)
from app.services.ai_providers import get_embedding_provider


# ─── HTML Cleaning ───────────────────────────────────────────────────

def clean_html(raw_html: str) -> str:
    """Strip HTML tags and normalize whitespace."""
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(raw_html, "lxml")
    for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()
    text = soup.get_text(separator="\n")
    lines = [line.strip() for line in text.splitlines()]
    return "\n".join(line for line in lines if line)


def compute_hash(content: str) -> str:
    return hashlib.sha256(content.encode()).hexdigest()


# ─── Heading-Aware Chunking ─────────────────────────────────────────

def chunk_by_headings(text: str, max_chunk_size: int = 800, overlap: int = 100) -> list[dict]:
    """Split text into chunks respecting heading boundaries."""
    heading_pattern = re.compile(r'^(#{1,4})\s+(.+)$|^([A-Z][A-Z\s]{3,})$', re.MULTILINE)
    chunks = []
    current_chunk = ""
    current_heading = None
    chunk_index = 0

    lines = text.split("\n")
    for line in lines:
        match = heading_pattern.match(line.strip())
        if match and len(current_chunk.strip()) > 50:
            # Save current chunk
            chunks.append({
                "content": current_chunk.strip(),
                "heading": current_heading,
                "chunk_index": chunk_index,
            })
            chunk_index += 1
            current_heading = line.strip().lstrip("#").strip()
            current_chunk = line + "\n"
        else:
            if match:
                current_heading = line.strip().lstrip("#").strip()
            current_chunk += line + "\n"

            # Split if too long
            if len(current_chunk) > max_chunk_size:
                chunks.append({
                    "content": current_chunk.strip(),
                    "heading": current_heading,
                    "chunk_index": chunk_index,
                })
                chunk_index += 1
                # Keep overlap
                words = current_chunk.split()
                overlap_words = words[-overlap // 5:] if len(words) > overlap // 5 else []
                current_chunk = " ".join(overlap_words) + "\n"

    if current_chunk.strip():
        chunks.append({
            "content": current_chunk.strip(),
            "heading": current_heading,
            "chunk_index": chunk_index,
        })

    return chunks


# ─── Document Ingestion ─────────────────────────────────────────────

async def ingest_document(
    db: AsyncSession,
    source_id: uuid.UUID,
    title: str,
    url: str,
    raw_content: str,
    content_type: str = "html",
) -> Document:
    """Ingest a single document: clean, hash, store."""
    if content_type == "html":
        cleaned = clean_html(raw_content)
    else:
        cleaned = raw_content

    content_hash = compute_hash(cleaned)

    # Check for existing version
    stmt = select(Document).where(Document.source_url == url, Document.content_hash == content_hash)
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()
    if existing:
        existing.last_seen_at = datetime.now(timezone.utc)
        return existing

    doc = Document(
        source_id=source_id,
        title=title,
        source_url=url,
        content_type=ContentType(content_type),
        raw_content=raw_content,
        cleaned_content=cleaned,
        content_hash=content_hash,
        status=DocumentStatus.INGESTED,
        last_seen_at=datetime.now(timezone.utc),
    )
    db.add(doc)
    await db.flush()
    return doc


# ─── Indexing (Chunking + Embedding) ────────────────────────────────

async def index_document(db: AsyncSession, document: Document) -> int:
    """Chunk a document and generate embeddings for each chunk."""
    if not document.cleaned_content:
        return 0

    # Remove old chunks
    stmt = select(Chunk).where(Chunk.document_id == document.id)
    result = await db.execute(stmt)
    old_chunks = result.scalars().all()
    for c in old_chunks:
        await db.delete(c)

    # Chunk the content
    chunk_dicts = chunk_by_headings(document.cleaned_content)
    if not chunk_dicts:
        return 0

    # Generate embeddings
    provider = get_embedding_provider()
    texts = [c["content"] for c in chunk_dicts]
    embeddings = await provider.embed(texts)

    # Create chunk records
    for chunk_dict, embedding in zip(chunk_dicts, embeddings):
        chunk = Chunk(
            document_id=document.id,
            chunk_index=chunk_dict["chunk_index"],
            content=chunk_dict["content"],
            heading=chunk_dict.get("heading"),
            token_count=len(chunk_dict["content"].split()),
            embedding=embedding,
        )
        db.add(chunk)

    document.status = DocumentStatus.INDEXED
    await db.flush()
    return len(chunk_dicts)


async def run_crawl_job(db: AsyncSession, source_id: uuid.UUID | None = None) -> CrawlJob:
    """Create and run a crawl job (stub for real crawler)."""
    job = CrawlJob(
        source_id=source_id,
        status=JobStatus.RUNNING,
        started_at=datetime.now(timezone.utc),
    )
    db.add(job)
    await db.flush()

    # In production, this would use httpx to crawl pages
    # For now, mark as completed
    job.status = JobStatus.COMPLETED
    job.completed_at = datetime.now(timezone.utc)
    return job


async def run_index_job(db: AsyncSession) -> IndexJob:
    """Index all ingested but unindexed documents."""
    job = IndexJob(
        status=JobStatus.RUNNING,
        started_at=datetime.now(timezone.utc),
    )
    db.add(job)
    await db.flush()

    stmt = select(Document).where(Document.status == DocumentStatus.INGESTED)
    result = await db.execute(stmt)
    documents = result.scalars().all()

    total_chunks = 0
    for doc in documents:
        try:
            n = await index_document(db, doc)
            total_chunks += n
            job.documents_processed += 1
        except Exception as e:
            doc.status = DocumentStatus.FAILED
            job.error_message = str(e)

    job.chunks_created = total_chunks
    job.status = JobStatus.COMPLETED
    job.completed_at = datetime.now(timezone.utc)
    return job
