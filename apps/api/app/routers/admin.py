"""Admin API routes: auth, dashboard, sources, documents, jobs, feedback, FAQs, evaluation."""
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from app.core.database import get_db
from app.core.auth import (
    hash_password, verify_password, create_access_token, get_current_admin,
)
from app.core.config import get_settings
from app.models.models import (
    AdminUser, Source, Document, Chunk, CrawlJob, IndexJob,
    ChatSession, ChatMessage, UserFeedback, FAQEntry,
    EvaluationRun, EvaluationCase, AuditLog,
    DocumentStatus, JobStatus, SourceCategory,
)
from app.schemas.schemas import (
    LoginRequest, LoginResponse, SourceCreate, SourceUpdate, SourceOut,
    DocumentOut, DocumentDetail, ChunkOut, CrawlJobOut, IndexJobOut,
    FAQCreate, FAQUpdate, FAQOut, FeedbackOut,
    ChatSessionOut, ChatMessageOut, DashboardStats,
    EvaluationRunOut, EvaluationCaseOut,
)
from app.services.ingestion import run_crawl_job, run_index_job

settings = get_settings()
router = APIRouter(prefix="/admin")


# ─── Auth ────────────────────────────────────────────────────────────

@router.post("/auth/login", response_model=LoginResponse)
async def admin_login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    stmt = select(AdminUser).where(AdminUser.email == req.email, AdminUser.is_active == True)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    user.last_login_at = datetime.now(timezone.utc)
    token = create_access_token({"sub": user.email, "role": user.role})
    return LoginResponse(access_token=token, email=user.email, role=user.role)


# ─── Dashboard ───────────────────────────────────────────────────────

@router.get("/dashboard", response_model=DashboardStats)
async def dashboard(admin=Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    total_sources = (await db.execute(select(func.count(Source.id)))).scalar() or 0
    active_sources = (await db.execute(select(func.count(Source.id)).where(Source.is_active == True))).scalar() or 0
    total_docs = (await db.execute(select(func.count(Document.id)))).scalar() or 0
    indexed_docs = (await db.execute(select(func.count(Document.id)).where(Document.status == "indexed"))).scalar() or 0
    total_chunks = (await db.execute(select(func.count(Chunk.id)))).scalar() or 0
    total_sessions = (await db.execute(select(func.count(ChatSession.id)))).scalar() or 0
    total_messages = (await db.execute(select(func.count(ChatMessage.id)))).scalar() or 0
    total_feedback = (await db.execute(select(func.count(UserFeedback.id)))).scalar() or 0
    avg_conf = (await db.execute(select(func.avg(ChatMessage.confidence_score)).where(ChatMessage.confidence_score.isnot(None)))).scalar()

    crawl_result = await db.execute(select(CrawlJob).order_by(desc(CrawlJob.created_at)).limit(5))
    index_result = await db.execute(select(IndexJob).order_by(desc(IndexJob.created_at)).limit(5))

    return DashboardStats(
        total_sources=total_sources, active_sources=active_sources,
        total_documents=total_docs, indexed_documents=indexed_docs,
        total_chunks=total_chunks, total_sessions=total_sessions,
        total_messages=total_messages, total_feedback=total_feedback,
        avg_confidence=round(avg_conf, 3) if avg_conf else None,
        recent_crawl_jobs=[CrawlJobOut.model_validate(j) for j in crawl_result.scalars().all()],
        recent_index_jobs=[IndexJobOut.model_validate(j) for j in index_result.scalars().all()],
    )


# ─── Sources CRUD ────────────────────────────────────────────────────

@router.get("/sources", response_model=list[SourceOut])
async def list_sources(admin=Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Source).order_by(Source.created_at.desc()))
    return [SourceOut.model_validate(s) for s in result.scalars().all()]


@router.post("/sources", response_model=SourceOut)
async def create_source(req: SourceCreate, admin=Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    source = Source(name=req.name, url=req.url, category=SourceCategory(req.category),
                    office=req.office, crawl_frequency_hours=req.crawl_frequency_hours,
                    authority_score=req.authority_score)
    db.add(source)
    db.add(AuditLog(admin_email=admin["email"], action="create_source", resource_type="source", details={"name": req.name}))
    await db.flush()
    return SourceOut.model_validate(source)


@router.put("/sources/{source_id}", response_model=SourceOut)
async def update_source(source_id: uuid.UUID, req: SourceUpdate, admin=Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Source).where(Source.id == source_id))
    source = result.scalar_one_or_none()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    for field, value in req.model_dump(exclude_unset=True).items():
        if field == "category" and value:
            setattr(source, field, SourceCategory(value))
        else:
            setattr(source, field, value)
    db.add(AuditLog(admin_email=admin["email"], action="update_source", resource_type="source", resource_id=str(source_id)))
    return SourceOut.model_validate(source)


@router.delete("/sources/{source_id}")
async def delete_source(source_id: uuid.UUID, admin=Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Source).where(Source.id == source_id))
    source = result.scalar_one_or_none()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    await db.delete(source)
    db.add(AuditLog(admin_email=admin["email"], action="delete_source", resource_type="source", resource_id=str(source_id)))
    return {"status": "deleted"}


# ─── Documents ───────────────────────────────────────────────────────

@router.get("/documents", response_model=list[DocumentOut])
async def list_documents(
    status: str | None = None, source_id: uuid.UUID | None = None,
    page: int = 1, page_size: int = 50,
    admin=Depends(get_current_admin), db: AsyncSession = Depends(get_db),
):
    stmt = select(Document).order_by(Document.created_at.desc())
    if status:
        stmt = stmt.where(Document.status == status)
    if source_id:
        stmt = stmt.where(Document.source_id == source_id)
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(stmt)
    return [DocumentOut.model_validate(d) for d in result.scalars().all()]


