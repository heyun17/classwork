from __future__ import annotations

import unittest

from domain import Product
from services import ProductService


class FakeProductRepository:
    def __init__(self) -> None:
        self.last_keyword: str | None = None
        self.products = [Product(id=1, name="노트북", price=1200000)]

    def list(
        self,
        *,
        keyword: str | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> list[Product]:
        self.last_keyword = keyword
        return self.products[offset : offset + limit]

    def get_by_id(self, product_id: int) -> Product | None:
        return next((item for item in self.products if item.id == product_id), None)


class ProductServiceTests(unittest.TestCase):
    def test_search_normalizes_whitespace(self) -> None:
        repository = FakeProductRepository()
        ProductService(repository).search("  노트북   ")
        self.assertEqual(repository.last_keyword, "노트북")

    def test_blank_search_is_sent_as_no_filter(self) -> None:
        repository = FakeProductRepository()
        ProductService(repository).search("   ")
        self.assertIsNone(repository.last_keyword)

    def test_search_rejects_overlong_keyword(self) -> None:
        with self.assertRaises(ValueError):
            ProductService(FakeProductRepository()).search("a" * 101)


if __name__ == "__main__":
    unittest.main()
