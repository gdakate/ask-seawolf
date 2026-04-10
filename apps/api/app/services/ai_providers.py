"""AI provider abstraction for embeddings and text generation."""
import abc
import re
import numpy as np
import hashlib
from app.core.config import get_settings

settings = get_settings()


class EmbeddingProvider(abc.ABC):
    @abc.abstractmethod
    async def embed(self, texts: list[str]) -> list[list[float]]:
        ...

    @abc.abstractmethod
    async def embed_query(self, text: str) -> list[float]:
        ...


class LLMProvider(abc.ABC):
    @abc.abstractmethod
    async def generate(self, prompt: str, system: str = "", max_tokens: int = 1024) -> str:
        ...


# ─── Mock Providers ──────────────────────────────────────────────────

class MockEmbeddingProvider(EmbeddingProvider):
    """Deterministic mock embeddings for local development."""

    def _deterministic_embedding(self, text: str) -> list[float]:
        seed = int(hashlib.md5(text.encode()).hexdigest()[:8], 16) % (2**31)
        rng = np.random.RandomState(seed)
        vec = rng.randn(settings.embedding_dimensions).astype(float)
        vec = vec / np.linalg.norm(vec)
        return vec.tolist()

    async def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._deterministic_embedding(t) for t in texts]

    async def embed_query(self, text: str) -> list[float]:
        return self._deterministic_embedding(text)


class MockLLMProvider(LLMProvider):
    """Mock LLM for local development — handles both classifier and answer generation."""

    _PRIVATE_KEYWORDS = [
        "my grade", "my grades", "my gpa", "did i pass", "did i fail",
        "what grade did i", "grade from last", "gpa last", "what was my gpa",
        "my schedule", "my class", "my courses", "what classes am i",
        "my bill", "my balance", "account balance", "what i owe",
        "my financial aid", "my aid", "my award", "did i get aid", "when does my aid",
        "my housing", "my room", "my roommate",
        "my netid", "my password", "my account", "my login",
        "am i registered", "am i enrolled", "enrolled this term",
        "my enrollment", "my refund", "my transcript", "check my transcript",
        "can you check my", "my degree audit", "my holds",
    ]
    _AMBIGUOUS_TRIGGERS = {
        "tell me about registration": "Are you asking about course registration for a specific term (e.g., Fall 2026), or about registering as a new student?",
        "what are the fees": "Are you asking about tuition fees, housing fees, dining fees, or another charge?",
        "how do i apply": "Are you asking about undergraduate admissions, graduate admissions, or a specific program?",
        "what's the deadline": "Which deadline — admissions, financial aid, housing, or course add/drop?",
        "what is the deadline": "Which deadline — admissions, financial aid, housing, or course add/drop?",
        "tell me about housing": "Are you asking about on-campus housing options, the application process, or costs?",
        "tell me about financial aid": "Are you asking about types of aid, eligibility, deadlines, or the application process?",
    }
    _OUT_OF_SCOPE_KEYWORDS = [
        "weather", "temperature", "forecast",
        "harvard", "mit", "yale", "stanford", "columbia", "cornell", "princeton",
        "nyu", "other university", "other school", "different university",
        "what is 2", "solve this", "calculate", "math problem",
        "recipe", "how to cook", "stock price", "bitcoin",
        "who is the president", "news today", "sports score",
    ]

    async def generate(self, prompt: str, system: str = "", max_tokens: int = 1024) -> str:
        import json as _json

        # ── Classification request ────────────────────────────────────
        if system and "intent classifier" in system.lower():
            q_matches = re.findall(r'Q:\s*"(.+?)"', prompt)
            q = q_matches[-1].lower() if q_matches else prompt.lower()

            # Out of scope
            if any(kw in q for kw in self._OUT_OF_SCOPE_KEYWORDS):
                return _json.dumps({
                    "intent": "out_of_scope_non_sbu",
                    "confidence": 0.97,
                    "reasoning": "Query is unrelated to Stony Brook University.",
                    "clarification_question": None,
                })

            # Private
            for kw in self._PRIVATE_KEYWORDS:
                if kw in q:
                    return _json.dumps({
                        "intent": "private_account_specific",
                        "confidence": 0.97,
                        "reasoning": f"Query contains '{kw}', indicating personal account data.",
                        "clarification_question": None,
                    })

            # Ambiguous
            for trigger, cq in self._AMBIGUOUS_TRIGGERS.items():
                if trigger in q and len(q.split()) <= 8:
                    return _json.dumps({
                        "intent": "ambiguous_public",
                        "confidence": 0.88,
                        "reasoning": "Query is too vague to answer without clarification.",
                        "clarification_question": cq,
                    })

            # Human support
            human_kws = ["need to talk", "speak to someone", "complaint", "urgent", "overwhelmed"]
            if any(kw in q for kw in human_kws):
                return _json.dumps({
                    "intent": "human_support_needed",
                    "confidence": 0.93,
                    "reasoning": "User wants to speak with a person.",
                    "clarification_question": None,
                })

            # Default: public school info
            return _json.dumps({
                "intent": "public_school_info",
                "confidence": 0.85,
                "reasoning": "Appears to be a question about public SBU information.",
                "clarification_question": None,
            })

        # ── Answer generation (has [CONTEXT] block) ──
        context_lines = []
        in_context = False
        for line in prompt.split("\n"):
            stripped = line.strip()
            if stripped.startswith("[Source"):
                in_context = True
                context_lines.append(stripped)
            elif in_context and stripped and not stripped.startswith("[/CONTEXT]"):
                context_lines.append(stripped)
            elif stripped.startswith("[/CONTEXT]"):
                in_context = False

        if context_lines:
            content = " ".join(context_lines[:6])
            if len(content) > 600:
                content = content[:600].rsplit(" ", 1)[0] + "..."
            return content

        return (
            "I don't have enough information from official Stony Brook University sources to answer "
            "this question. Please contact the relevant university office or visit stonybrook.edu."
        )


