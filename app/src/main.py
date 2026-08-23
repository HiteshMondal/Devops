"""Application entrypoint.

Run locally with:
    uvicorn src.main:app --reload --port 8000

Run in the container with:
    uvicorn src.main:app --host 0.0.0.0 --port 8000
"""

from __future__ import annotations

from fastapi import FastAPI

from src.api.routes import router
from src.core.config import get_settings
from src.core.logging_config import configure_logging, get_logger

configure_logging()
logger = get_logger(__name__)

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description=(
        "DevOps console demonstrating core DSA (priority queue, LRU cache, "
        "topological sort, binary search), OOP (abstraction, inheritance, "
        "polymorphism, design patterns), basic system design (rate limiting, "
        "circuit breaker, singleton config) and SQL (SQLite persistence)."
    ),
    version="0.1.0",
)

app.include_router(router, prefix="/api/v1")


@app.on_event("startup")
def on_startup() -> None:
    logger.info("Starting %s in %s environment", settings.app_name, settings.env)


@app.get("/")
def root() -> dict[str, str]:
    return {"service": settings.app_name, "status": "running"}