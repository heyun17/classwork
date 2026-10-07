"""Repository contract and MySQL product implementation."""

from __future__ import annotations

from typing import Any, Callable, Protocol

from domain import Product


class RepositoryError(RuntimeError):
    """Raised when a product query fails."""


class ProductRepository(Protocol):
    def list(
        self,
        *,
        keyword: str | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> list[Product]: ...

    def get_by_id(self, product_id: int) -> Product | None: ...


def _escape_like(value: str) -> str:
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


class MySQLProductRepository:
    """Product repository backed by MySQL."""

    def __init__(self, connection_factory: Callable[[], Any]) -> None:
        self._connection_factory = connection_factory

    def list(
        self,
        *,
        keyword: str | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> list[Product]:
        if offset < 0 or limit < 1:
            raise ValueError("offset must be non-negative and limit must be positive")

        query = "SELECT id, name, price FROM products"
        parameters: list[object] = []
        if keyword:
            query += r" WHERE LOWER(name) LIKE %s ESCAPE '\\'"
            parameters.append(f"%{_escape_like(keyword.lower())}%")
        query += " ORDER BY id LIMIT %s OFFSET %s"
        parameters.extend((limit, offset))

        connection: Any | None = None
        cursor: Any | None = None
        try:
            connection = self._connection_factory()
            cursor = connection.cursor(dictionary=True)
            cursor.execute(query, tuple(parameters))
            return [Product.model_validate(row) for row in cursor.fetchall()]
        except Exception as exc:
            raise RepositoryError("Could not load products") from exc
        finally:
            if cursor is not None:
                cursor.close()
            if connection is not None:
                connection.close()

    def get_by_id(self, product_id: int) -> Product | None:
        if product_id < 1:
            raise ValueError("product_id must be positive")

        connection: Any | None = None
        cursor: Any | None = None
        try:
            connection = self._connection_factory()
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                "SELECT id, name, price FROM products WHERE id = %s",
                (product_id,),
            )
            row = cursor.fetchone()
            return Product.model_validate(row) if row else None
        except Exception as exc:
            raise RepositoryError("Could not load the product") from exc
        finally:
            if cursor is not None:
                cursor.close()
            if connection is not None:
                connection.close()
