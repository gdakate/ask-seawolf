"""Public API routes: auth, chat, topics, search, feedback, health."""
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.core.database import get_db
from app.core.auth import (
    hash_password, verify_password, create_access_token, validate_sbu_email,
)
from app.models.models import (
    Source, Document, Chunk, ChatSession, ChatMessage, UserFeedback,
    OfficeContact, FAQEntry, SourceCategory, PublicUser,
)
from app.schemas.schemas import (
    ChatQueryRequest, ChatQueryResponse, Citation, FeedbackCreate, FeedbackOut,
    TopicOut, DocumentOut, OfficeContactOut, SearchResult,
    RegisterRequest, PublicLoginResponse, LoginRequest,
)
from app.services.retrieval import (
    retrieve_chunks, build_citations, find_office_routing,
    generate_follow_ups, check_faq_match,
)
from app.services.answering import generate_answer, should_warn_term_dependent
from app.services.classifier import classify_query

router = APIRouter()


# ─── Auth ────────────────────────────────────────────────────────────

@router.post("/auth/register", response_model=PublicLoginResponse, status_code=201)
async def public_register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    validate_sbu_email(req.email)
    existing = (await db.execute(select(PublicUser).where(PublicUser.email == req.email))).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")

    user = PublicUser(email=req.email, password_hash=hash_password(req.password), name=req.name)
    db.add(user)
    await db.flush()
    token = create_access_token({"sub": str(user.id), "email": user.email, "type": "public"})
    return PublicLoginResponse(access_token=token, email=user.email, name=user.name)


@router.post("/auth/login", response_model=PublicLoginResponse)
async def public_login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    validate_sbu_email(req.email)
    stmt = select(PublicUser).where(PublicUser.email == req.email, PublicUser.is_active == True)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    user.last_login_at = datetime.now(timezone.utc)
    token = create_access_token({"sub": str(user.id), "email": user.email, "type": "public"})
    return PublicLoginResponse(access_token=token, email=user.email, name=user.name)


@router.get("/health")
async def health_check():
    return {"status": "healthy", "service": "sbu-assistant-api", "timestamp": datetime.now(timezone.utc).isoformat()}


