"""Admin API routes: auth, dashboard, sources, documents, jobs, feedback, FAQs, evaluation."""
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from app.core.database import get_db
from app.core.auth import (
    hash_password, verify_password, create_access_token, get_current_admin, validate_sbu_email,
)
from app.core.config import get_settings
from app.models.models import (
    AdminUser, Source, Document, Chunk, CrawlJob, IndexJob,
    ChatSession, ChatMessage, UserFeedback, FAQEntry,
    EvaluationRun, EvaluationCase, AuditLog,
    DocumentStatus, JobStatus, SourceCategory,
)
from app.schemas.schemas import (
    LoginRequest, LoginResponse, RegisterRequest, SourceCreate, SourceUpdate, SourceOut,
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
    validate_sbu_email(req.email)
    stmt = select(AdminUser).where(AdminUser.email == req.email, AdminUser.is_active == True)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    user.last_login_at = datetime.now(timezone.utc)
    token = create_access_token({"sub": user.email, "role": user.role})
    return LoginResponse(access_token=token, email=user.email, role=user.role)


@router.post("/auth/register", response_model=LoginResponse, status_code=201)
async def admin_register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    validate_sbu_email(req.email)
    existing = (await db.execute(select(AdminUser).where(AdminUser.email == req.email))).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")

    user = AdminUser(email=req.email, password_hash=hash_password(req.password), name=req.name)
    db.add(user)
    await db.flush()
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


# ─── Analytics ───────────────────────────────────────────────────────

CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "admissions":    ["apply", "application", "admission", "deadline", "transfer", "accept"],
    "bursar":        ["tuition", "billing", "pay", "fee", "cost", "charge", "refund", "bill"],
    "financial_aid": ["financial aid", "fafsa", "scholarship", "grant", "loan", "aid", "award"],
    "housing":       ["housing", "dorm", "residence", "room", "residential", "roommate", "live"],
    "registrar":     ["register", "registration", "transcript", "withdraw", "schedule", "enroll", "course"],
    "dining":        ["dining", "meal plan", "food", "cafe", "eat", "meal"],
    "academics":     ["class", "program", "degree", "major", "graduate", "professor", "credit"],
    "it_services":   ["netid", "password", "it help", "software", "wifi", "login", "account"],
}

def _categorize(text: str) -> str:
    t = text.lower()
    for cat, keywords in CATEGORY_KEYWORDS.items():
        if any(kw in t for kw in keywords):
            return cat
    return "general"


