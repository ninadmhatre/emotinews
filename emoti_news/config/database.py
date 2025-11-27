"""Database configuration and engine management."""

import os


DB_TYPE = os.getenv("EMOTINEWS_DB_TYPE", "sqlite")

POSTGRES: dict[str, str | int] = {
    "host": "localhost",
    "port": 5432,
    "database": "news",
    "user": "postgres",
    "password": os.getenv("PG_PASS", ""),
}

SQLITE: dict[str, str] = {
    "path": os.getenv("EMOTINEWS_SQLITE_PATH", "news.db"),
}
