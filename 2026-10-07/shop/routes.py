"""FastAPI routes for the product catalog."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, HTTPException, Path, Query, Request
from fastapi.responses import HTMLResponse

from domain import Product
from repositories import RepositoryError
from services import ProductService


router = APIRouter()


def _service(request: Request) -> ProductService:
    return request.app.state.product_service


@router.get("/", name="home", response_class=HTMLResponse)
def home(
    request: Request,
    q: Annotated[str, Query(max_length=100)] = "",
    offset: Annotated[int, Query(ge=0, le=10_000)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
) -> HTMLResponse:
    try:
        products = _service(request).search(q, offset=offset, limit=limit)
    except RepositoryError as exc:
        raise HTTPException(status_code=503, detail="상품 데이터를 불러올 수 없습니다.") from exc

    return request.app.state.templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"products": products, "keyword": q, "offset": offset, "limit": limit},
    )


@router.get("/product/{product_id}", name="get_product", response_model=Product)
def get_product(
    request: Request,
    product_id: Annotated[int, Path(gt=0)],
) -> Product:
    try:
        product = _service(request).get(product_id)
    except RepositoryError as exc:
        raise HTTPException(status_code=503, detail="상품 데이터를 불러올 수 없습니다.") from exc
    if product is None:
        raise HTTPException(status_code=404, detail="상품을 찾을 수 없습니다.")
    return product