@router.get("/analytics")
async def get_analytics(admin=Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    # Core counts
    total_sources   = (await db.execute(select(func.count(Source.id)))).scalar() or 0
    total_documents = (await db.execute(select(func.count(Document.id)))).scalar() or 0
    total_chunks    = (await db.execute(select(func.count(Chunk.id)))).scalar() or 0
    total_sessions  = (await db.execute(select(func.count(ChatSession.id)))).scalar() or 0
    total_messages  = (await db.execute(select(func.count(ChatMessage.id)))).scalar() or 0

    # FAQ hits: assistant messages where confidence = 1.0 (FAQ fast-path)
    faq_hit_count = (await db.execute(
        select(func.count(ChatMessage.id)).where(
            ChatMessage.role == "assistant",
            ChatMessage.confidence_score == 1.0,
        )
    )).scalar() or 0

    # Low confidence: assistant messages with conf < 0.3 (excludes None)
    low_conf_count = (await db.execute(
        select(func.count(ChatMessage.id)).where(
            ChatMessage.role == "assistant",
            ChatMessage.confidence_score.isnot(None),
            ChatMessage.confidence_score < 0.3,
        )
    )).scalar() or 0

    avg_conf_row = (await db.execute(
        select(func.avg(ChatMessage.confidence_score)).where(
            ChatMessage.role == "assistant",
            ChatMessage.confidence_score.isnot(None),
        )
    )).scalar()

    # Top categories: derive from user messages via keyword matching
    user_msgs_result = await db.execute(
        select(ChatMessage.content).where(ChatMessage.role == "user").limit(500)
    )
    category_counts: dict[str, int] = {}
    for (content,) in user_msgs_result:
        cat = _categorize(content)
        category_counts[cat] = category_counts.get(cat, 0) + 1
    top_categories = sorted(
        [{"category": k, "count": v} for k, v in category_counts.items()],
        key=lambda x: x["count"], reverse=True
    )[:7]

    # Recent queries: last 20 user messages + paired confidence
    recent_result = await db.execute(
        select(ChatMessage).where(ChatMessage.role == "user")
        .order_by(desc(ChatMessage.created_at)).limit(20)
    )
    recent_user_msgs = recent_result.scalars().all()

    # For each user msg, find next assistant msg in same session
    recent_queries = []
    for msg in recent_user_msgs:
        asst = (await db.execute(
            select(ChatMessage).where(
                ChatMessage.session_id == msg.session_id,
                ChatMessage.role == "assistant",
                ChatMessage.created_at > msg.created_at,
            ).order_by(ChatMessage.created_at).limit(1)
        )).scalar_one_or_none()
        recent_queries.append({
            "query":      msg.content[:120],
            "created_at": msg.created_at.isoformat(),
            "confidence": asst.confidence_score if asst else None,
        })

    return {
        "total_sources":       total_sources,
        "total_documents":     total_documents,
        "total_chunks":        total_chunks,
        "total_sessions":      total_sessions,
        "total_messages":      total_messages,
        "faq_hit_count":       faq_hit_count,
        "low_confidence_count": low_conf_count,
        "avg_confidence":      round(avg_conf_row, 3) if avg_conf_row else None,
        "top_categories":      top_categories,
        "recent_queries":      recent_queries,
    }


# ─── FAQ Suggestions ─────────────────────────────────────────────────

_STOP_WORDS = {
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "can", "i", "me", "my", "we", "our", "you",
    "your", "he", "she", "it", "they", "them", "what", "which", "who",
    "how", "when", "where", "why", "much", "many", "at", "by", "for",
    "with", "about", "into", "through", "before", "after", "to", "from",
    "in", "out", "on", "off", "of", "and", "but", "or", "not", "just",
    "as", "if", "than", "very", "so", "get", "also", "there", "their",
    "this", "that", "these", "those", "want", "need", "know", "tell",
    "please", "help", "like", "make", "look", "see", "go", "come",
}

def _key_tokens(text: str) -> frozenset[str]:
    import re
    tokens = re.sub(r"[^a-z0-9\s]", "", text.lower()).split()
    return frozenset(t for t in tokens if t not in _STOP_WORDS and len(t) > 2)

def _jaccard(a: frozenset, b: frozenset) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)

def _covered_by_faqs(tokens: frozenset, faq_token_sets: list[frozenset]) -> bool:
    """Return True if any existing FAQ question is semantically close to this query."""
    return any(_jaccard(tokens, ft) >= 0.40 for ft in faq_token_sets)


