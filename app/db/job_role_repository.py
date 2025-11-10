"""Job role repository for MongoDB persistence."""

from __future__ import annotations

from typing import Any

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection, AsyncIOMotorDatabase  # type: ignore[import-untyped]


class JobRoleRepository:
    """Repository for JobRole aggregate using MongoDB."""

    def __init__(self, db: AsyncIOMotorDatabase) -> None:  # type: ignore[name-defined]
        """Initialize with MongoDB database instance."""
        self.collection: AsyncIOMotorCollection[dict[str, Any]] = db["job_roles"]  # type: ignore[index,assignment]

    async def create_job_role(
        self,
        name: str,
        description: str,
    ) -> dict[str, Any]:
        """
        Create a new job role in the database.

        Args:
            name: Job role name
            description: Job role description

        Returns:
            Created job role document with _id

        Raises:
            ValueError: If job role with same name already exists
        """
        # Check if job role with same name already exists
        existing = await self.collection.find_one({"name": name})
        if existing:
            raise ValueError(f"Job role with name '{name}' already exists")

        job_role_doc: dict[str, Any] = {
            "name": name,
            "description": description,
            "created_at": ObjectId().generation_time,
            "updated_at": ObjectId().generation_time,
        }

        result = await self.collection.insert_one(job_role_doc)
        job_role_doc["_id"] = result.inserted_id

        return job_role_doc

    async def find_by_id(self, job_role_id: str) -> dict[str, Any] | None:
        """
        Find a job role by ID.

        Args:
            job_role_id: MongoDB ObjectId as string

        Returns:
            Job role document if found, None otherwise
        """
        try:
            return await self.collection.find_one({"_id": ObjectId(job_role_id)})
        except Exception:
            return None

    async def find_by_name(self, name: str) -> dict[str, Any] | None:
        """
        Find a job role by name.

        Args:
            name: Job role name

        Returns:
            Job role document if found, None otherwise
        """
        return await self.collection.find_one({"name": name})

    async def get_all_job_roles(self) -> list[dict[str, Any]]:
        """Get all job roles from database."""
        return await self.collection.find().to_list(length=None)  # type: ignore[return-value]

    async def update_job_role(
        self,
        job_role_id: str,
        name: str | None = None,
        description: str | None = None,
    ) -> dict[str, Any] | None:
        """
        Update a job role.

        Args:
            job_role_id: MongoDB ObjectId as string
            name: New name (optional)
            description: New description (optional)

        Returns:
            Updated job role document if found and updated, None otherwise
        """
        try:
            update_data: dict[str, Any] = {}
            if name is not None:
                # Check if new name already exists
                existing = await self.collection.find_one(
                    {"name": name, "_id": {"$ne": ObjectId(job_role_id)}}
                )
                if existing:
                    raise ValueError(f"Job role with name '{name}' already exists")
                update_data["name"] = name

            if description is not None:
                update_data["description"] = description

            if not update_data:
                # No changes to make
                return await self.find_by_id(job_role_id)

            update_data["updated_at"] = ObjectId().generation_time

            result = await self.collection.find_one_and_update(
                {"_id": ObjectId(job_role_id)},
                {"$set": update_data},
                return_document=True,
            )
            return result
        except ValueError:
            raise
        except Exception:
            return None

    async def delete_job_role(self, job_role_id: str) -> bool:
        """
        Delete a job role from database.

        Args:
            job_role_id: MongoDB ObjectId as string

        Returns:
            True if deleted, False if job role not found
        """
        try:
            result = await self.collection.delete_one({"_id": ObjectId(job_role_id)})
            return result.deleted_count > 0
        except Exception:
            return False

    async def create_indexes(self) -> None:
        """Create necessary database indexes for performance."""
        # Create unique index on name for fast lookups and uniqueness
        await self.collection.create_index("name", unique=True)
