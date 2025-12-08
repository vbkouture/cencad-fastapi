"""MongoDB database connection and utilities."""

from __future__ import annotations

from typing import Any

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.core.config import settings

# Global MongoDB client and database instances
_client: AsyncIOMotorClient[Any] | None = None
_db: AsyncIOMotorDatabase[Any] | None = None


async def connect_to_mongodb() -> None:
    """Initialize MongoDB connection."""
    global _client, _db

    _client = AsyncIOMotorClient(settings.mongodb_url)
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
