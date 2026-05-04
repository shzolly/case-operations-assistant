# RAG Design

## Current MVP

The local MVP uses a Markdown corpus under `knowledge/policies`.

Ingestion flow:

1. Read each Markdown policy file.
2. Parse the title and source id.
3. Split content into paragraph-aware chunks.
4. Tokenize each chunk.
5. Generate a deterministic local embedding for each chunk.
6. Rank chunks with hybrid lexical/vector scoring.
7. Return chunk-level citations such as `SOP-FM-001#1`.

## Production RAG Path

The production path uses OpenAI `text-embedding-3-small` and PostgreSQL with
pgvector. Set `RAG_BACKEND=pgvector` to make runtime retrieval query the
database instead of the local in-memory index.

See `docs/pgvector-rag.md` for setup and ingestion commands.

## Case-Aware Retrieval

The assistant does not retrieve only from the raw user question. For case
workflow questions, the orchestrator first looks up the case record, then builds
a retrieval query from:

- user question
- case type
- case status
- assigned unit
- last docket event
- case flags

This improves retrieval for generic questions such as "What should I do next for
case FM-2026-001?" because the policy search receives operational context that
the user did not explicitly type.

## Production Upgrade Path

The local lexical index is intentionally simple. The next production step is to
replace the local hash embedding model and in-memory vectors with production
embeddings and a managed vector store while preserving the same retrieval
contract.

Production implementation:

- Store source documents in S3 or a controlled document repository.
- Run ingestion as a batch job.
- Generate embeddings for chunks with `text-embedding-3-small`.
- Store vectors in PostgreSQL with pgvector.
- Keep source id, chunk id, title, and excerpt metadata.
- Add evaluation tests for top-k recall, citation quality, and refusal behavior.
