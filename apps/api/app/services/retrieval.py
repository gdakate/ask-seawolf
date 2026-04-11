"""Retrieval service: vector search, hybrid retrieval, citation packaging."""
import uuid
import re
import json
import hashlib
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text, func
from app.models.models import Chunk, Document, Source, OfficeContact, FAQEntry
from app.services.ai_providers import get_embedding_provider
from app.schemas.schemas import Citation, OfficeRouting
from app.core.config import get_settings

_settings = get_settings()
_redis_client = None

async def _get_redis():
    global _redis_client
    if _redis_client is None:
        try:
            import redis.asyncio as aioredis
            _redis_client = aioredis.from_url(_settings.redis_url, decode_responses=True)
        except Exception:
            _redis_client = None
    return _redis_client


async def _get_cached_embedding(query: str) -> list[float] | None:
    r = await _get_redis()
    if r is None:
        return None
    key = "emb:" + hashlib.md5(query.lower().strip().encode()).hexdigest()
    try:
        cached = await r.get(key)
        if cached:
            return json.loads(cached)
    except Exception:
        pass
    return None


async def _cache_embedding(query: str, embedding: list[float]) -> None:
    r = await _get_redis()
    if r is None:
        return
    key = "emb:" + hashlib.md5(query.lower().strip().encode()).hexdigest()
    try:
        await r.set(key, json.dumps(embedding), ex=3600)  # 1-hour TTL
    except Exception:
        pass

# ── Category routing map ──────────────────────────────────────────────
# Maps keyword patterns (lowercase) to source name substrings for boosting.
CATEGORY_ROUTING = [
    # Faculty / departments
    (["professor", "faculty", "dr.", "phd", "researcher", "who teaches",
      "who is the", "department chair", "office hours of", "research interest"],
     ["Faculty", "Dept:"]),
    (["computer science", "cs department", "cse", "cs professor", "cs faculty"],
     ["Dept: Computer Science"]),
    (["math department", "math professor", "mathematics faculty"],
     ["Dept: Mathematics"]),
    (["physics", "astronomy", "physics professor"],
     ["Dept: Physics"]),
    (["chemistry professor", "chemistry department"],
     ["Dept: Chemistry"]),
    (["biology professor", "biology department"],
     ["Dept: Biology"]),
    (["economics professor", "economics department"],
     ["Dept: Economics"]),
    (["psychology professor", "psychology department"],
     ["Dept: Psychology"]),
    (["sociology professor", "sociology department"],
     ["Dept: Sociology"]),
    (["linguistics professor", "linguistics department"],
     ["Dept: Linguistics"]),
    (["english department", "english professor"],
     ["Dept: English"]),
    (["history department", "history professor"],
     ["Dept: History"]),
    (["applied math", "ams department", "statistics department"],
     ["Dept: Applied Math"]),
    (["electrical engineering", "ece department"],
     ["Dept: Electrical"]),
    (["mechanical engineering", "me department"],
     ["Dept: Mechanical"]),
    (["biomedical engineering", "bme department"],
     ["Dept: Biomedical"]),
    (["business school", "college of business", "business professor"],
     ["Dept: Business"]),
    # Academic / registration
    (["brightspace", "lms", "course management", "online course portal"],
     ["Brightspace"]),
    (["solar", "course registration", "enroll", "add/drop", "register for class"],
     ["SOLAR", "Registrar"]),
    (["tuition", "fees", "billing", "bursar", "payment plan"],
     ["Tuition", "Financial Aid"]),
    (["financial aid", "fafsa", "scholarship", "grant", "loan", "work study"],
     ["Financial Aid"]),
    (["housing", "residence hall", "dorm", "room assignment", "roommate"],
     ["Housing"]),
    (["dining", "meal plan", "cafeteria", "food", "dining hall"],
     ["Dining"]),
    (["library", "book", "journal", "database", "interlibrary"],
     ["Libraries"]),
    (["parking", "permit", "commuter", "bus", "shuttle", "transportation"],
     ["Parking"]),
    (["club", "organization", "student group", "sac", "activity"],
     ["Clubs"]),
    (["career", "internship", "job", "resume", "interview", "employer"],
     ["Career Center"]),
    (["graduate admission", "grad school", "masters", "phd program", "doctoral"],
     ["Graduate Admissions"]),
    (["undergraduate admission", "apply to sbu", "freshman", "transfer student"],
     ["Undergraduate Admissions"]),
    (["health", "medical", "counseling", "mental health", "caps", "wellness"],
     ["Health", "Wellness"]),
    (["international student", "visa", "oiss", "f-1", "i-20"],
     ["International Student"]),
    (["disability", "accommodation", "dss", "accessibility"],
     ["Disability Support"]),
    (["writing center", "tutoring", "academic support", "lisc"],
     ["Academic Support"]),
    (["police", "safety", "emergency", "title ix", "harassment", "crime"],
     ["Safety", "Emergency"]),
    (["research", "undergraduate research", "ureca", "grant", "lab"],
     ["Research"]),
    (["graduation", "commencement", "diploma", "degree audit", "degreeworks"],
     ["Graduation", "Commencement"]),
    (["calendar", "academic calendar", "semester dates", "holiday"],
     ["Academic Calendar"]),
    (["it help", "netid", "wifi", "vpn", "software", "computer help"],
     ["IT Help"]),
    (["about sbu", "about stony brook", "when was sbu founded", "sbu mascot",
      "seawolf", "wolfie", "sbu ranking", "sbu president", "where is sbu",
      "sbu location", "sbu history", "what is sbu", "tell me about sbu",
      "ask seawolves", "who are you", "what can you do"],
     ["About Stony Brook"]),
]


