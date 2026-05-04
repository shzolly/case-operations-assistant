from urllib.parse import unquote, urlparse


def parse_database_url(database_url: str) -> dict:
    parsed = urlparse(database_url)
    if parsed.scheme not in {"postgresql", "postgres"}:
        raise ValueError("DATABASE_URL must use postgresql:// or postgres://")
    if not parsed.hostname:
        raise ValueError("DATABASE_URL must include a host")

    database = parsed.path.lstrip("/") or None
    return {
        "user": unquote(parsed.username or ""),
        "password": unquote(parsed.password or ""),
        "host": parsed.hostname,
        "port": parsed.port or 5432,
        "database": database,
    }


def connect(database_url: str):
    import pg8000.dbapi

    return pg8000.dbapi.connect(**parse_database_url(database_url))

