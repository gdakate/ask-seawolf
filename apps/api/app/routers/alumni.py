"""Alumni platform API routes: auth, profile, matching, feed."""
import uuid
import math
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func, text
from pydantic import BaseModel, EmailStr

from app.core.database import get_db
from app.core.auth import hash_password, verify_password, create_access_token
from app.models.models import AlumniUser, AlumniProfile, AlumniPost, AlumniComment, AlumniLike
from app.services.ai_providers import get_embedding_provider
from app.core.config import get_settings

settings = get_settings()
router = APIRouter(prefix="/alumni")

SBU_DOMAINS = {"stonybrook.edu", "alumni.stonybrook.edu", "cs.stonybrook.edu"}

OPEN_TO_OPTIONS = [
    "coffee_chat",
    "mentoring",
    "referrals_career_advice",
    "research_project_collab",
    "community_general_chat",
    "events_networking",
]


# ─── Auth helpers ────────────────────────────────────────────────────

def _validate_sbu_email(email: str):
    domain = email.lower().split("@")[-1]
    if domain not in SBU_DOMAINS:
        raise HTTPException(status_code=400, detail="Must be an @stonybrook.edu or @alumni.stonybrook.edu email")


async def _get_current_alumni(token: str = Depends(lambda: None), db: AsyncSession = Depends(get_db)):
    """Dependency: decode JWT and return alumni user."""
    from fastapi import Header
    from app.core.auth import get_current_admin  # reuse JWT logic
    raise HTTPException(status_code=501, detail="Use auth header")


def _get_alumni_dep():
    from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
    from fastapi import Security
    import jwt as pyjwt
    bearer = HTTPBearer(auto_error=False)

    async def dep(
        credentials: HTTPAuthorizationCredentials = Security(bearer),
        db: AsyncSession = Depends(get_db),
    ) -> AlumniUser:
        if not credentials:
            raise HTTPException(status_code=401, detail="Not authenticated")
        try:
            payload = pyjwt.decode(
                credentials.credentials,
                settings.jwt_secret,
                algorithms=[settings.jwt_algorithm],
            )
            user_id = payload.get("sub")
            if not user_id:
                raise HTTPException(status_code=401, detail="Invalid token")
        except Exception:
            raise HTTPException(status_code=401, detail="Invalid token")

        result = await db.execute(select(AlumniUser).where(AlumniUser.id == uuid.UUID(user_id)))
        user = result.scalar_one_or_none()
        if not user or not user.is_active:
            raise HTTPException(status_code=401, detail="User not found")
        return user

    return dep


get_current_alumni = _get_alumni_dep()


# ─── Schemas (inline) ────────────────────────────────────────────────

class AlumniRegisterRequest(BaseModel):
    email: str
    password: str
    name: str


class AlumniLoginRequest(BaseModel):
    email: str
    password: str


class AlumniAuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    name: str
    email: str
    has_profile: bool


class ProfileCreateRequest(BaseModel):
    major: str
    degree: str  # bs/ba/ms/ma/phd/mba/other
    graduation_year: int
    is_international: bool = False
    current_company: Optional[str] = None
    job_title: Optional[str] = None
    industry: Optional[str] = None
    location: Optional[str] = None
    skills: list[str] = []
    interests: list[str] = []
    open_to: list[str] = []
    linkedin_url: Optional[str] = None
    bio: Optional[str] = None


class ProfileUpdateRequest(BaseModel):
    major: Optional[str] = None
    degree: Optional[str] = None
    graduation_year: Optional[int] = None
    is_international: Optional[bool] = None
    current_company: Optional[str] = None
    job_title: Optional[str] = None
    industry: Optional[str] = None
    location: Optional[str] = None
    skills: Optional[list[str]] = None
    interests: Optional[list[str]] = None
    open_to: Optional[list[str]] = None
    linkedin_url: Optional[str] = None
    bio: Optional[str] = None
    is_visible: Optional[bool] = None


class PostCreateRequest(BaseModel):
    content: str
    tags: list[str] = []


class CommentCreateRequest(BaseModel):
    content: str


def _profile_to_dict(profile: AlumniProfile, user: AlumniUser) -> dict:
    return {
        "id": str(profile.id),
        "user_id": str(profile.user_id),
        "name": user.name,
        "email": user.email,
        "major": profile.major,
        "degree": profile.degree,
        "graduation_year": profile.graduation_year,
        "is_international": profile.is_international,
        "current_company": profile.current_company,
        "job_title": profile.job_title,
        "industry": profile.industry,
        "location": profile.location,
        "skills": profile.skills or [],
        "interests": profile.interests or [],
        "open_to": profile.open_to or [],
        "linkedin_url": profile.linkedin_url,
        "bio": profile.bio,
        "is_visible": profile.is_visible,
        "created_at": profile.created_at.isoformat(),
    }