# ─── OpenAI Provider ────────────────────────────────────────────────

class OpenAIEmbeddingProvider(EmbeddingProvider):
    def __init__(self):
        import openai
        self.client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_embedding_model

    async def embed(self, texts: list[str]) -> list[list[float]]:
        response = await self.client.embeddings.create(input=texts, model=self.model)
        return [item.embedding for item in response.data]

    async def embed_query(self, text: str) -> list[float]:
        result = await self.embed([text])
        return result[0]


class OpenAILLMProvider(LLMProvider):
    def __init__(self):
        import openai
        self.client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model

    async def generate(self, prompt: str, system: str = "", max_tokens: int = 1024) -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        response = await self.client.chat.completions.create(
            model=self.model, messages=messages, max_tokens=max_tokens, temperature=0.1
        )
        return response.choices[0].message.content or ""


# ─── Bedrock Provider (stub, ready for integration) ─────────────────

class BedrockEmbeddingProvider(EmbeddingProvider):
    def __init__(self):
        import boto3
        self.client = boto3.client("bedrock-runtime", region_name=settings.aws_region)
        self.model_id = settings.bedrock_embedding_model_id

    async def embed(self, texts: list[str]) -> list[list[float]]:
        import json
        results = []
        for text in texts:
            response = self.client.invoke_model(
                modelId=self.model_id,
                body=json.dumps({"inputText": text}),
                contentType="application/json",
            )
            body = json.loads(response["body"].read())
            results.append(body["embedding"])
        return results

    async def embed_query(self, text: str) -> list[float]:
        result = await self.embed([text])
        return result[0]


class BedrockLLMProvider(LLMProvider):
    def __init__(self):
        import boto3
        self.client = boto3.client("bedrock-runtime", region_name=settings.aws_region)
        self.model_id = settings.bedrock_model_id

    async def generate(self, prompt: str, system: str = "", max_tokens: int = 1024) -> str:
        import json
        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system:
            body["system"] = system
        response = self.client.invoke_model(
            modelId=self.model_id, body=json.dumps(body), contentType="application/json"
        )
        result = json.loads(response["body"].read())
        return result["content"][0]["text"]


# ─── Factory ─────────────────────────────────────────────────────────

def get_embedding_provider() -> EmbeddingProvider:
    if settings.ai_provider == "openai":
        return OpenAIEmbeddingProvider()
    elif settings.ai_provider == "bedrock":
        return BedrockEmbeddingProvider()
    return MockEmbeddingProvider()


def get_llm_provider() -> LLMProvider:
    if settings.ai_provider == "openai":
        return OpenAILLMProvider()
    elif settings.ai_provider == "bedrock":
        return BedrockLLMProvider()
    return MockLLMProvider()
