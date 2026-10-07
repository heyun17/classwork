"""One-off database connectivity check."""

from __future__ import annotations

from typing import Any

from config import Settings
from db import create_mysql_connection


def run_check() -> int:
    """Print database status and return a shell-friendly exit code."""

    connection: Any | None = None
    cursor: Any | None = None
    try:
        connection = create_mysql_connection(Settings.from_env())
        cursor = connection.cursor()
        cursor.execute("SELECT DATABASE()")
        database_name = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM products")
        product_count = cursor.fetchone()[0]
        print("MySQL 연결 성공")
        print("데이터베이스:", database_name)
        print("상품 개수:", product_count)
        return 0
    except Exception as error:
        print("MySQL 연결 실패")
        print(error)
        return 1
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None:
            connection.close()


def main() -> int:
    return run_check()