# ─── Embedding helpers ───────────────────────────────────────────────

def _build_profile_texts(profile: AlumniProfile, name: str) -> dict[str, str]:
    career = (
        f"{profile.degree.upper()} in {profile.major}. "
        f"Graduated {profile.graduation_year}. "
        + (f"Works as {profile.job_title} at {profile.current_company}. " if profile.job_title else "")
        + (f"Industry: {profile.industry}." if profile.industry else "")
    )
    skills = " ".join(profile.skills or [])
    interests = " ".join(profile.interests or [])
    return {"career": career, "skills": skills or "general", "interests": interests or "general"}


async def _embed_and_store(profile: AlumniProfile, user_name: str, db: AsyncSession):
    provider = get_embedding_provider()
    texts = _build_profile_texts(profile, user_name)
    career_vec, skills_vec, interests_vec = await provider.embed(
        [texts["career"], texts["skills"], texts["interests"]]
    )
    profile.profile_embedding = career_vec
    profile.skills_embedding = skills_vec
    profile.interests_embedding = interests_vec


# ─── Matching algorithm ──────────────────────────────────────────────

def _cosine(a: list[float], b: list[float]) -> float:
    if not a or not b:
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def _jaccard(a: list, b: list) -> float:
    sa, sb = set(s.lower() for s in a), set(s.lower() for s in b)
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


def _compute_match_score(src: AlumniProfile, tgt: AlumniProfile) -> tuple[float, list[str]]:
    """
    2-stage: embeddings (stage 1) + multi-signal rerank (stage 2).
    Returns (score 0-1, list of human-readable reasons).
    """
    # Stage 2: multi-signal features
    profile_sim  = _cosine(src.profile_embedding, tgt.profile_embedding)
    skills_sim   = _cosine(src.skills_embedding, tgt.skills_embedding)
    interests_sim = _cosine(src.interests_embedding, tgt.interests_embedding)

    skill_jaccard   = _jaccard(src.skills or [], tgt.skills or [])
    major_match     = 1.0 if src.major.lower() == tgt.major.lower() else 0.0
    industry_match  = 1.0 if (src.industry and tgt.industry and
                               src.industry.lower() == tgt.industry.lower()) else 0.0
    grad_diff       = abs(src.graduation_year - tgt.graduation_year)
    grad_proximity  = max(0.0, 1.0 - grad_diff / 10.0)
    open_to_compat  = _jaccard(src.open_to or [], tgt.open_to or [])

    score = (
        0.25 * profile_sim +
        0.20 * skills_sim +
        0.15 * interests_sim +
        0.20 * skill_jaccard +
        0.10 * major_match +
        0.05 * industry_match +
        0.03 * grad_proximity +
        0.02 * open_to_compat
    )

    # Build explainable reasons
    reasons = []
    if major_match:
        reasons.append(f"Same major: {tgt.major}")
    overlapping_skills = sorted(
        set(s.lower() for s in (src.skills or [])) & set(s.lower() for s in (tgt.skills or []))
    )
    if overlapping_skills:
        reasons.append(f"Overlapping skills: {', '.join(overlapping_skills[:4])}")
    if src.job_title and tgt.job_title:
        reasons.append(f"Similar career path: {src.job_title} → {tgt.job_title}")
    if industry_match:
        reasons.append(f"Same industry: {tgt.industry}")
    if grad_diff == 0:
        reasons.append("Same graduation year")
    elif grad_diff <= 2:
        reasons.append(f"Graduation proximity: {grad_diff} year{'s' if grad_diff > 1 else ''} apart")
    overlapping_interests = sorted(
        set(s.lower() for s in (src.interests or [])) & set(s.lower() for s in (tgt.interests or []))
    )
    if overlapping_interests and not reasons:
        reasons.append(f"Shared interests: {', '.join(overlapping_interests[:3])}")

    return min(score, 1.0), reasons


def _mmr_select(
    scored: list[tuple[float, AlumniProfile, list[str]]],
    k: int = 10,
    lambda_: float = 0.7,
) -> list[tuple[float, AlumniProfile, list[str]]]:
    """Maximal Marginal Relevance — pick diverse top-k."""
    if not scored:
        return []
    selected = []
    remaining = list(scored)

    while len(selected) < k and remaining:
        if not selected:
            best = max(remaining, key=lambda x: x[0])
        else:
            best_mmr, best_item = -1.0, None
            for item in remaining:
                relevance = item[0]
                max_sim = max(
                    _cosine(item[1].profile_embedding or [], s[1].profile_embedding or [])
                    for s in selected
                )
                mmr = lambda_ * relevance - (1 - lambda_) * max_sim
                if mmr > best_mmr:
                    best_mmr, best_item = mmr, item
            best = best_item

        selected.append(best)
        remaining.remove(best)

    return selected


