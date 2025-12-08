"""App factory for FastAPI.

Creates the FastAPI app via create_app(), sets title/version, and mounts
versioned routers at /api/v1. Exposes a module-level `app` for uvicorn:
`uvicorn app.main:app`.
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.routers import get_v1_router
from app.db import close_mongodb_connection, connect_to_mongodb


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

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",
            "http://localhost:3000",
            "http://127.0.0.1:5173",
            "http://localhost:5174",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
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
