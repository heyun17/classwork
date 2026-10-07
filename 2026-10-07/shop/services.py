"""Use cases independent from HTTP and database details."""

from __future__ import annotations

from domain import Product
from repositories import ProductRepository


class ProductService:
    def __init__(self, repository: ProductRepository) -> None:
        self._repository = repository

    def search(
        self,
        keyword: str = "",
        *,
        offset: int = 0,
        limit: int = 100,
    ) -> list[Product]:
        normalized = " ".join(keyword.split())
        if len(normalized) > 100:
            raise ValueError("keyword must be 100 characters or fewer")
        return self._repository.list(
            keyword=normalized or None,
            offset=offset,
            limit=limit,
        )

    def get(self, product_id: int) -> Product | None:
        if product_id < 1:
            raise ValueError("product_id must be positive")
        return self._repository.get_by_id(product_id)
