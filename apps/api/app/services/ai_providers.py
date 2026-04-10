"""AI provider abstraction for embeddings and text generation."""
import abc
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
    """Mock LLM for local development - returns structured template responses."""

    async def generate(self, prompt: str, system: str = "", max_tokens: int = 1024) -> str:
        # Extract question and context from prompt
        question = ""
        context_lines = []
        in_context = False

        for line in prompt.split("\n"):
            stripped = line.strip()
            if stripped.lower().startswith("question:"):
                question = stripped.split(":", 1)[1].strip()
            elif stripped.startswith("[Source"):
                in_context = True
                context_lines.append(stripped)
            elif in_context and stripped:
                context_lines.append(stripped)

        if context_lines:
            # Return the first relevant chunk content as the answer
            content = " ".join(context_lines[:6])
            # Trim to a reasonable length
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