# ─── Auth ─────────────────────────────────────────────────────────────

@router.post("/auth/register", response_model=AlumniAuthResponse, status_code=201)
async def alumni_register(req: AlumniRegisterRequest, db: AsyncSession = Depends(get_db)):
    _validate_sbu_email(req.email)
    existing = (await db.execute(select(AlumniUser).where(AlumniUser.email == req.email))).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")
    user = AlumniUser(email=req.email, password_hash=hash_password(req.password), name=req.name)
    db.add(user)
    await db.flush()
    token = create_access_token({"sub": str(user.id), "email": user.email, "type": "alumni"})
    return AlumniAuthResponse(access_token=token, user_id=str(user.id), name=user.name,
                               email=user.email, has_profile=False)


@router.post("/auth/login", response_model=AlumniAuthResponse)
async def alumni_login(req: AlumniLoginRequest, db: AsyncSession = Depends(get_db)):
    _validate_sbu_email(req.email)
    result = await db.execute(select(AlumniUser).where(AlumniUser.email == req.email, AlumniUser.is_active == True))
    user = result.scalar_one_or_none()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    user.last_login_at = datetime.now(timezone.utc)
    profile = (await db.execute(select(AlumniProfile).where(AlumniProfile.user_id == user.id))).scalar_one_or_none()
    token = create_access_token({"sub": str(user.id), "email": user.email, "type": "alumni"})
    return AlumniAuthResponse(access_token=token, user_id=str(user.id), name=user.name,
                               email=user.email, has_profile=profile is not None)


# ─── Profile ─────────────────────────────────────────────────────────

@router.post("/profile")
async def create_profile(
    req: ProfileCreateRequest,
    user: AlumniUser = Depends(get_current_alumni),
    db: AsyncSession = Depends(get_db),
):
    existing = (await db.execute(select(AlumniProfile).where(AlumniProfile.user_id == user.id))).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail="Profile already exists")

    profile = AlumniProfile(
        user_id=user.id, major=req.major, degree=req.degree,
        graduation_year=req.graduation_year, is_international=req.is_international,
        current_company=req.current_company, job_title=req.job_title, industry=req.industry,
        location=req.location, skills=req.skills, interests=req.interests, open_to=req.open_to,
        linkedin_url=req.linkedin_url, bio=req.bio,
    )
    db.add(profile)
    await db.flush()
    await _embed_and_store(profile, user.name, db)
    return _profile_to_dict(profile, user)


@router.get("/profile/me")
async def get_my_profile(user: AlumniUser = Depends(get_current_alumni), db: AsyncSession = Depends(get_db)):
    profile = (await db.execute(select(AlumniProfile).where(AlumniProfile.user_id == user.id))).scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return _profile_to_dict(profile, user)


@router.put("/profile/me")
async def update_profile(
    req: ProfileUpdateRequest,
    user: AlumniUser = Depends(get_current_alumni),
    db: AsyncSession = Depends(get_db),
):
    profile = (await db.execute(select(AlumniProfile).where(AlumniProfile.user_id == user.id))).scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    for field, value in req.model_dump(exclude_unset=True).items():
        setattr(profile, field, value)
    profile.updated_at = datetime.now(timezone.utc)
    await _embed_and_store(profile, user.name, db)
    return _profile_to_dict(profile, user)


