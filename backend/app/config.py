import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class Settings:
    app_env: str
    rag_backend: str
    database_url: str | None
    openai_api_key: str | None
    embedding_model: str
    embedding_dimensions: int


def get_settings() -> Settings:
    return Settings(
        app_env=os.getenv("APP_ENV", "local"),
        rag_backend=os.getenv("RAG_BACKEND", "local").lower(),
        database_url=os.getenv("DATABASE_URL"),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        embedding_model=os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"),
        embedding_dimensions=int(os.getenv("OPENAI_EMBEDDING_DIMENSIONS", "1536")),
    )