@router.get("/documents/{doc_id}")
async def get_document(doc_id: uuid.UUID, admin=Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Document).where(Document.id == doc_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    chunk_count = (await db.execute(select(func.count(Chunk.id)).where(Chunk.document_id == doc_id))).scalar() or 0
    data = DocumentDetail.model_validate(doc)
    data.chunk_count = chunk_count
    return data


# ─── Chunks ──────────────────────────────────────────────────────────

@router.get("/chunks", response_model=list[ChunkOut])
async def list_chunks(
    document_id: uuid.UUID | None = None, page: int = 1, page_size: int = 50,
    admin=Depends(get_current_admin), db: AsyncSession = Depends(get_db),
):
    stmt = select(Chunk).order_by(Chunk.created_at.desc())
    if document_id:
        stmt = stmt.where(Chunk.document_id == document_id)
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(stmt)
    return [ChunkOut.model_validate(c) for c in result.scalars().all()]


# ─── Jobs ────────────────────────────────────────────────────────────

@router.post("/crawl", response_model=CrawlJobOut)
async def trigger_crawl(source_id: uuid.UUID | None = None, admin=Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    job = await run_crawl_job(db, source_id)
    db.add(AuditLog(admin_email=admin["email"], action="trigger_crawl", resource_type="crawl_job", resource_id=str(job.id)))
    return CrawlJobOut.model_validate(job)


@router.post("/reindex", response_model=IndexJobOut)
async def trigger_reindex(admin=Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    job = await run_index_job(db)
    db.add(AuditLog(admin_email=admin["email"], action="trigger_reindex", resource_type="index_job", resource_id=str(job.id)))
    return IndexJobOut.model_validate(job)


# ─── Conversations ───────────────────────────────────────────────────

@router.get("/conversations")
async def list_conversations(page: int = 1, page_size: int = 50, admin=Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    stmt = (
        select(ChatSession, func.count(ChatMessage.id).label("msg_count"))
        .outerjoin(ChatMessage)
        .group_by(ChatSession.id)
        .order_by(desc(ChatSession.last_active_at))
        .offset((page - 1) * page_size).limit(page_size)
    )
    result = await db.execute(stmt)
    rows = result.all()
    return [
        {**ChatSessionOut.model_validate(session).model_dump(), "message_count": count}
        for session, count in rows
    ]


@router.get("/conversations/{session_id}/messages", response_model=list[ChatMessageOut])
async def get_conversation_messages(session_id: uuid.UUID, admin=Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ChatMessage).where(ChatMessage.session_id == session_id).order_by(ChatMessage.created_at)
    )
    return [ChatMessageOut.model_validate(m) for m in result.scalars().all()]


# ─── Feedback ────────────────────────────────────────────────────────

@router.get("/feedback", response_model=list[FeedbackOut])
async def list_feedback(page: int = 1, page_size: int = 50, admin=Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(UserFeedback).order_by(desc(UserFeedback.created_at)).offset((page - 1) * page_size).limit(page_size))
    return [FeedbackOut.model_validate(f) for f in result.scalars().all()]


# ─── FAQs CRUD ───────────────────────────────────────────────────────

@router.get("/faqs", response_model=list[FAQOut])
async def list_faqs(admin=Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(FAQEntry).order_by(FAQEntry.priority.desc()))
    return [FAQOut.model_validate(f) for f in result.scalars().all()]


@router.post("/faqs", response_model=FAQOut)
async def create_faq(req: FAQCreate, admin=Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    faq = FAQEntry(question=req.question, answer=req.answer, category=SourceCategory(req.category),
                   office_key=req.office_key, priority=req.priority)
    db.add(faq)
    await db.flush()
    return FAQOut.model_validate(faq)


@router.put("/faqs/{faq_id}", response_model=FAQOut)
async def update_faq(faq_id: uuid.UUID, req: FAQUpdate, admin=Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(FAQEntry).where(FAQEntry.id == faq_id))
    faq = result.scalar_one_or_none()
    if not faq:
        raise HTTPException(status_code=404, detail="FAQ not found")
    for field, value in req.model_dump(exclude_unset=True).items():
        if field == "category" and value:
            setattr(faq, field, SourceCategory(value))
        else:
            setattr(faq, field, value)
    return FAQOut.model_validate(faq)


@router.delete("/faqs/{faq_id}")
async def delete_faq(faq_id: uuid.UUID, admin=Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(FAQEntry).where(FAQEntry.id == faq_id))
    faq = result.scalar_one_or_none()
    if not faq:
        raise HTTPException(status_code=404, detail="FAQ not found")
    await db.delete(faq)
    return {"status": "deleted"}


# ─── Evaluations ─────────────────────────────────────────────────────

@router.get("/evaluations", response_model=list[EvaluationRunOut])
async def list_evaluations(admin=Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(EvaluationRun).order_by(desc(EvaluationRun.created_at)))
    return [EvaluationRunOut.model_validate(e) for e in result.scalars().all()]


@router.post("/evaluations/run", response_model=EvaluationRunOut)
async def run_evaluation(name: str = "Manual Run", admin=Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    run = EvaluationRun(name=name, status=JobStatus.COMPLETED, completed_at=datetime.now(timezone.utc))
    db.add(run)
    db.add(AuditLog(admin_email=admin["email"], action="run_evaluation", resource_type="evaluation_run"))
    await db.flush()
    return EvaluationRunOut.model_validate(run)