def _detect_category_hints(query: str) -> list[str]:
    """Return source name substrings to boost based on query keywords."""
    q = query.lower()
    for keywords, source_hints in CATEGORY_ROUTING:
        if any(kw in q for kw in keywords):
            return source_hints
    return []


async def retrieve_chunks(
    db: AsyncSession,
    query: str,
    top_k: int = 10,
    category_filter: str | None = None,
) -> list[dict]:
    """Hybrid retrieval: category-boosted vector search + keyword fallback + re-ranking."""
    provider = get_embedding_provider()
    # Check Redis cache before running CPU inference
    query_embedding = await _get_cached_embedding(query)
    if query_embedding is None:
        query_embedding = await provider.embed_query(query)
        await _cache_embedding(query, query_embedding)
    embedding_str = f"[{','.join(str(x) for x in query_embedding)}]"

    category_hints = _detect_category_hints(query)

    # ── Primary: global vector search (fetch 3× top_k for re-ranking) ─
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
        LIMIT :fetch_k
    """)
    result = await db.execute(sql, {"embedding": embedding_str, "fetch_k": top_k * 3})
    rows = result.fetchall()

    chunks = []
    for row in rows:
        # Combined score: 80% vector similarity + 20% authority
        similarity = max(0.0, 1.0 - float(row.distance))
        authority = float(row.authority_score or 0.5)
        combined_score = similarity * 0.8 + authority * 0.2

        # Boost chunks whose source matches detected category hints
        source_name = row.source_name or ""
        if category_hints and any(hint in source_name for hint in category_hints):
            combined_score = min(1.0, combined_score + 0.15)

        chunks.append({
            "chunk_id": str(row.id),
            "content": row.content,
            "heading": row.heading,
            "title": row.title,
            "url": row.source_url,
            "source_url": row.source_url,
            "source_name": source_name,
            "category": row.category,
            "office": row.office,
            "authority_score": authority,
            "distance": float(row.distance),
            "score": combined_score,
            "is_archived": row.is_archived,
        })

    # Re-rank by combined score and return top_k
    chunks.sort(key=lambda c: c["score"], reverse=True)
    chunks = chunks[:top_k]

    # ── Fallback to keyword search if nothing retrieved ────────────────
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
    """Check if query matches a curated FAQ entry. Tracks hit_count and last_used_at."""
    from datetime import datetime, timezone
    search = f"%{query.lower()[:80]}%"
    stmt = (
        select(FAQEntry)
        .where(FAQEntry.is_active == True, func.lower(FAQEntry.question).contains(search))
        .order_by(FAQEntry.priority.desc())
        .limit(1)
    )
    result = await db.execute(stmt)
    faq = result.scalar_one_or_none()
    if faq:
        faq.hit_count = (faq.hit_count or 0) + 1
        faq.last_used_at = datetime.now(timezone.utc)
    return faq


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


# ── Category → office fallback (when office_contacts table is empty) ──
CATEGORY_OFFICE_FALLBACK = {
    "faculty":                   ("Faculty Directory",         "https://www.stonybrook.edu/experts/"),
    "dept_computer_science":     ("CS Department",             "https://www.cs.stonybrook.edu/"),
    "dept_mathematics":          ("Math Department",           "https://www.math.stonybrook.edu/"),
    "dept_physics_astronomy":    ("Physics & Astronomy Dept",  "https://www.physics.stonybrook.edu/"),
    "dept_chemistry":            ("Chemistry Department",      "https://chemistry.stonybrook.edu/"),
    "dept_biology":              ("Biology Department",        "https://www.stonybrook.edu/commcms/biology/"),
    "dept_economics":            ("Economics Department",      "https://www.stonybrook.edu/commcms/economics/"),
    "dept_psychology":           ("Psychology Department",     "https://www.stonybrook.edu/commcms/psychology/"),
    "dept_sociology":            ("Sociology Department",      "https://www.stonybrook.edu/commcms/sociology/"),
    "dept_english":              ("English Department",        "https://www.stonybrook.edu/commcms/english/"),
    "dept_history":              ("History Department",        "https://www.stonybrook.edu/commcms/history/"),
    "dept_linguistics":          ("Linguistics Department",    "https://www.stonybrook.edu/commcms/linguistics/"),
    "dept_applied_math_stats":   ("AMS Department",           "https://www.stonybrook.edu/commcms/ams/"),
    "dept_electrical_computer_engineering": ("ECE Department","https://www.stonybrook.edu/commcms/ece/"),
    "dept_mechanical_engineering":("ME Department",            "https://www.stonybrook.edu/commcms/me/"),
    "dept_biomedical_engineering":("BME Department",           "https://www.stonybrook.edu/commcms/bme/"),
    "dept_business":             ("College of Business",       "https://www.stonybrook.edu/commcms/business/"),
    "brightspace":               ("Brightspace / IT Help",     "https://it.stonybrook.edu/services/brightspace"),
    "solar":                     ("SOLAR / Registrar",         "https://www.stonybrook.edu/commcms/registrar/"),
    "academic_calendar":         ("Office of the Registrar",   "https://www.stonybrook.edu/commcms/registrar/"),
    "tuition_financial_aid":     ("Bursar & Financial Aid",    "https://www.stonybrook.edu/bursar/"),
    "housing":                   ("Residential Programs",      "https://www.stonybrook.edu/commcms/studentaffairs/res/"),
    "dining":                    ("Dining Services",           "https://www.stonybrook.edu/commcms/dining/"),
    "library":                   ("University Libraries",      "https://library.stonybrook.edu/"),
    "parking":                   ("Parking & Transportation",  "https://www.stonybrook.edu/mobility-and-parking/"),
    "clubs":                     ("Student Activities Center", "https://www.stonybrook.edu/commcms/studentaffairs/sac/"),
    "career_center":             ("Career Center",             "https://www.stonybrook.edu/commcms/career-center/"),
    "graduate_admissions":       ("Graduate Admissions",       "https://www.stonybrook.edu/graduate/"),
    "undergraduate_admissions":  ("Undergraduate Admissions",  "https://www.stonybrook.edu/undergraduate-admissions/"),
    "health_wellness":           ("Student Health Services",   "https://www.stonybrook.edu/commcms/studentaffairs/health/"),
    "international_students":    ("OISS",                      "https://www.stonybrook.edu/commcms/oiss/"),
    "disability_support":        ("Disability Support Services","https://www.stonybrook.edu/commcms/dss/"),
    "academic_support":          ("Academic Support & Tutoring","https://www.stonybrook.edu/commcms/academic-success/"),
    "campus_life":               ("Student Affairs",           "https://www.stonybrook.edu/commcms/studentaffairs/"),
    "safety_emergency":          ("University Police",         "https://www.stonybrook.edu/commcms/police/"),
    "research":                  ("Office of Research",        "https://www.stonybrook.edu/research/"),
    "graduation":                ("Commencement Office",       "https://www.stonybrook.edu/commcms/commencement/"),
    "it_help":                   ("IT Help Desk",              "https://it.stonybrook.edu/"),
    "faq":                       ("Student Affairs",           "https://www.stonybrook.edu/commcms/studentaffairs/"),
}


async def find_office_routing(
    db: AsyncSession, query: str, chunks: list[dict]
) -> OfficeRouting | None:
    """Determine if the query should route to a specific office."""
    from collections import Counter

    # Try office_contacts table first
    offices = [c.get("office") for c in chunks if c.get("office")]
    if offices:
        most_common_office = Counter(offices).most_common(1)[0][0]
        stmt = select(OfficeContact).where(OfficeContact.office_key == most_common_office)
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

    # Fallback: derive routing from the dominant chunk category
    categories = [c.get("category", "") for c in chunks if c.get("category")]
    if not categories:
        return None

    dominant = Counter(categories).most_common(1)[0][0]
    # Also check source_name for dept-level routing
    source_names = [c.get("source_name", "") for c in chunks]
    for cat, (office_name, office_url) in CATEGORY_OFFICE_FALLBACK.items():
        if cat == dominant or any(cat.replace("_", " ") in sn.lower() for sn in source_names):
            return OfficeRouting(
                name=office_name,
                office_key=cat,
                phone=None,
                email=None,
                url=office_url,
                reason=f"This question relates to {office_name}",
            )

    return None


# ── Follow-up questions per category ──────────────────────────────────
CATEGORY_FOLLOW_UPS = {
    # Faculty
    "faculty":                   ["Who else is in this department?", "What research groups exist in this department?", "How do I contact this professor?"],
    "dept_computer_science":     ["Who are the CS faculty working on AI/ML?", "What graduate programs does CS offer?", "How do I apply to the CS PhD program?"],
    "dept_mathematics":          ["What math courses are required for the major?", "Who are the faculty in pure mathematics?", "Does Math offer a graduate program?"],
    "dept_applied_math_stats":   ["What is the difference between AMS and Math?", "Who are the AMS faculty?", "What graduate programs does AMS offer?"],
    "dept_economics":            ["What economics courses does SBU offer?", "Who are the economics faculty?", "Does SBU have a PhD in Economics?"],
    "dept_psychology":           ["What research labs exist in Psychology?", "Who leads the Psychology department?", "What graduate programs does Psychology offer?"],
    "dept_biology":              ["What biology research centers are at SBU?", "Who are the biology faculty?", "What undergraduate biology tracks are available?"],
    "dept_chemistry":            ["What research areas does Chemistry cover?", "Who are the chemistry professors?", "What graduate degrees does Chemistry offer?"],
    # Academics / admin
    "brightspace":               ["How do I access course materials on Brightspace?", "How do I submit assignments on Brightspace?", "Who do I contact for Brightspace technical issues?"],
    "solar":                     ["How do I register for courses on SOLAR?", "How do I check my enrollment status?", "How do I view my academic schedule?"],
    "academic_calendar":         ["When does the spring semester end?", "When is the last day to add/drop a course?", "When are final exams?"],
    "tuition_financial_aid":     ["What payment plans are available?", "When is the tuition due?", "What scholarships does SBU offer?"],
    "housing":                   ["How do I apply for on-campus housing?", "What are the different residence halls?", "When does the housing application open?"],
    "dining":                    ["What meal plans are available for freshmen?", "Where are the main dining halls located?", "Can I use meal swipes at all dining locations?"],
    "library":                   ["How do I access e-journals and databases?", "What are the library hours?", "How do I request an interlibrary loan?"],
    "parking":                   ["How do I get a student parking permit?", "Where can I park on campus?", "Are there commuter bus options?"],
    "clubs":                     ["How do I start a new student club?", "Where can I find the full list of clubs?", "How do I join a club at SBU?"],
    "career_center":             ["How do I schedule a resume review?", "When is the next career fair?", "Does the career center help with internship searches?"],
    "graduate_admissions":       ["What GRE scores do I need?", "What is the application deadline for graduate programs?", "Does SBU offer graduate assistantships?"],
    "undergraduate_admissions":  ["What is the average SAT score for admitted students?", "When is the application deadline?", "Does SBU offer merit scholarships?"],
    "health_wellness":           ["Where is the Student Health Center located?", "How do I make a counseling appointment?", "What mental health resources does SBU offer?"],
    "international_students":    ["How do I maintain my F-1 visa status?", "What is OPT and how do I apply?", "Does OISS help with cultural adjustment?"],
    "disability_support":        ["How do I register with DSS?", "How do I request exam accommodations?", "What services does DSS provide?"],
    "academic_support":          ["Where is the Writing Center located?", "Does SBU offer free tutoring?", "How do I make an appointment at the Writing Center?"],
    "campus_life":               ["What student services are available on campus?", "How do I get involved in campus life?", "What resources are available for LGBTQ+ students?"],
    "safety_emergency":          ["How do I contact SBU University Police?", "What is the campus emergency number?", "How do I report a safety concern?"],
    "research":                  ["How do I apply for URECA undergraduate research?", "What research centers exist at SBU?", "How do I find a faculty research mentor?"],
    "graduation":                ["How do I apply for graduation?", "When is the commencement ceremony?", "What are the graduation requirements?"],
    "it_help":                   ["How do I reset my NetID password?", "How do I connect to SBU WiFi?", "Where can I get free software as an SBU student?"],
}

DEFAULT_FOLLOW_UPS = [
    "What programs does Stony Brook University offer?",
    "How do I contact the relevant SBU office?",
    "Where can I find more information on stonybrook.edu?",
]


def generate_follow_ups(query: str, chunks: list[dict]) -> list[str]:
    """Generate contextual follow-up questions based on retrieved content categories."""
    from collections import Counter
    if not chunks:
        return DEFAULT_FOLLOW_UPS

    # Find the dominant category from retrieved chunks
    categories = [c.get("category", "") for c in chunks if c.get("category")]
    if not categories:
        return DEFAULT_FOLLOW_UPS

    dominant = Counter(categories).most_common(1)[0][0]
    follow_ups = CATEGORY_FOLLOW_UPS.get(dominant, [])

    # If the dominant category has no specific follow-ups, try source_name matching
    if not follow_ups:
        source_names = " ".join(c.get("source_name", "") for c in chunks).lower()
        for cat, questions in CATEGORY_FOLLOW_UPS.items():
            if cat.replace("_", " ") in source_names or cat in source_names:
                follow_ups = questions
                break

    return (follow_ups or DEFAULT_FOLLOW_UPS)[:3]
