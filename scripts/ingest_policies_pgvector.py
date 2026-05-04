import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.app.config import get_settings
from backend.app.embeddings import OpenAIEmbeddingModel
from backend.app.postgres import connect
from backend.app.pgvector_store import to_pgvector
from backend.app.retrieval import POLICY_DIR, chunk_text, parse_policy_doc
from backend.app.retrieval_text import tokenize


def iter_policy_chunks():
    for path in sorted(POLICY_DIR.glob("*.md")):
        source_id, title, body = parse_policy_doc(path)
        for chunk in chunk_text(source_id, title, body):
            chunk_number = int(chunk.chunk_id.split("#", 1)[1])
            yield path, chunk_number, chunk


def main() -> None:
    settings = get_settings()
    if not settings.database_url:
        raise RuntimeError("DATABASE_URL is required")
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is required")

    embedder = OpenAIEmbeddingModel(
        model=settings.embedding_model,
        dimensions=settings.embedding_dimensions,
        api_key=settings.openai_api_key,
    )

    upsert_sql = """
        INSERT INTO rag_chunks (
            source_id,
            chunk_id,
            title,
            content,
            token_count,
            embedding_model,
            embedding,
            metadata
        )
        VALUES (%s, %s, %s, %s, %s, %s, CAST(%s AS vector), CAST(%s AS jsonb))
        ON CONFLICT (source_id, chunk_id, embedding_model)
        DO UPDATE SET
            title = EXCLUDED.title,
            content = EXCLUDED.content,
            token_count = EXCLUDED.token_count,
            embedding = EXCLUDED.embedding,
            metadata = EXCLUDED.metadata,
            updated_at = now()
    """

    total = 0
    connection = connect(settings.database_url)
    cursor = connection.cursor()
    try:
        for path, chunk_number, chunk in iter_policy_chunks():
            text_for_embedding = f"{chunk.title}\n\n{chunk.text}"
            embedding = embedder.embed(text_for_embedding)
            cursor.execute(
                upsert_sql,
                (
                    chunk.source_id,
                    chunk_number,
                    chunk.title,
                    chunk.text,
                    len(tokenize(text_for_embedding)),
                    settings.embedding_model,
                    to_pgvector(embedding),
                    json.dumps({"path": str(path.relative_to(ROOT))}),
                ),
            )
            total += 1
        connection.commit()
    finally:
        cursor.close()
        connection.close()

    print(f"Ingested {total} policy chunks using {settings.embedding_model}")


if __name__ == "__main__":
    os.environ.setdefault("RAG_BACKEND", "pgvector")
    main()
