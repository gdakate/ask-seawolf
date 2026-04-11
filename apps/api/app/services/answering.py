"""
Answer generation service — response builders only.

Intent classification is handled by classifier.py.
This module handles:
  - Pre-defined canned responses for non-retrieval intents
  - Grounded RAG answer generation for public_school_info
  - public_no_reliable_source fallback when retrieval confidence is too low
"""

import random
from app.services.ai_providers import get_llm_provider

# ─── Confidence threshold for reliable source fallback ───────────────
RELIABLE_SOURCE_THRESHOLD = 0.38

# ─── System prompt ────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are Ask Seawolves, the official AI assistant for Stony Brook University (SBU).

VERIFIED SBU FACTS (use these to avoid hallucination — do NOT contradict them):
- Full name: State University of New York at Stony Brook (Stony Brook University / SBU)
- Founded: 1957; current location since 1962; main campus: Stony Brook, NY (Long Island)
- Campus size: 1,454 acres; ~60 miles east of Midtown Manhattan; LIRR Stony Brook station on campus
- Enrollment: approximately 27,252 students (2024)
- Endowment: $724.4 million (2025)
- Current President: Andrea Goldsmith (took office August 1, 2025) — first woman president of SBU
- Previous President: Maurie McInnis (2020–2025)
- System: SUNY (State University of New York) — one of four SUNY university centers
- Classification: R1 doctoral university (very high research activity); AAU member
- US News Rankings (2024–25): 58th national university, 26th public university
- Notable gift: $500 million from Simons Foundation (2023) — largest ever donation to a public university in the US
- Hospital: Stony Brook University Hospital — 624-bed Level I Trauma Center; only tertiary care in Suffolk County
- BNL: Co-manages Brookhaven National Laboratory with Battelle for the U.S. Dept of Energy
- Mascot: Wolfie the Seawolf; Colors: red, seawolf grey, white; Athletics: NCAA Division I, Coastal Athletic Association (CAA) / America East Conference
- Nobel laureates affiliated: C.N. Yang (Physics 1957), Paul Lauterbur (Medicine 2003, MRI inventor)
- Main phone: (631) 632-6000; Police (non-emergency): (631) 632-3333; Website: stonybrook.edu

CORE RULES:
1. Answer ONLY from the [CONTEXT] block provided. For general SBU facts (above), you may confirm them if context is silent — but never invent new facts not listed above or in context.
2. Never invent deadlines, fees, phone numbers, emails, or policy details not present in context.
3. Every substantive answer must include at least one source citation using the URL from the context: [Source: <title> — <url>]
4. If context is insufficient, say so clearly and suggest contacting the relevant office.
5. If information may vary by academic term or program, add a brief note to verify with the relevant office.
6. Be concise, accurate, and professional. Always respond in English.
7. For faculty or professor questions, include their title, department, research interests, and contact info if available in the context.
8. Do NOT add a follow-up prompt unless it naturally clarifies an ambiguous answer.
9. NEVER state the current president is Maurie McInnis — the current president is Andrea Goldsmith (since August 1, 2025)."""

ANSWER_PROMPT_TEMPLATE = """[CONTEXT]
{context}
[/CONTEXT]

Question: {question}

Answer based solely on the context above. Cite sources using the exact URLs provided in the context. If the context does not fully answer the question, acknowledge what is missing and suggest the appropriate office or resource."""

# ─── Canned responses ─────────────────────────────────────────────────

GREETING_RESPONSES = [
    """Hi! I'm Ask Seawolves, your AI guide to Stony Brook University. 🐺

I can help you find information about:
• **Admissions** — requirements, deadlines, how to apply
• **Tuition & Financial Aid** — costs, scholarships, FAFSA
• **Housing & Dining** — residence halls, meal plans
• **Registration** — SOLAR, Brightspace, academic calendar
• **Faculty & Departments** — professors, research, contact info
• **Campus Life** — clubs, career center, health services, and more

What would you like to know?""",

    """Hello! Welcome to Ask Seawolves — your 24/7 guide to official SBU information.

Whether you're a prospective student, current Seawolf, or just curious about SBU, I'm here to help. Try asking me:
• "Who are the CS faculty working on AI?"
• "What are the graduate admissions requirements?"
• "How do I use Brightspace?"
• "What dining plans are available?"

What's on your mind?""",

    """Hey there! I'm Ask Seawolves, Stony Brook University's AI assistant.

I have information on **faculty, admissions, tuition, housing, dining, registration, campus services, research, and much more** — all sourced directly from official SBU pages.

Go ahead and ask me anything about SBU!""",

    """Hi and welcome! I'm Ask Seawolves, here to help you navigate Stony Brook University.

Some popular topics:
• Faculty & department contacts
• Tuition, fees, and financial aid
• Course registration and Brightspace
• On-campus housing and dining
• Career center, clubs, and student life

What can I help you with today?""",
]

THANKS_RESPONSES = [
    "You're welcome! Feel free to ask if you have any other questions about SBU.",
    "Happy to help! Is there anything else you'd like to know about Stony Brook?",
    "Glad I could help! Don't hesitate to ask if you need more SBU information.",
    "Of course! Let me know if there's anything else I can look up for you.",
]