@router.get("/faq-suggestions")
async def get_faq_suggestions(admin=Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    """Derive FAQ candidates from conversation history with semantic clustering."""
    # Fetch all user messages (last 500 for performance)
    user_msgs_result = await db.execute(
        select(ChatMessage).where(ChatMessage.role == "user")
        .order_by(ChatMessage.created_at.desc()).limit(500)
    )
    user_msgs = user_msgs_result.scalars().all()

    # Pre-compute token sets for existing FAQ questions
    faq_result = await db.execute(select(FAQEntry.question))
    faq_token_sets = [_key_tokens(q) for (q,) in faq_result]

    # Clusters: list of {"tokens", "queries", "count", "confidences", "representative"}
    clusters: list[dict] = []

    for msg in user_msgs:
        text = msg.content.strip()
        if not text or len(text) < 5:
            continue
        tokens = _key_tokens(text)
        if not tokens:
            continue

        # Skip if already covered by an existing FAQ
        if _covered_by_faqs(tokens, faq_token_sets):
            continue

        # Find the best matching cluster (greedy nearest-neighbour)
        best_idx, best_sim = -1, 0.0
        for i, cluster in enumerate(clusters):
            sim = _jaccard(tokens, cluster["tokens"])
            if sim > best_sim:
                best_sim = sim
                best_idx = i

        # Merge if similarity exceeds threshold, else create new cluster
        MERGE_THRESHOLD = 0.30
        if best_idx >= 0 and best_sim >= MERGE_THRESHOLD:
            c = clusters[best_idx]
            c["count"] += 1
            c["queries"].append(text)
            # Keep the shortest query as representative (usually the clearest)
            if len(text) < len(c["representative"]):
                c["representative"] = text
            # Union the token sets so the cluster grows to cover variants
            c["tokens"] = c["tokens"] | tokens
        else:
            clusters.append({
                "tokens":        tokens,
                "representative": text,
                "queries":       [text],
                "count":         1,
                "confidences":   [],
            })

    # Attach confidence scores: look up the assistant reply for each query
    # Do this only for clusters with count > 1 to avoid N+1 at scale
    for cluster in clusters:
        sample = cluster["queries"][:5]  # sample up to 5 messages
        for q_text in sample:
            asst = (await db.execute(
                select(ChatMessage.confidence_score).where(
                    ChatMessage.session_id.in_(
                        select(ChatMessage.session_id).where(
                            ChatMessage.role == "user",
                            ChatMessage.content == q_text,
                        ).limit(3)
                    ),
                    ChatMessage.role == "assistant",
                ).order_by(ChatMessage.created_at).limit(1)
            )).scalar_one_or_none()
            if asst is not None:
                cluster["confidences"].append(asst)

    # Score and filter
    suggestions = []
    for cluster in clusters:
        if cluster["count"] < 1:
            continue
        avg_conf = (sum(cluster["confidences"]) / len(cluster["confidences"])
                    if cluster["confidences"] else 0.5)
        # Score: high frequency + low confidence = most urgent
        score = cluster["count"] * (1.2 - avg_conf)
        suggestions.append({
            "query":          cluster["representative"],
            "count":          cluster["count"],
            "avg_confidence": round(avg_conf, 3),
            "score":          round(score, 2),
            "category":       _categorize(cluster["representative"]),
            "variants":       list(dict.fromkeys(cluster["queries"]))[:3],  # up to 3 example variants
        })

    suggestions.sort(key=lambda x: x["score"], reverse=True)
    return suggestions[:5]


# ─── Evaluations ─────────────────────────────────────────────────────

@router.get("/evaluations", response_model=list[EvaluationRunOut])
async def list_evaluations(admin=Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(EvaluationRun).order_by(desc(EvaluationRun.created_at)))
    return [EvaluationRunOut.model_validate(e) for e in result.scalars().all()]


@router.get("/evaluations/{run_id}/cases", response_model=list[EvaluationCaseOut])
async def get_evaluation_cases(run_id: uuid.UUID, admin=Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(EvaluationCase).where(EvaluationCase.run_id == run_id).order_by(EvaluationCase.created_at)
    )
    return [EvaluationCaseOut.model_validate(c) for c in result.scalars().all()]


@router.post("/evaluations/run", response_model=EvaluationRunOut)
async def run_evaluation(name: str = "Manual Run", admin=Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    import json, os
    from app.services.retrieval import retrieve_chunks, check_faq_match
    from app.services.answering import generate_answer
    from app.services.classifier import classify_query

    # Load eval cases from alignment dataset
    eval_path = os.path.join(os.path.dirname(__file__), "..", "..", "alignment", "eval_queries.json")
    try:
        with open(eval_path) as f:
            eval_data = json.load(f)
        cases_data = eval_data.get("cases", [])[:20]  # limit to first 20 for speed
    except Exception:
        cases_data = []

    run = EvaluationRun(name=name, status=JobStatus.RUNNING)
    db.add(run)
    await db.flush()

    total, passed = 0, 0
    retrieval_scores, answer_scores = [], []

    NO_RETRIEVAL_INTENTS = {
        "greeting", "private_account_specific", "human_support_needed",
        "ambiguous_public", "out_of_scope_non_sbu", "no_meaningful_query",
    }

    for case in cases_data:
        query = case.get("query", "")
        expected_intent = case.get("intent", "")
        if not query:
            continue

        try:
            classification = await classify_query(query)
            intent = classification.intent
            intent_match = (intent == expected_intent)

            if intent in NO_RETRIEVAL_INTENTS:
                actual_answer, confidence = await generate_answer(query, [], intent=intent)
                retrieval_score = 1.0 if intent_match else 0.0
                answer_score = confidence if confidence else 0.5
                did_pass = intent_match
                notes = f"intent={intent} (expected={expected_intent})"
            else:
                faq = await check_faq_match(db, query)
                if faq:
                    actual_answer = faq.answer
                    confidence = 1.0
                    retrieval_score = 1.0
                else:
                    chunks = await retrieve_chunks(db, query, top_k=5)
                    actual_answer, confidence = await generate_answer(query, chunks)
                    retrieval_score = min(1.0, len(chunks) / 3) if chunks else 0.0

                answer_score = confidence if confidence else 0.5
                did_pass = intent_match and (confidence or 0) >= 0.3
                notes = f"intent={intent} (expected={expected_intent}), conf={confidence:.2f}" if confidence else f"intent={intent}"

            answer_scores.append(answer_score)
            retrieval_scores.append(retrieval_score)
            if did_pass:
                passed += 1
            total += 1

            eval_case = EvaluationCase(
                run_id=run.id,
                question=query,
                expected_answer=case.get("expected_behavior"),
                actual_answer=actual_answer[:500] if actual_answer else None,
                retrieval_score=round(retrieval_score, 3),
                answer_score=round(answer_score, 3),
                passed=did_pass,
                notes=notes,
            )
            db.add(eval_case)

        except Exception as e:
            total += 1
            db.add(EvaluationCase(
                run_id=run.id,
                question=query,
                actual_answer=None,
                passed=False,
                notes=f"Error: {str(e)[:200]}",
            ))

    run.status = JobStatus.COMPLETED
    run.total_cases = total
    run.passed_cases = passed
    run.avg_retrieval_score = round(sum(retrieval_scores) / len(retrieval_scores), 3) if retrieval_scores else None
    run.avg_answer_score = round(sum(answer_scores) / len(answer_scores), 3) if answer_scores else None
    run.completed_at = datetime.now(timezone.utc)

    db.add(AuditLog(admin_email=admin["email"], action="run_evaluation", resource_type="evaluation_run", resource_id=str(run.id)))
    return EvaluationRunOut.model_validate(run)


# ─── Settings ─────────────────────────────────────────────────────────

@router.get("/settings")
async def get_admin_settings(admin=Depends(get_current_admin)):
    """Return non-sensitive runtime configuration."""
    return {
        "ai_provider":           settings.ai_provider,
        "openai_model":          settings.openai_model if settings.ai_provider == "openai" else None,
        "ollama_model":          settings.ollama_model if settings.ai_provider == "local" else None,
        "bedrock_model_id":      settings.bedrock_model_id if settings.ai_provider == "bedrock" else None,
        "embedding_dimensions":  settings.embedding_dimensions,
        "storage_backend":       settings.storage_backend,
        "environment":           settings.environment,
        "jwt_expire_minutes":    settings.jwt_expire_minutes,
        "openai_key_set":        bool(settings.openai_api_key),
        "cors_origins":          settings.cors_origins,
    }
