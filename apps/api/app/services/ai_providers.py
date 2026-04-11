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


# ─── Local Providers (fastembed + Ollama) ────────────────────────────

class LocalEmbeddingProvider(EmbeddingProvider):
    """Local embeddings via fastembed — no API key required."""

    def __init__(self):
        from fastembed import TextEmbedding
        self.model = TextEmbedding(settings.local_embedding_model)

    def _embed_sync(self, texts: list[str]) -> list[list[float]]:
        return [emb.tolist() for emb in self.model.embed(texts)]

    async def embed(self, texts: list[str]) -> list[list[float]]:
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._embed_sync, texts)

    async def embed_query(self, text: str) -> list[float]:
        result = await self.embed([text])
        return result[0]


class OllamaLLMProvider(LLMProvider):
    """Local LLM via Ollama — no API key required."""

    def __init__(self):
        import httpx
        self.client = httpx.AsyncClient(base_url=settings.ollama_base_url, timeout=120.0)
        self.model = settings.ollama_model

    async def generate(self, prompt: str, system: str = "", max_tokens: int = 1024) -> str:
        import httpx
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        try:
            response = await self.client.post(
                "/api/chat",
                json={"model": self.model, "messages": messages, "stream": False,
                      "options": {"num_predict": max_tokens, "temperature": 0.1}},
            )
            response.raise_for_status()
            return response.json()["message"]["content"]
        except httpx.ConnectError:
            return (
                "Ollama is not running. Please install and start Ollama:\n"
                "  brew install ollama\n"
                "  ollama serve\n"
                f"  ollama pull {self.model}"
            )
        except Exception as e:
            return f"Ollama error: {str(e)}"


# ─── Bedrock Providers ───────────────────────────────────────────────

class BedrockEmbeddingProvider(EmbeddingProvider):
    """
    Amazon Titan Embed Text v2 — async-safe via run_in_executor.
    Outputs 1024-dimensional embeddings (matches DB schema after migration 006).
    """

    def __init__(self):
        import boto3
        session = boto3.Session(
            aws_access_key_id=settings.aws_access_key_id or None,
            aws_secret_access_key=settings.aws_secret_access_key or None,
            region_name=settings.aws_region,
        )
        self.client = session.client("bedrock-runtime")
        self.model_id = settings.bedrock_embedding_model_id

    def _embed_sync(self, texts: list[str]) -> list[list[float]]:
        import json
        results = []
        for text in texts:
            body = json.dumps({
                "inputText": text,
            })
            response = self.client.invoke_model(
                modelId=self.model_id,
                body=body,
                contentType="application/json",
                accept="application/json",
            )
            results.append(json.loads(response["body"].read())["embedding"])
        return results

    async def embed(self, texts: list[str]) -> list[list[float]]:
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._embed_sync, texts)

    async def embed_query(self, text: str) -> list[float]:
        result = await self.embed([text])
        return result[0]


class BedrockLLMProvider(LLMProvider):
    """
    Claude via Amazon Bedrock — async-safe via run_in_executor.
    Defaults to claude-3-5-haiku for fast, low-latency responses.
    """

    def __init__(self):
        import boto3
        session = boto3.Session(
            aws_access_key_id=settings.aws_access_key_id or None,
            aws_secret_access_key=settings.aws_secret_access_key or None,
            region_name=settings.aws_region,
        )
        self.client = session.client("bedrock-runtime")
        self.model_id = settings.bedrock_model_id

    def _generate_sync(self, prompt: str, system: str, max_tokens: int) -> str:
        import json
        body: dict = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "temperature": 0.1,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system:
            body["system"] = system
        response = self.client.invoke_model(
            modelId=self.model_id,
            body=json.dumps(body),
            contentType="application/json",
            accept="application/json",
        )
        result = json.loads(response["body"].read())
        return result["content"][0]["text"]

    async def generate(self, prompt: str, system: str = "", max_tokens: int = 1024) -> str:
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._generate_sync, prompt, system, max_tokens)


# ─── Factory ─────────────────────────────────────────────────────────

_embedding_provider: EmbeddingProvider | None = None
_llm_provider: LLMProvider | None = None


def get_embedding_provider() -> EmbeddingProvider:
    global _embedding_provider
    if _embedding_provider is None:
        if settings.ai_provider == "local":
            _embedding_provider = LocalEmbeddingProvider()
        elif settings.ai_provider == "openai":
            _embedding_provider = OpenAIEmbeddingProvider()
        elif settings.ai_provider == "bedrock":
            _embedding_provider = BedrockEmbeddingProvider()
        else:
            _embedding_provider = MockEmbeddingProvider()
    return _embedding_provider


def get_llm_provider() -> LLMProvider:
    global _llm_provider
    if _llm_provider is None:
        if settings.ai_provider == "local":
            _llm_provider = OllamaLLMProvider()
        elif settings.ai_provider == "openai":
            _llm_provider = OpenAILLMProvider()
        elif settings.ai_provider == "bedrock":
            _llm_provider = BedrockLLMProvider()
        else:
            _llm_provider = MockLLMProvider()
    return _llm_provider
