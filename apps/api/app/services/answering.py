"""
Answer generation service — response builders only.

Intent classification is handled by classifier.py.
This module handles:
  - Pre-defined canned responses for non-retrieval intents
  - Grounded RAG answer generation for public_school_info
  - public_no_reliable_source fallback when retrieval confidence is too low
"""

from app.services.ai_providers import get_llm_provider

# ─── Confidence threshold for reliable source fallback ───────────────
RELIABLE_SOURCE_THRESHOLD = 0.38

# ─── System prompt ────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are Ask Seawolves, the official AI assistant for Stony Brook University (SBU).

CORE RULES:
1. Answer ONLY from the [CONTEXT] block provided. Never use outside knowledge.
2. Never invent deadlines, fees, phone numbers, emails, or policy details.
3. Every substantive answer must include at least one source citation using the URL from the context: [Source: <title> — <url>]
4. If context is insufficient, say so clearly and suggest contacting the relevant office.
5. If information may vary by academic term or program, add a brief note to verify with the relevant office.
6. Be concise, accurate, and professional. Always respond in English.
7. For faculty or professor questions, include their title, department, research interests, and contact info if available in the context.
8. Do NOT add a follow-up prompt unless it naturally clarifies an ambiguous answer."""

ANSWER_PROMPT_TEMPLATE = """[CONTEXT]
{context}
[/CONTEXT]

Question: {question}

Answer based solely on the context above. Cite sources using the exact URLs provided in the context. If the context does not fully answer the question, acknowledge what is missing and suggest the appropriate office or resource."""

# ─── Canned responses ─────────────────────────────────────────────────

GREETING_RESPONSE = """Hi! I'm Ask Seawolves, your guide to official Stony Brook University information.

I can help with admissions, tuition, housing, financial aid, registration, dining, IT services, and more.

Here are some things you can ask me:
• "What is the tuition for in-state undergraduate students?"
• "When does spring 2026 registration open?"
• "How do I apply for on-campus housing?"
• "What dining plans are available for freshmen?"

What would you like to know?"""

NO_MEANING_RESPONSE = """No worries — whenever you're ready, feel free to ask anything about Stony Brook University.

Some popular questions:
• "What is the tuition for in-state undergrad students?"
• "How do I apply for on-campus housing?"
• "What financial aid options are available?"
• "Where can I get help with my NetID or SBU account?" """

OUT_OF_SCOPE_RESPONSE = """I can only help with official Stony Brook University information — that question is outside my scope.

If you have questions about SBU admissions, tuition, housing, financial aid, registration, dining, or other university services, I'm happy to help!"""

HUMAN_SUPPORT_RESPONSE = """I understand — for urgent matters or to speak with someone directly, please contact the **Dean of Students Office** (stonybrook.edu/dos) or call University Police at (631) 632-3333 for emergencies.

If you're going through a difficult time, **CAPS (Counseling and Psychological Services)** is available at stonybrook.edu/caps."""

NO_RELIABLE_SOURCE_RESPONSE = """I couldn't find reliable official SBU information for that question.

For accurate and up-to-date information, I recommend:
- Visiting **stonybrook.edu** directly
- Contacting the relevant university office

Would you like help finding the right office or resource?"""

PRIVATE_REFUSAL_TEMPLATE = """I don't have access to personal student account information — that's outside my current scope.

For **{topic}**, please use one of these resources:
{resources}

Is there anything about general university policies or services I can help with?"""

# ─── Private topic → resource map ────────────────────────────────────
# Keys are matched against lowercased query text (substring match).
# Order matters: more specific keys first.

