# PostgreSQL pgvector RAG

The production RAG path uses:

- OpenAI `text-embedding-3-small`
- 1536-dimensional vectors
- PostgreSQL with the `pgvector` extension
- `pg8000` as the Python PostgreSQL driver
- cosine distance via `vector_cosine_ops`

## Environment

```powershell
$env:OPENAI_API_KEY="..."
$env:RAG_BACKEND="pgvector"
$env:DATABASE_URL="postgresql://judiciary:judiciary_dev@localhost:5432/judiciary_ai"
$env:OPENAI_EMBEDDING_MODEL="text-embedding-3-small"
$env:OPENAI_EMBEDDING_DIMENSIONS="1536"
```

## Start PostgreSQL

```powershell
docker compose up postgres
```

The compose file uses the `pgvector/pgvector:pg16` image and runs
`infra/postgres/init.sql` to create the extension, `rag_chunks` table, and HNSW
cosine index.

## Ingest Policy Documents

```powershell
.venv\Scripts\python.exe scripts\ingest_policies_pgvector.py
```

The script reads Markdown files from `knowledge/policies`, chunks them, embeds
each chunk with `text-embedding-3-small`, and upserts vectors into `rag_chunks`.

## Run API Against pgvector

```powershell
$env:RAG_BACKEND="pgvector"
.venv\Scripts\python.exe -m uvicorn backend.app.api:app --reload --port 8000
```

For local tests that should not call OpenAI or PostgreSQL, leave `RAG_BACKEND`
unset so the deterministic local vector store is used.
