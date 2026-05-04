from backend.app.postgres import parse_database_url


def test_parse_database_url() -> None:
    parsed = parse_database_url("postgresql://judiciary:secret@localhost:5432/judiciary_ai")

    assert parsed == {
        "user": "judiciary",
        "password": "secret",
        "host": "localhost",
        "port": 5432,
        "database": "judiciary_ai",
    }