@router.get("/profile/{profile_id}")
async def get_profile(profile_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    profile = (await db.execute(select(AlumniProfile).where(
        AlumniProfile.id == profile_id, AlumniProfile.is_visible == True
    ))).scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    user = (await db.execute(select(AlumniUser).where(AlumniUser.id == profile.user_id))).scalar_one()
    return _profile_to_dict(profile, user)


# ─── Matching ────────────────────────────────────────────────────────

@router.get("/matches")
async def get_matches(
    user: AlumniUser = Depends(get_current_alumni),
    db: AsyncSession = Depends(get_db),
):
    """2-stage alumni matching: ANN retrieval → multi-signal rerank → MMR diversity."""
    my_profile = (await db.execute(
        select(AlumniProfile).where(AlumniProfile.user_id == user.id)
    )).scalar_one_or_none()
    if not my_profile:
        raise HTTPException(status_code=404, detail="Complete your profile first")
    if not my_profile.profile_embedding:
        raise HTTPException(status_code=400, detail="Profile embeddings not ready")

    # ── Stage 1: ANN retrieval (top-50 candidates via pgvector) ──────
    embedding_str = f"[{','.join(str(x) for x in my_profile.profile_embedding)}]"
    sql = text("""
        SELECT ap.id
        FROM alumni_profiles ap
        WHERE ap.user_id != :user_id
          AND ap.is_visible = true
          AND ap.profile_embedding IS NOT NULL
        ORDER BY ap.profile_embedding <=> CAST(:embedding AS vector)
        LIMIT 50
    """)
    result = await db.execute(sql, {"user_id": str(user.id), "embedding": embedding_str})
    candidate_ids = [row[0] for row in result.fetchall()]

    if not candidate_ids:
        return []

    # Fetch full candidate profiles
    candidates_result = await db.execute(
        select(AlumniProfile, AlumniUser)
        .join(AlumniUser, AlumniProfile.user_id == AlumniUser.id)
        .where(AlumniProfile.id.in_(candidate_ids))
    )
    candidates = candidates_result.all()

    # ── Stage 2: Multi-signal reranking ──────────────────────────────
    scored = []
    for profile, cand_user in candidates:
        score, reasons = _compute_match_score(my_profile, profile)
        scored.append((score, profile, reasons, cand_user))

    scored.sort(key=lambda x: x[0], reverse=True)

    # ── Stage 3: MMR diversity ────────────────────────────────────────
    mmr_input = [(s, p, r) for s, p, r, _ in scored]
    diverse = _mmr_select(mmr_input, k=10)

    # Build response
    user_map = {p.id: u for _, p, _, u in scored}
    matches = []
    for score, profile, reasons in diverse:
        cand_user = user_map[profile.id]
        matches.append({
            "profile": _profile_to_dict(profile, cand_user),
            "match_score": round(score * 100),
            "match_pct": f"{round(score * 100)}%",
            "reasons": reasons,
        })

    return matches


# ─── Resume parsing ──────────────────────────────────────────────────

@router.post("/resume/parse")
async def parse_resume(
    file: UploadFile = File(...),
    user: AlumniUser = Depends(get_current_alumni),
):
    """Upload a PDF/text resume and extract profile fields via LLM."""
    from app.services.ai_providers import get_llm_provider

    if not file.filename or not file.filename.lower().endswith((".pdf", ".txt")):
        raise HTTPException(status_code=400, detail="Only PDF or TXT files supported")

    content = await file.read()

    # For PDF: extract text (simple approach — read raw bytes, extract ASCII)
    if file.filename.lower().endswith(".pdf"):
        try:
            import re
            raw = content.decode("latin-1", errors="ignore")
            # Extract readable text from PDF (basic — good enough for demo)
            text_chunks = re.findall(r'[A-Za-z0-9][A-Za-z0-9\s\.,\-\+\(\)@:;\'\"]{10,}', raw)
            resume_text = "\n".join(text_chunks[:200])[:3000]
        except Exception:
            resume_text = content.decode("utf-8", errors="ignore")[:3000]
    else:
        resume_text = content.decode("utf-8", errors="ignore")[:3000]

    prompt = f"""Extract profile information from this resume and return JSON only.

Resume:
{resume_text}

Return this exact JSON structure (use null for missing fields):
{{
  "major": "...",
  "degree": "bs|ba|ms|ma|phd|mba|other",
  "graduation_year": 2020,
  "current_company": "...",
  "job_title": "...",
  "industry": "...",
  "location": "...",
  "skills": ["skill1", "skill2"],
  "interests": ["interest1", "interest2"],
  "bio": "one sentence summary"
}}"""

    llm = get_llm_provider()
    try:
        raw_response = await llm.generate(prompt, [])
        import json, re
        json_match = re.search(r'\{.*\}', raw_response, re.DOTALL)
        if json_match:
            extracted = json.loads(json_match.group())
        else:
            extracted = {}
    except Exception:
        extracted = {}

    return {"extracted": extracted, "raw_text_preview": resume_text[:200]}


# ─── Feed ────────────────────────────────────────────────────────────

@router.get("/feed")
async def get_feed(page: int = 1, db: AsyncSession = Depends(get_db)):
    page_size = 20
    stmt = (
        select(AlumniPost, AlumniProfile, AlumniUser)
        .join(AlumniProfile, AlumniPost.author_id == AlumniProfile.id)
        .join(AlumniUser, AlumniProfile.user_id == AlumniUser.id)
        .where(AlumniPost.is_pinned == False)
        .order_by(desc(AlumniPost.created_at))
        .offset((page - 1) * page_size).limit(page_size)
    )
    result = await db.execute(stmt)

    # Pinned posts first
    pinned_result = await db.execute(
        select(AlumniPost, AlumniProfile, AlumniUser)
        .join(AlumniProfile, AlumniPost.author_id == AlumniProfile.id)
        .join(AlumniUser, AlumniProfile.user_id == AlumniUser.id)
        .where(AlumniPost.is_pinned == True)
        .order_by(desc(AlumniPost.created_at))
    )

    def _post_to_dict(post, profile, user):
        return {
            "id": str(post.id),
            "content": post.content,
            "tags": post.tags or [],
            "likes_count": post.likes_count,
            "comments_count": post.comments_count,
            "is_pinned": post.is_pinned,
            "created_at": post.created_at.isoformat(),
            "author": {
                "id": str(profile.id),
                "name": user.name,
                "job_title": profile.job_title,
                "current_company": profile.current_company,
                "major": profile.major,
                "graduation_year": profile.graduation_year,
            },
        }

    posts = [_post_to_dict(p, pr, u) for p, pr, u in pinned_result.all()]
    posts += [_post_to_dict(p, pr, u) for p, pr, u in result.all()]
    return posts


@router.post("/feed")
async def create_post(
    req: PostCreateRequest,
    user: AlumniUser = Depends(get_current_alumni),
    db: AsyncSession = Depends(get_db),
):
    profile = (await db.execute(select(AlumniProfile).where(AlumniProfile.user_id == user.id))).scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=400, detail="Complete your profile first")

    post = AlumniPost(author_id=profile.id, content=req.content, tags=req.tags)
    db.add(post)
    await db.flush()
    return {"id": str(post.id), "content": post.content, "tags": post.tags, "created_at": post.created_at.isoformat()}