PRIVATE_RESOURCE_MAP = [
    (["my gpa", "gpa last", "what was my gpa", "what's my gpa"],
     "your GPA",
     ["SOLAR — solar.stonybrook.edu"]),

    (["my grade", "my grades", "did i pass", "did i fail", "what grade", "grade from last", "grade this semester"],
     "your grades or academic records",
     ["SOLAR — solar.stonybrook.edu", "Registrar's Office — registrar.stonybrook.edu"]),

    (["my transcript", "check my transcript", "request my transcript"],
     "transcripts",
     ["Registrar's Office — registrar.stonybrook.edu"]),

    (["my schedule", "my classes", "my courses", "what classes am i", "what courses am i"],
     "your class schedule",
     ["SOLAR — solar.stonybrook.edu"]),

    (["am i enrolled", "am i registered", "my enrollment", "enrolled this term", "registered for"],
     "your enrollment status",
     ["SOLAR — solar.stonybrook.edu", "Registrar's Office"]),

    (["my bill", "my balance", "account balance", "my charges", "what i owe"],
     "your billing or tuition charges",
     ["SOLAR — solar.stonybrook.edu", "Bursar's Office — bursar.stonybrook.edu"]),

    (["my financial aid", "my aid", "my award", "did i get aid", "when does my aid", "my fafsa", "my refund"],
     "your financial aid status",
     ["SOLAR — solar.stonybrook.edu", "Student Financial Services — stonybrook.edu/sfs"]),

    (["my housing", "my room", "my roommate", "my housing assignment"],
     "your housing assignment",
     ["Residential Programs — housing.stonybrook.edu"]),

    (["my netid", "my password", "my account", "my login", "log in to my", "can't log in", "cannot log in", "reset my password"],
     "your NetID or account access",
     ["IT Help Desk — it.stonybrook.edu"]),

    (["my degree audit", "my graduation", "my holds", "my degree"],
     "your degree audit or graduation status",
     ["DegreeWorks via SOLAR"]),
]


# ─── Response builders ────────────────────────────────────────────────

def _build_private_refusal(question: str) -> str:
    q = question.lower()
    for keywords, topic_label, resources in PRIVATE_RESOURCE_MAP:
        if any(kw in q for kw in keywords):
            resource_list = "\n".join(f"• {r}" for r in resources)
            return PRIVATE_REFUSAL_TEMPLATE.format(topic=topic_label, resources=resource_list)
    # Generic fallback
    return PRIVATE_REFUSAL_TEMPLATE.format(
        topic="personal account information",
        resources="• SOLAR — solar.stonybrook.edu\n• Relevant university office",
    )


def _build_context(chunks: list[dict]) -> str:
    parts = []
    for i, chunk in enumerate(chunks):
        title = chunk.get("title", "SBU")
        url = chunk.get("url", "")
        source_info = f"[Source {i+1}: {title}"
        if url:
            source_info += f" — {url}"
        source_info += "]"
        if chunk.get("office"):
            source_info += f" (Office: {chunk['office']})"
        parts.append(f"{source_info}\n{chunk['content']}\n")
    return "\n".join(parts)


def build_prompt(question: str, chunks: list[dict]) -> str:
    """Public wrapper used by tests and external callers."""
    context = _build_context(chunks)
    return ANSWER_PROMPT_TEMPLATE.format(context=context, question=question)


# ─── Main entry point ─────────────────────────────────────────────────

async def generate_answer(
    question: str,
    chunks: list[dict],
    intent: str = "public_school_info",
) -> tuple[str, float]:
    """
    Generate a response based on pre-classified intent.
    Non-retrieval intents return immediately with canned responses.
    public_school_info runs the RAG pipeline; falls back if confidence too low.
    """

    if intent == "greeting":
        return GREETING_RESPONSE, 1.0

    if intent == "no_meaningful_query":
        return NO_MEANING_RESPONSE, 1.0

    if intent == "out_of_scope_non_sbu":
        return OUT_OF_SCOPE_RESPONSE, 1.0

    if intent == "private_account_specific":
        return _build_private_refusal(question), 1.0

    if intent == "human_support_needed":
        return HUMAN_SUPPORT_RESPONSE, 1.0

    # ── public_school_info: RAG pipeline ──────────────────────────────
    if not chunks:
        return NO_RELIABLE_SOURCE_RESPONSE, 0.0

    # Confidence check BEFORE calling LLM
    avg_distance = sum(c.get("distance", 1.0) for c in chunks) / len(chunks)
    confidence = max(0.0, min(1.0, 1.0 - avg_distance))

    if confidence < RELIABLE_SOURCE_THRESHOLD:
        return NO_RELIABLE_SOURCE_RESPONSE, confidence

    context = _build_context(chunks)
    prompt = ANSWER_PROMPT_TEMPLATE.format(context=context, question=question)
    llm = get_llm_provider()
    answer = await llm.generate(prompt, system=SYSTEM_PROMPT)

    return answer, confidence


def should_warn_term_dependent(chunks: list[dict], question: str) -> str | None:
    """Flag answers about deadlines, fees, or schedules as potentially term-dependent."""
    term_keywords = ["tuition", "deadline", "fee", "schedule", "calendar", "rate", "cost", "date"]
    if any(kw in question.lower() for kw in term_keywords):
        return "This information may vary by academic term or program. Please verify with the relevant office for the most current details."
    return None