@router.post("/chat/query", response_model=ChatQueryResponse)
async def chat_query(req: ChatQueryRequest, db: AsyncSession = Depends(get_db)):
    """Main chat endpoint with alignment layer: classify intent before retrieval."""
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

    # ── Step 1: Classify intent (hybrid rule + LLM) ───────────────────
    classification = await classify_query(req.query)
    intent = classification.intent

    # Intents that bypass retrieval entirely
    NO_RETRIEVAL_INTENTS = {
        "greeting", "private_account_specific", "human_support_needed",
        "ambiguous_public", "out_of_scope_non_sbu", "no_meaningful_query",
    }
    if intent in NO_RETRIEVAL_INTENTS:
        # For ambiguous: use the LLM-generated clarification question directly
        if intent == "ambiguous_public" and classification.clarification_question:
            answer = classification.clarification_question
            confidence = classification.confidence
        else:
            answer, confidence = await generate_answer(req.query, [], intent=intent)

        user_msg = ChatMessage(session_id=session.id, role="user", content=req.query)
        db.add(user_msg)
        asst_msg = ChatMessage(
            session_id=session.id, role="assistant", content=answer,
            confidence_score=confidence,
            citations=None, office_routing=None, follow_up_questions=None,
        )
        db.add(asst_msg)
        session.last_active_at = datetime.now(timezone.utc)

        return ChatQueryResponse(
            answer=answer,
            citations=[],
            confidence_score=confidence,
            session_id=session_id,
            follow_up_questions=[],
        )

    # ── Step 2: FAQ fast-path (public_school_info only) ───────────────
    faq = await check_faq_match(db, req.query)
    if faq:
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

    # ── Step 3: RAG pipeline (public_school_info) ─────────────────────
    chunks = await retrieve_chunks(db, req.query, top_k=10)
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
        # ── Core academics ────────────────────────────────────────────────
        TopicOut(key="undergraduate_admissions", name="Undergraduate Admissions", description="Apply to SBU, deadlines, requirements, and scholarships", icon="GraduationCap"),
        TopicOut(key="graduate_admissions",      name="Graduate Admissions",      description="Masters and PhD programs, applications, and funding", icon="GraduationCap"),
        TopicOut(key="academic_calendar",        name="Academic Calendar",        description="Semester dates, registration windows, and exam schedules", icon="Calendar"),
        TopicOut(key="solar",                    name="SOLAR & Registration",     description="Course registration, enrollment, and student records", icon="FileText"),
        TopicOut(key="brightspace",              name="Brightspace LMS",          description="Online course platform, assignments, and grades", icon="Monitor"),
        TopicOut(key="tuition_financial_aid",    name="Tuition & Financial Aid",  description="Tuition rates, fees, scholarships, grants, and loans", icon="DollarSign"),
        TopicOut(key="graduation",               name="Graduation",               description="Graduation requirements, application, and commencement", icon="Award"),
        # ── Faculty & departments ─────────────────────────────────────────
        TopicOut(key="faculty",                  name="Faculty Directory",        description="Professors, researchers, and department contacts across all SBU departments", icon="Users"),
        TopicOut(key="dept_computer_science",    name="Computer Science",         description="CS faculty, research, and graduate programs", icon="Code"),
        TopicOut(key="dept_mathematics",         name="Mathematics",              description="Math faculty, courses, and research", icon="Calculator"),
        TopicOut(key="dept_applied_math_stats",  name="Applied Math & Statistics","AMS faculty, programs, and research", icon="BarChart"),
        TopicOut(key="dept_physics_astronomy",   name="Physics & Astronomy",      description="Physics faculty and research areas", icon="Star"),
        TopicOut(key="dept_chemistry",           name="Chemistry",                description="Chemistry faculty and research", icon="Flask"),
        TopicOut(key="dept_biology",             name="Biology",                  description="Biology faculty and life sciences research", icon="Leaf"),
        TopicOut(key="dept_economics",           name="Economics",                description="Economics faculty and research", icon="TrendingUp"),
        TopicOut(key="dept_business",            name="Business",                 description="College of Business faculty and programs", icon="Briefcase"),
        TopicOut(key="dept_electrical_computer_engineering", name="Electrical & Computer Engineering", description="ECE faculty and research", icon="Zap"),
        TopicOut(key="dept_mechanical_engineering", name="Mechanical Engineering","ME faculty and research", icon="Settings"),
        TopicOut(key="dept_biomedical_engineering", name="Biomedical Engineering","BME faculty and research", icon="Activity"),
        # ── Campus life ───────────────────────────────────────────────────
        TopicOut(key="housing",                  name="Housing",                  description="Campus residences, applications, and room assignments", icon="Home"),
        TopicOut(key="dining",                   name="Dining",                   description="Meal plans, dining locations, and hours", icon="UtensilsCrossed"),
        TopicOut(key="clubs",                    name="Clubs & Organizations",    description="Student clubs, organizations, and campus activities", icon="Users"),
        TopicOut(key="campus_life",              name="Campus Life",              description="Student life, diversity resources, and campus services", icon="MapPin"),
        TopicOut(key="athletics_recreation",     name="Athletics & Recreation",   description="Sports, fitness facilities, and intramural activities", icon="Activity"),
        TopicOut(key="parking",                  name="Parking & Transit",        description="Parking permits, commuter buses, and transportation", icon="Car"),
        # ── Student services ──────────────────────────────────────────────
        TopicOut(key="career_center",            name="Career Center",            description="Internships, jobs, resume help, and career fairs", icon="Briefcase"),
        TopicOut(key="health_wellness",          name="Health & Wellness",        description="Student health, counseling, and mental health services", icon="Heart"),
        TopicOut(key="international_students",   name="International Students",   description="OISS, visa support, and international student resources", icon="Globe"),
        TopicOut(key="disability_support",       name="Disability Support",       description="DSS accommodations and accessibility services", icon="Shield"),
        TopicOut(key="academic_support",         name="Academic Support",         description="Writing center, tutoring, and academic success resources", icon="BookOpen"),
        TopicOut(key="research",                 name="Research",                 description="Undergraduate research, labs, and URECA program", icon="Search"),
        TopicOut(key="safety_emergency",         name="Safety & Emergency",       description="University police, campus safety, and emergency contacts", icon="AlertTriangle"),
        # ── IT & systems ──────────────────────────────────────────────────
        TopicOut(key="it_help",                  name="IT Help",                  description="NetID, WiFi, software, and technical support", icon="Monitor"),
        TopicOut(key="library",                  name="Library",                  description="Library resources, databases, and research help", icon="BookOpen"),
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
