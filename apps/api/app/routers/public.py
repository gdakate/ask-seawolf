"""Public API routes: chat, topics, search, feedback, health."""
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.core.database import get_db
from app.models.models import (
    Source, Document, Chunk, ChatSession, ChatMessage, UserFeedback,
    OfficeContact, FAQEntry, SourceCategory,
)
from app.schemas.schemas import (
    ChatQueryRequest, ChatQueryResponse, Citation, FeedbackCreate, FeedbackOut,
    TopicOut, DocumentOut, OfficeContactOut, SearchResult,
)
from app.services.retrieval import (
    retrieve_chunks, build_citations, find_office_routing,
    generate_follow_ups, check_faq_match,
)
from app.services.answering import generate_answer, should_warn_term_dependent

router = APIRouter()


@router.get("/health")
async def health_check():
    return {"status": "healthy", "service": "sbu-assistant-api", "timestamp": datetime.now(timezone.utc).isoformat()}


@router.post("/chat/query", response_model=ChatQueryResponse)
async def chat_query(req: ChatQueryRequest, db: AsyncSession = Depends(get_db)):
    """Main chat endpoint: retrieve context, generate answer, return with citations."""
    import time
    start = time.time()

    # Get or create session
    session_id = req.session_id or str(uuid.uuid4())
    stmt = select(ChatSession).where(ChatSession.session_token == session_id)
    result = await db.execute(stmt)
    session = result.scalar_one_or_none()
    if not session:
        session = ChatSession(session_token=session_id)
        db.add(session)
        await db.flush()

    # Check FAQ match first
    faq = await check_faq_match(db, req.query)
    if faq:
        # FAQ response with supporting citations from retrieval
        chunks = await retrieve_chunks(db, req.query, top_k=3)
        citations = build_citations(chunks)
        follow_ups = generate_follow_ups(req.query, chunks)
        office = await find_office_routing(db, req.query, chunks)

        user_msg = ChatMessage(session_id=session.id, role="user", content=req.query)
        db.add(user_msg)
        asst_msg = ChatMessage(
            session_id=session.id, role="assistant", content=faq.answer,
            citations=[c.model_dump() for c in citations],
            confidence_score=1.0,
            office_routing=office.model_dump() if office else None,
            follow_up_questions=follow_ups,
        )
        db.add(asst_msg)

        return ChatQueryResponse(
            answer=faq.answer,
            citations=citations,
            office_routing=office,
            confidence_score=1.0,
            session_id=session_id,
            follow_up_questions=follow_ups,
        )

    # RAG pipeline
    chunks = await retrieve_chunks(db, req.query, top_k=5)
    citations = build_citations(chunks)
    answer, confidence = await generate_answer(req.query, chunks)
    office = await find_office_routing(db, req.query, chunks)
    follow_ups = generate_follow_ups(req.query, chunks)
    warning = should_warn_term_dependent(chunks, req.query)

    latency_ms = int((time.time() - start) * 1000)

    # Store messages
    user_msg = ChatMessage(session_id=session.id, role="user", content=req.query)
    db.add(user_msg)

    asst_msg = ChatMessage(
        session_id=session.id, role="assistant", content=answer,
        citations=[c.model_dump() for c in citations],
        confidence_score=confidence,
        office_routing=office.model_dump() if office else None,
        follow_up_questions=follow_ups,
        latency_ms=latency_ms,
    )
    db.add(asst_msg)
    session.last_active_at = datetime.now(timezone.utc)

    return ChatQueryResponse(
        answer=answer,
        citations=citations,
        office_routing=office,
        follow_up_questions=follow_ups,
        confidence_score=confidence,
        session_id=session_id,
        warning=warning,
    )


@router.get("/topics", response_model=list[TopicOut])
async def get_topics():
    """Return browsable topic categories."""
    topics = [
        TopicOut(key="admissions", name="Admissions", description="Undergraduate and graduate admissions information", icon="GraduationCap"),
        TopicOut(key="registrar", name="Registrar", description="Registration, transcripts, and academic records", icon="FileText"),
        TopicOut(key="bursar", name="Tuition & Billing", description="Tuition rates, fees, and payment options", icon="DollarSign"),
        TopicOut(key="financial_aid", name="Financial Aid", description="Scholarships, grants, loans, and work-study", icon="Wallet"),
        TopicOut(key="housing", name="Housing", description="Campus residences and housing applications", icon="Home"),
        TopicOut(key="dining", name="Dining", description="Meal plans, dining locations, and hours", icon="UtensilsCrossed"),
        TopicOut(key="academics", name="Academics", description="Programs, policies, and academic resources", icon="BookOpen"),
        TopicOut(key="student_affairs", name="Student Life", description="Clubs, activities, and campus services", icon="Users"),
    ]
    return topics


@router.get("/sources/{source_id}")
async def get_source(source_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    stmt = select(Source).where(Source.id == source_id)
    result = await db.execute(stmt)
    source = result.scalar_one_or_none()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    return source


@router.get("/search")
async def search_documents(
    q: str = Query(..., min_length=1),
    category: str | None = None,
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
):
    search_term = f"%{q.lower()}%"
    stmt = (
        select(Document)
        .join(Source)
        .where(
            Document.is_archived == False,
            Source.is_active == True,
            func.lower(Document.title).contains(search_term),
        )
    )
    if category:
        stmt = stmt.where(Source.category == category)

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar() or 0

    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(stmt)
    docs = result.scalars().all()

    return {
        "items": [DocumentOut.model_validate(d) for d in docs],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.post("/feedback", response_model=FeedbackOut)
async def submit_feedback(req: FeedbackCreate, db: AsyncSession = Depends(get_db)):
    fb = UserFeedback(
        message_id=req.message_id,
        rating=req.rating,
        comment=req.comment,
        feedback_type=req.feedback_type,
    )
    db.add(fb)
    await db.flush()
    return FeedbackOut.model_validate(fb)


@router.get("/offices", response_model=list[OfficeContactOut])
async def get_offices(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(OfficeContact))
    return [OfficeContactOut.model_validate(o) for o in result.scalars().all()]
