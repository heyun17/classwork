"""FastAPI application composition root."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from config import Settings
from db import create_mysql_connection
from repositories import MySQLProductRepository, ProductRepository
from routes import router
from services import ProductService


BASE_DIR = Path(__file__).resolve().parent


def create_app(
    settings: Settings | None = None,
    repository: ProductRepository | None = None,
) -> FastAPI:
    """Create a configured app with an injectable repository for tests."""

    runtime_settings = settings or Settings.from_env()
    app = FastAPI(title="Shop Catalog", version="1.0.0")
    app.state.templates = Jinja2Templates(directory=BASE_DIR / "templates")
    selected_repository = (
        repository
        if repository is not None
        else MySQLProductRepository(
            lambda: create_mysql_connection(runtime_settings)
        )
    )
    app.state.product_service = ProductService(selected_repository)
    app.mount(
        "/static",
        StaticFiles(directory=BASE_DIR / "static"),
        name="static",
    )
    app.include_router(router)
    return app


app = create_app()
