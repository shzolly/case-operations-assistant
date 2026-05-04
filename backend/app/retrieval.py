from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from backend.app.embeddings import HashEmbeddingModel
from backend.app.config import get_settings
from backend.app.models import Citation
from backend.app.retrieval_text import tokenize


ROOT = Path(__file__).resolve().parents[2]
POLICY_DIR = ROOT / "knowledge" / "policies"
EMBEDDING_MODEL = HashEmbeddingModel(dimensions=64)


@dataclass(frozen=True)
class KnowledgeChunk:
    source_id: str
    title: str
    chunk_id: str
    text: str
    tokens: frozenset[str]
    embedding: tuple[float, ...]


def parse_policy_doc(path: Path) -> tuple[str, str, str]:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    title = lines[0].lstrip("# ").strip() if lines else path.stem
    source_id = path.stem
    body_lines = []

    for line in lines[1:]:
        if line.lower().startswith("source id:"):
            source_id = line.split(":", 1)[1].strip()
            continue
        if line.lower().startswith("domain:"):
            continue
        body_lines.append(line)

    body = "\n".join(body_lines).strip()
    return source_id, title, body


def chunk_text(source_id: str, title: str, text: str, max_words: int = 90) -> list[KnowledgeChunk]:
    paragraphs = [paragraph.strip() for paragraph in text.split("\n\n") if paragraph.strip()]
    chunks = []
    current: list[str] = []
    current_words = 0

    for paragraph in paragraphs:
        words = paragraph.split()
        if current and current_words + len(words) > max_words:
            chunk_body = "\n\n".join(current)
            chunks.append(
                KnowledgeChunk(
                    source_id=source_id,
                    title=title,
                    chunk_id=f"{source_id}#{len(chunks) + 1}",
                    text=chunk_body,
                    tokens=frozenset(tokenize(f"{title} {chunk_body}")),
                    embedding=EMBEDDING_MODEL.embed(f"{title} {chunk_body}"),
                )
            )
            current = []
            current_words = 0
        current.append(paragraph)
        current_words += len(words)

    if current:
        chunk_body = "\n\n".join(current)
        chunks.append(
            KnowledgeChunk(
                source_id=source_id,
                title=title,
                chunk_id=f"{source_id}#{len(chunks) + 1}",
                text=chunk_body,
                tokens=frozenset(tokenize(f"{title} {chunk_body}")),
                embedding=EMBEDDING_MODEL.embed(f"{title} {chunk_body}"),
            )
        )
    return chunks


@lru_cache(maxsize=1)
def load_knowledge_index() -> tuple[KnowledgeChunk, ...]:
    chunks: list[KnowledgeChunk] = []
    for path in sorted(POLICY_DIR.glob("*.md")):
        source_id, title, body = parse_policy_doc(path)
        chunks.extend(chunk_text(source_id, title, body))
    return tuple(chunks)


def retrieve_policy(query: str, limit: int = 3) -> list[Citation]:
    settings = get_settings()
    if settings.rag_backend == "pgvector":
        from backend.app.pgvector_store import PgVectorStore

        return PgVectorStore().search(query, limit=limit)

    from backend.app.vector_store import InMemoryVectorStore

    vector_store = InMemoryVectorStore(load_knowledge_index(), EMBEDDING_MODEL)
    ranked = vector_store.search(query, limit=limit)
    return [
        Citation(
            source_id=result.chunk.chunk_id,
            title=result.chunk.title,
            excerpt=result.chunk.text,
        )
        for result in ranked
    ]
