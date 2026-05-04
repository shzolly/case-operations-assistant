from dataclasses import dataclass

from backend.app.embeddings import EmbeddingModel, cosine_similarity
from backend.app.retrieval import KnowledgeChunk
from backend.app.retrieval_text import tokenize


@dataclass(frozen=True)
class VectorSearchResult:
    chunk: KnowledgeChunk
    score: float
    lexical_score: float
    vector_score: float
    overlap_count: int


class InMemoryVectorStore:
    """In-memory vector store for local RAG development.

    Production can replace this with pgvector or OpenSearch while keeping the
    query contract: text query in, ranked chunk results out.
    """

    def __init__(self, chunks: tuple[KnowledgeChunk, ...], embedding_model: EmbeddingModel) -> None:
        self.chunks = chunks
        self.embedding_model = embedding_model

    def search(self, query: str, limit: int = 3) -> list[VectorSearchResult]:
        query_tokens = set(tokenize(query))
        if not query_tokens:
            return []

        query_embedding = self.embedding_model.embed(query)
        results = []
        for chunk in self.chunks:
            overlap = query_tokens.intersection(chunk.tokens)
            if not overlap:
                continue
            lexical_score = len(overlap) / max(len(query_tokens), 1)
            vector_score = max(cosine_similarity(query_embedding, chunk.embedding), 0.0)
            score = (0.75 * lexical_score) + (0.25 * vector_score)
            results.append(
                VectorSearchResult(
                    chunk=chunk,
                    score=score,
                    lexical_score=lexical_score,
                    vector_score=vector_score,
                    overlap_count=len(overlap),
                )
            )

        return sorted(
            results,
            key=lambda item: (item.score, item.lexical_score, item.vector_score, item.overlap_count),
            reverse=True,
        )[:limit]

