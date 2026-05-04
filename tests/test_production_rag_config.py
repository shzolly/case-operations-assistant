import pytest

from backend.app.config import get_settings
from backend.app.embeddings import OpenAIEmbeddingModel
from backend.app.pgvector_store import to_pgvector


def test_settings_default_to_text_embedding_3_small(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_EMBEDDING_MODEL", raising=False)
    monkeypatch.delenv("OPENAI_EMBEDDING_DIMENSIONS", raising=False)

    settings = get_settings()

    assert settings.embedding_model == "text-embedding-3-small"
    assert settings.embedding_dimensions == 1536


def test_pgvector_literal_format() -> None:
    assert to_pgvector((0.1, -0.25, 1.0)) == "[0.1000000000,-0.2500000000,1.0000000000]"


def test_openai_embedding_requires_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    model = OpenAIEmbeddingModel(api_key=None)

    with pytest.raises(RuntimeError, match="OPENAI_API_KEY"):
        model.embed("family case follow-up")

