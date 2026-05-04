from backend.app.embeddings import HashEmbeddingModel, cosine_similarity
from backend.app.retrieval import load_knowledge_index, retrieve_policy


def test_hash_embeddings_are_deterministic_and_normalized() -> None:
    model = HashEmbeddingModel(dimensions=32)

    first = model.embed("family case follow-up")
    second = model.embed("family case follow-up")

    assert first == second
    assert len(first) == 32
    assert round(cosine_similarity(first, first), 6) == 1.0


def test_policy_index_loads_markdown_documents() -> None:
    chunks = load_knowledge_index()

    assert len(chunks) >= 5
    assert any(chunk.source_id == "SOP-FM-001" for chunk in chunks)
    assert any(chunk.source_id == "SOP-GEN-002" for chunk in chunks)
    assert all(chunk.embedding for chunk in chunks)


def test_family_follow_up_question_retrieves_family_sop_first() -> None:
    citations = retrieve_policy("family case no docket activity missing documents follow-up", limit=2)

    assert citations
    assert citations[0].source_id.startswith("SOP-FM-001")


def test_approval_question_retrieves_sensitive_action_policy() -> None:
    citations = retrieve_policy("supervisor approval official notice external communication", limit=3)

    assert any(citation.source_id.startswith("SOP-GEN-002") for citation in citations)


def test_audit_question_retrieves_audit_requirements() -> None:
    citations = retrieve_policy("audit trail user role retrieval tool call authorization", limit=2)

    assert citations[0].source_id.startswith("SOP-AUDIT-004")


def test_unknown_query_returns_no_citations() -> None:
    citations = retrieve_policy("volcanic mineral survey telescope calibration", limit=2)

    assert citations == []

