from dataclasses import dataclass

from backend.app.config import get_settings
from backend.app.embeddings import EmbeddingModel, OpenAIEmbeddingModel
from backend.app.models import Citation
from backend.app.postgres import connect


def to_pgvector(vector: tuple[float, ...]) -> str:
    return "[" + ",".join(f"{value:.10f}" for value in vector) + "]"


@dataclass(frozen=True)
class PgVectorSettings:
    database_url: str
    embedding_dimensions: int


class PgVectorStore:
    """PostgreSQL + pgvector retrieval store."""

    def __init__(
        self,
        database_url: str | None = None,
        embedding_model: EmbeddingModel | None = None,
    ) -> None:
        settings = get_settings()
        self.database_url = database_url or settings.database_url
        self.embedding_model = embedding_model or OpenAIEmbeddingModel()
        if not self.database_url:
            raise RuntimeError("DATABASE_URL is required for pgvector retrieval")

    def search(self, query: str, limit: int = 3) -> list[Citation]:
        query_vector = to_pgvector(self.embedding_model.embed(query))
        sql = """
            SELECT
                source_id,
                chunk_id,
                title,
                content,
                1 - (embedding <=> CAST(%s AS vector)) AS score
            FROM rag_chunks
            ORDER BY embedding <=> CAST(%s AS vector)
            LIMIT %s
        """
        connection = connect(self.database_url)
        cursor = connection.cursor()
        try:
            cursor.execute(sql, (query_vector, query_vector, limit))
            rows = cursor.fetchall()
        finally:
            cursor.close()
            connection.close()

        return [
            Citation(
                source_id=f"{source_id}#{chunk_id}",
                title=title,
                excerpt=content,
            )
            for source_id, chunk_id, title, content, _score in rows
        ]
