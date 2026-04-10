"""Retrieval service: vector search, hybrid retrieval, citation packaging."""
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text, func
from app.models.models import Chunk, Document, Source, OfficeContact, FAQEntry
from app.services.ai_providers import get_embedding_provider
from app.schemas.schemas import Citation, OfficeRouting


async def retrieve_chunks(
    db: AsyncSession,
    query: str,
    top_k: int = 5,
    category_filter: str | None = None,
) -> list[dict]:
    """Hybrid retrieval: vector similarity + keyword fallback."""
    provider = get_embedding_provider()
    query_embedding = await provider.embed_query(query)

    # Vector search with pgvector
    embedding_str = f"[{','.join(str(x) for x in query_embedding)}]"

    sql = text("""
        SELECT c.id, c.content, c.heading, c.chunk_index, c.metadata,
               d.title, d.source_url, d.content_type, d.is_archived,
               s.name as source_name, s.category, s.office, s.authority_score,
               (c.embedding <=> CAST(:embedding AS vector)) as distance
        FROM chunks c
        JOIN documents d ON c.document_id = d.id
        JOIN sources s ON d.source_id = s.id
        WHERE d.status = 'indexed'
          AND d.is_archived = false
          AND s.is_active = true
        ORDER BY distance ASC
        LIMIT :top_k
    """)

    result = await db.execute(sql, {"embedding": embedding_str, "top_k": top_k})
    rows = result.fetchall()

    chunks = []
    for row in rows:
        chunks.append({
            "chunk_id": str(row.id),
            "content": row.content,
            "heading": row.heading,
            "title": row.title,
            "source_url": row.source_url,
            "source_name": row.source_name,
            "category": row.category,
            "office": row.office,
            "authority_score": row.authority_score,
            "distance": row.distance,
            "is_archived": row.is_archived,
        })

    # If no vector results, fall back to keyword search
    if not chunks:
        chunks = await _keyword_search(db, query, top_k)

    return chunks


async def _keyword_search(db: AsyncSession, query: str, top_k: int) -> list[dict]:
    """Simple keyword-based fallback search."""
    search_term = f"%{query.lower()}%"
    stmt = (
        select(Chunk, Document, Source)
        .join(Document, Chunk.document_id == Document.id)
        .join(Source, Document.source_id == Source.id)
        .where(
            Document.status == "indexed",
            Document.is_archived == False,
            Source.is_active == True,
            func.lower(Chunk.content).contains(search_term),
        )
        .limit(top_k)
    )
    result = await db.execute(stmt)
    rows = result.all()
    return [
        {
            "chunk_id": str(chunk.id),
            "content": chunk.content,
            "heading": chunk.heading,
            "title": doc.title,
            "source_url": doc.source_url,
            "source_name": source.name,
            "category": source.category.value if source.category else "general",
            "office": source.office,
            "authority_score": source.authority_score,
            "distance": 1.0,
            "is_archived": doc.is_archived,
        }
        for chunk, doc, source in rows
    ]


async def check_faq_match(db: AsyncSession, query: str) -> FAQEntry | None:
    """Check if query matches a curated FAQ entry."""
    search = f"%{query.lower()[:80]}%"
    stmt = (
        select(FAQEntry)
        .where(FAQEntry.is_active == True, func.lower(FAQEntry.question).contains(search))
        .order_by(FAQEntry.priority.desc())
        .limit(1)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


def build_citations(chunks: list[dict]) -> list[Citation]:
    """Package retrieved chunks into citation objects."""
    seen_urls = set()
    citations = []
    for chunk in chunks:
        url = chunk["source_url"]
        if url in seen_urls:
            continue
        seen_urls.add(url)
        citations.append(Citation(
            title=chunk["title"],
            url=url,
            snippet=chunk["content"][:200] + "..." if len(chunk["content"]) > 200 else chunk["content"],
            office=chunk.get("office"),
            category=chunk.get("category"),
        ))
    return citations


async def find_office_routing(
    db: AsyncSession, query: str, chunks: list[dict]
) -> OfficeRouting | None:
    """Determine if the query should route to a specific office."""
    # Check if retrieved chunks point to a specific office
    offices = [c.get("office") for c in chunks if c.get("office")]
    if not offices:
        return None

    # Most common office from results
    from collections import Counter
    most_common = Counter(offices).most_common(1)[0][0]

    stmt = select(OfficeContact).where(OfficeContact.office_key == most_common)
    result = await db.execute(stmt)
    contact = result.scalar_one_or_none()

    if contact:
        return OfficeRouting(
            name=contact.name,
            office_key=contact.office_key,
            phone=contact.phone,
            email=contact.email,
            url=contact.url,
            reason=f"This question relates to {contact.name}",
        )
    return None


def generate_follow_ups(query: str, chunks: list[dict]) -> list[str]:
    """Generate contextual follow-up questions based on retrieved content."""
    categories = set(c.get("category", "") for c in chunks)
    follow_ups = []

    category_questions = {
        "admissions": "What are the application deadlines for Stony Brook?",
        "registrar": "How do I access my academic transcript?",
        "bursar": "What are the tuition payment options?",
        "financial_aid": "What scholarships are available at Stony Brook?",
        "housing": "What are the campus housing options?",
        "dining": "What meal plans are available?",
        "academics": "What are the degree requirements?",
    }

    for cat in categories:
        if cat in category_questions:
            follow_ups.append(category_questions[cat])
        if len(follow_ups) >= 3:
            break

    if not follow_ups:
        follow_ups = [
            "What programs does Stony Brook offer?",
            "How do I apply to Stony Brook University?",
            "Where can I find campus resources?",
        ]

    return follow_ups[:3]
