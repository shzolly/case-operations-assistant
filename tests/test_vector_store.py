from backend.app.embeddings import HashEmbeddingModel
from backend.app.retrieval import load_knowledge_index
from backend.app.vector_store import InMemoryVectorStore


def test_in_memory_vector_store_returns_ranked_results() -> None:
    store = InMemoryVectorStore(load_knowledge_index(), HashEmbeddingModel())

    results = store.search("family missing documents follow-up", limit=2)

    assert len(results) == 2
    assert results[0].chunk.source_id == "SOP-FM-001"
    assert results[0].score >= results[1].score
    assert results[0].lexical_score > 0

