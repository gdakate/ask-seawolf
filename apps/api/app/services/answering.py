"""Answer generation service: prompt orchestration, grounding, response formatting."""
from app.services.ai_providers import get_llm_provider


SYSTEM_PROMPT = """You are Seawolf Ask, the AI assistant for Stony Brook University. You answer questions about Stony Brook University using ONLY the provided context from official university sources.

Rules:
1. Answer ONLY based on the provided context. Do not use outside knowledge.
2. If the context does not contain enough information, say so clearly and suggest contacting the relevant office.
3. Always mention the source of information when available.
4. Be specific about dates, deadlines, fees, and policies — but only if they appear in the context.
5. If information may vary by term or program, add a warning.
6. Be helpful, concise, and accurate. Use a friendly, professional tone.
7. Never fabricate deadlines, fees, policies, or contact information.
8. When multiple sources provide different information, prefer the most authoritative and recent source."""

ANSWER_PROMPT_TEMPLATE = """Context from official Stony Brook University sources:

{context}

---

Question: {question}

Provide a clear, helpful answer based solely on the context above. Include specific details when available. If the context doesn't fully answer the question, acknowledge what's missing and suggest next steps."""


def build_prompt(question: str, chunks: list[dict]) -> str:
    """Build the answer generation prompt from retrieved chunks."""
    context_parts = []
    for i, chunk in enumerate(chunks):
        source_info = f"[Source {i+1}: {chunk['title']}]"
        if chunk.get("office"):
            source_info += f" (Office: {chunk['office']})"
        context_parts.append(f"{source_info}\n{chunk['content']}\n")

    context = "\n".join(context_parts)
    return ANSWER_PROMPT_TEMPLATE.format(context=context, question=question)


async def generate_answer(question: str, chunks: list[dict]) -> tuple[str, float]:
    """Generate an answer using the LLM provider with retrieved context."""
    llm = get_llm_provider()

    if not chunks:
        return (
            "I don't have enough information from official Stony Brook University sources to answer "
            "this question confidently. I recommend contacting the relevant university office directly "
            "or visiting stonybrook.edu for the most current information.",
            0.0,
        )

    prompt = build_prompt(question, chunks)
    answer = await llm.generate(prompt, system=SYSTEM_PROMPT)

    # Simple confidence heuristic based on retrieval quality
    avg_distance = sum(c.get("distance", 1.0) for c in chunks) / len(chunks)
    confidence = max(0.0, min(1.0, 1.0 - avg_distance))

    return answer, confidence


def should_warn_term_dependent(chunks: list[dict], question: str) -> str | None:
    """Check if the answer might be term/program dependent."""
    term_keywords = ["tuition", "deadline", "fee", "schedule", "calendar", "rate", "cost"]
    q_lower = question.lower()
    if any(kw in q_lower for kw in term_keywords):
        return "This information may vary by academic term or program. Please verify with the relevant office for the most current details."
    return None
