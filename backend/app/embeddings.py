import hashlib
import math
from typing import Protocol

from backend.app.config import get_settings
from backend.app.retrieval_text import tokenize


class EmbeddingModel(Protocol):
    def embed(self, text: str) -> tuple[float, ...]:
        """Return a deterministic vector representation for text."""


class HashEmbeddingModel:
    """Small local embedding model used for MVP tests and demos.

    This is not semantically equivalent to a production embedding model. It gives
    us the same engineering contract: text goes in, a fixed-size vector comes
    out, and retrieval can rank chunks by cosine similarity. Production can swap
    this for OpenAI, Bedrock, or another embedding provider.
    """

    def __init__(self, dimensions: int = 64) -> None:
        self.dimensions = dimensions

    def embed(self, text: str) -> tuple[float, ...]:
        vector = [0.0] * self.dimensions
        for token in tokenize(text):
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:2], "big") % self.dimensions
            sign = 1.0 if digest[2] % 2 == 0 else -1.0
            vector[index] += sign
        return normalize(vector)


class OpenAIEmbeddingModel:
    """Production embedding client for OpenAI text embeddings."""

    def __init__(
        self,
        model: str | None = None,
        dimensions: int | None = None,
        api_key: str | None = None,
    ) -> None:
        settings = get_settings()
        self.model = model or settings.embedding_model
        self.dimensions = dimensions or settings.embedding_dimensions
        self.api_key = api_key or settings.openai_api_key

    def embed(self, text: str) -> tuple[float, ...]:
        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY is required for OpenAI embeddings")

        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError("Install the openai package to use OpenAI embeddings") from exc

        client = OpenAI(api_key=self.api_key)
        response = client.embeddings.create(
            model=self.model,
            input=text.replace("\n", " "),
            dimensions=self.dimensions,
            encoding_format="float",
        )
        return tuple(float(value) for value in response.data[0].embedding)


def normalize(vector: list[float]) -> tuple[float, ...]:
    magnitude = math.sqrt(sum(value * value for value in vector))
    if magnitude == 0:
        return tuple(vector)
    return tuple(value / magnitude for value in vector)


def cosine_similarity(left: tuple[float, ...], right: tuple[float, ...]) -> float:
    if len(left) != len(right):
        raise ValueError("Vectors must have the same dimensions")
    return sum(a * b for a, b in zip(left, right))