@router.delete("/feed/{post_id}")
async def delete_post(
    post_id: uuid.UUID,
    user: AlumniUser = Depends(get_current_alumni),
    db: AsyncSession = Depends(get_db),
):
    profile = (await db.execute(select(AlumniProfile).where(AlumniProfile.user_id == user.id))).scalar_one_or_none()
    post = (await db.execute(select(AlumniPost).where(AlumniPost.id == post_id))).scalar_one_or_none()
    if not post or not profile or post.author_id != profile.id:
        raise HTTPException(status_code=404, detail="Post not found")
    await db.delete(post)
    return {"status": "deleted"}


@router.get("/feed/{post_id}/comments")
async def get_comments(post_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(AlumniComment, AlumniProfile, AlumniUser)
        .join(AlumniProfile, AlumniComment.author_id == AlumniProfile.id)
        .join(AlumniUser, AlumniProfile.user_id == AlumniUser.id)
        .where(AlumniComment.post_id == post_id)
        .order_by(AlumniComment.created_at)
    )
    return [
        {"id": str(c.id), "content": c.content, "created_at": c.created_at.isoformat(),
         "author": {"name": u.name, "job_title": p.job_title, "id": str(p.id)}}
        for c, p, u in result.all()
    ]


@router.post("/feed/{post_id}/comments")
async def add_comment(
    post_id: uuid.UUID,
    req: CommentCreateRequest,
    user: AlumniUser = Depends(get_current_alumni),
    db: AsyncSession = Depends(get_db),
):
    profile = (await db.execute(select(AlumniProfile).where(AlumniProfile.user_id == user.id))).scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=400, detail="Complete your profile first")
    post = (await db.execute(select(AlumniPost).where(AlumniPost.id == post_id))).scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    comment = AlumniComment(post_id=post_id, author_id=profile.id, content=req.content)
    db.add(comment)
    post.comments_count = (post.comments_count or 0) + 1
    await db.flush()
    return {"id": str(comment.id), "content": comment.content, "created_at": comment.created_at.isoformat()}


@router.post("/feed/{post_id}/like")
async def toggle_like(
    post_id: uuid.UUID,
    user: AlumniUser = Depends(get_current_alumni),
    db: AsyncSession = Depends(get_db),
):
    post = (await db.execute(select(AlumniPost).where(AlumniPost.id == post_id))).scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    existing = (await db.execute(
        select(AlumniLike).where(AlumniLike.post_id == post_id, AlumniLike.user_id == user.id)
    )).scalar_one_or_none()
    if existing:
        await db.delete(existing)
        post.likes_count = max(0, (post.likes_count or 0) - 1)
        return {"liked": False, "likes_count": post.likes_count}
    else:
        db.add(AlumniLike(post_id=post_id, user_id=user.id))
        post.likes_count = (post.likes_count or 0) + 1
        return {"liked": True, "likes_count": post.likes_count}
