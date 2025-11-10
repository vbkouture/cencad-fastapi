"""App factory for FastAPI.

Creates the FastAPI app via create_app(), sets title/version, and mounts
versioned routers at /api/v1. Exposes a module-level `app` for uvicorn:
`uvicorn app.main:app`.
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1.routers import get_v1_router
from app.db import connect_to_mongodb, close_mongodb_connection


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """
    App lifecycle manager.
    Startup: Initialize MongoDB connection
    Shutdown: Close MongoDB connection
    """
    # on_startup: Connect to MongoDB
    await connect_to_mongodb()

    yield

    # on_shutdown: Close MongoDB connection
    await close_mongodb_connection()


def create_app() -> FastAPI:
    """
    Application factory.
    - sets OpenAPI metadata
    - mounts versioned API routers
    - registers lifespan
    """
    app = FastAPI(
        title="FastAPI + Mongo Starter",
        version="1.0.0",
        description="Training track service — v1 API surface.",
        lifespan=lifespan,
        docs_url="/docs",  # Swagger UI
        redoc_url="/redoc",  # ReDoc UI
        openapi_url="/openapi.json",  # OpenAPI spec
    )

    # Mount v1
    app.include_router(get_v1_router())

    # Optional: a root redirect/info (kept simple)
    async def root() -> dict[str, str]:
        return {"service": "fastapi-mongo-starter"}

    # register the route explicitly so static analyzers see the function is used
    app.add_api_route("/", root, methods=["GET"], tags=["meta"])

    return app


# uvicorn entrypoint: `uvicorn app.main:app --reload`
app = create_app()