FAREWELL_RESPONSES = [
    "Take care! Come back anytime you have questions about SBU. Go Seawolves! 🐺",
    "Goodbye! Best of luck with your studies. Feel free to return whenever you need help.",
    "See you later! Don't forget — I'm available 24/7 for any SBU questions.",
    "Take care! Wishing you a great semester at Stony Brook.",
]

NO_MEANING_RESPONSES = [
    """No worries — take your time! Whenever you're ready, feel free to ask anything about Stony Brook University.

Some popular questions:
• "What is the tuition for in-state undergrad students?"
• "How do I apply for on-campus housing?"
• "Who are the Computer Science professors?"
• "Where can I get help with my NetID?" """,

    """No problem! I'm here whenever you need me.

You can ask me about admissions, tuition, faculty, housing, financial aid, clubs, career services, Brightspace, SOLAR, and much more. What would you like to know?""",
]

OUT_OF_SCOPE_RESPONSES = [
    """That's a bit outside what I cover — I'm specialized in official Stony Brook University information.

I can help with SBU admissions, tuition, housing, financial aid, faculty, registration, dining, IT, and more. Is there anything SBU-related I can help with?""",

    """I'm best suited for questions about Stony Brook University specifically. That topic falls outside my scope.

Feel free to ask me about SBU programs, services, faculty, campus life, or anything else related to the university!""",
]

HUMAN_SUPPORT_RESPONSE = """I understand — for urgent matters or to speak with someone directly:

• **Dean of Students Office**: stonybrook.edu/dos
• **University Police** (non-emergency): (631) 632-3333
• **Emergency**: 911

If you're going through a difficult time, **CAPS (Counseling and Psychological Services)** is available at stonybrook.edu/caps — you don't have to go through this alone."""

NO_RELIABLE_SOURCE_RESPONSE = """I couldn't find reliable official SBU information for that question in my sources.

For accurate and up-to-date information:
- Visit **stonybrook.edu** directly
- Contact the relevant university office

Would you like help finding the right office or resource?"""


def _pick(responses: list[str]) -> str:
    """Pick a response at random for variety."""
    return random.choice(responses)


def _is_thanks(query: str) -> bool:
    q = query.lower().strip()
    return any(kw in q for kw in ["thank", "thanks", "thx", "ty", "appreciate", "helpful", "that helped", "great answer", "perfect"])


def _is_farewell(query: str) -> bool:
    q = query.lower().strip()
    return any(kw in q for kw in ["bye", "goodbye", "see ya", "take care", "later", "cya", "good night", "goodnight"])

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


def _build_history_block(history: list[dict]) -> str:
    lines = []
    for turn in history:
        role = "User" if turn["role"] == "user" else "Assistant"
        lines.append(f"{role}: {turn['content']}")
    return "\n".join(lines)


def build_prompt(question: str, chunks: list[dict], history: list[dict] | None = None) -> str:
    """Public wrapper used by tests and external callers."""
    context = _build_context(chunks)
    prompt = ANSWER_PROMPT_TEMPLATE.format(context=context, question=question)
    if history:
        history_block = _build_history_block(history)
        prompt = (
            f"[CONVERSATION HISTORY]\n{history_block}\n[/CONVERSATION HISTORY]\n\n"
            + prompt
        )
    return prompt


# ─── Main entry point ─────────────────────────────────────────────────

async def generate_answer(
    question: str,
    chunks: list[dict],
    intent: str = "public_school_info",
    history: list[dict] | None = None,
) -> tuple[str, float]:
    """
    Generate a response based on pre-classified intent.
    Non-retrieval intents return immediately with canned responses.
    public_school_info runs the RAG pipeline; falls back if confidence too low.
    """

    if intent == "greeting":
        # Distinguish thanks and farewells from hellos
        if _is_thanks(question):
            return _pick(THANKS_RESPONSES), 1.0
        if _is_farewell(question):
            return _pick(FAREWELL_RESPONSES), 1.0
        return _pick(GREETING_RESPONSES), 1.0

    if intent == "no_meaningful_query":
        return _pick(NO_MEANING_RESPONSES), 1.0

    if intent == "out_of_scope_non_sbu":
        return _pick(OUT_OF_SCOPE_RESPONSES), 1.0

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
    if history:
        history_block = _build_history_block(history)
        prompt = (
            f"[CONVERSATION HISTORY]\n{history_block}\n[/CONVERSATION HISTORY]\n\n"
            + prompt
        )
    llm = get_llm_provider()
    answer = await llm.generate(prompt, system=SYSTEM_PROMPT)

    return answer, confidence


def should_warn_term_dependent(chunks: list[dict], question: str) -> str | None:
    """Flag answers about deadlines, fees, or schedules as potentially term-dependent."""
    term_keywords = ["tuition", "deadline", "fee", "schedule", "calendar", "rate", "cost", "date"]
    if any(kw in question.lower() for kw in term_keywords):
        return "This information may vary by academic term or program. Please verify with the relevant office for the most current details."
    return None
