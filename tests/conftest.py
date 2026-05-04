import pytest


@pytest.fixture(autouse=True)
def default_tests_to_local_rag(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RAG_BACKEND", "local")

