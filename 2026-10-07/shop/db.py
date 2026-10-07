"""Database connection boundary."""

from __future__ import annotations

from typing import Any

from config import Settings


class DatabaseError(RuntimeError):
    """Raised when the driver or database connection is unavailable."""


def create_mysql_connection(settings: Settings) -> Any:
    """Create one MySQL connection, importing the driver only when needed."""

    try:
        import mysql.connector
    except ModuleNotFoundError as exc:
        raise DatabaseError(
            "mysql-connector-python is required to access the database"
        ) from exc

    try:
        return mysql.connector.connect(**settings.mysql_kwargs())
    except Exception as exc:
        raise DatabaseError("Could not connect to MySQL") from exc
