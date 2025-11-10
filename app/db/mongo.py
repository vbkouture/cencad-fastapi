"""MongoDB database connection and utilities."""

from __future__ import annotations

from typing import Any

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase  # type: ignore[import-untyped]

from app.core.config import settings

# Global MongoDB client and database instances
_client: AsyncIOMotorClient | None = None  # type: ignore[name-defined]
_db: AsyncIOMotorDatabase | None = None  # type: ignore[name-defined]


async def connect_to_mongodb() -> None:
    """Initialize MongoDB connection."""
    global _client, _db

    _client = AsyncIOMotorClient(settings.mongodb_url)  # type: ignore[assignment]
    _db = _client[settings.mongodb_db]  # type: ignore[index]

    # Verify connection
    try:
        await _client.admin.command("ping")  # type: ignore[attr-defined]
        print(f"✅ Connected to MongoDB: {settings.mongodb_db}")
    except Exception as e:
        print(f"❌ Failed to connect to MongoDB: {e}")
        raise


async def close_mongodb_connection() -> None:
    """Close MongoDB connection."""
    global _client

    if _client:
        _client.close()  # type: ignore[attr-defined]
        print("✅ Closed MongoDB connection")


def get_database() -> Any:
    """Get the MongoDB database instance."""
    if _db is None:
        raise RuntimeError("Database not initialized. Call connect_to_mongodb() first.")
    return _db  # type: ignore[return-value]
