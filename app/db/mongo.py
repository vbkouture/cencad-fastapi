"""MongoDB database connection and utilities."""

from __future__ import annotations

from typing import Any

import certifi
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.core.config import settings

# Global MongoDB client and database instances
_client: AsyncIOMotorClient[Any] | None = None
_db: AsyncIOMotorDatabase[Any] | None = None


async def connect_to_mongodb() -> None:
    """Initialize MongoDB connection."""
    global _client, _db

    client_options = {}
    if "localhost" not in settings.mongodb_url and "127.0.0.1" not in settings.mongodb_url:
        client_options["tlsCAFile"] = certifi.where()

    _client = AsyncIOMotorClient(settings.mongodb_url, **client_options)  # type: ignore[arg-type]
    _db = _client[settings.mongodb_db]

    # Verify connection
    try:
        await _client.admin.command("ping")
        print(f"✅ Connected to MongoDB: {settings.mongodb_db}")
    except Exception as e:
        print(f"❌ Failed to connect to MongoDB: {e}")
        raise


async def close_mongodb_connection() -> None:
    """Close MongoDB connection."""
    global _client

    if _client:
        _client.close()
        print("✅ Closed MongoDB connection")


def get_database() -> AsyncIOMotorDatabase[Any]:
    """Get the MongoDB database instance."""
    if _db is None:
        raise RuntimeError("Database not initialized. Call connect_to_mongodb() first.")
    return _db
