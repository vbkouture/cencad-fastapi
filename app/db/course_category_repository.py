"""Course category repository for MongoDB persistence."""

from __future__ import annotations

from typing import Any

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase  # type: ignore[import-untyped]


class CourseCategoryRepository:
    """Repository for CourseCategory aggregate using MongoDB."""

    def __init__(self, db: AsyncIOMotorDatabase) -> None:  # type: ignore[name-defined]
        """Initialize with MongoDB database instance."""
        self.collection = db["course_categories"]  # type: ignore[index]

    async def create_category(
        self,
        name: str,
        description: str,
    ) -> dict[str, Any]:
        """
        Create a new course category in the database.

        Args:
            name: Category name
            description: Category description

        Returns:
            Created category document with _id

        Raises:
            ValueError: If category with same name already exists
        """
        # Check if category with same name already exists
        existing = await self.collection.find_one({"name": name})
        if existing:
            raise ValueError(f"Category with name '{name}' already exists")

        category_doc = {
            "name": name,
            "description": description,
            "created_at": ObjectId().generation_time,
            "updated_at": ObjectId().generation_time,
        }

        result = await self.collection.insert_one(category_doc)
        category_doc["_id"] = result.inserted_id

        return category_doc

    async def find_by_id(self, category_id: str) -> dict[str, Any] | None:
        """
        Find a course category by ID.

        Args:
            category_id: MongoDB ObjectId as string

        Returns:
            Category document if found, None otherwise
        """
        try:
            return await self.collection.find_one({"_id": ObjectId(category_id)})
        except Exception:
            return None

    async def find_by_name(self, name: str) -> dict[str, Any] | None:
        """
        Find a course category by name.

        Args:
            name: Category name

        Returns:
            Category document if found, None otherwise
        """
        return await self.collection.find_one({"name": name})

    async def get_all_categories(self) -> list[dict[str, Any]]:
        """Get all course categories from database."""
        return await self.collection.find().to_list(length=None)

    async def update_category(
        self,
        category_id: str,
        name: str | None = None,
        description: str | None = None,
    ) -> dict[str, Any] | None:
        """
        Update a course category.

        Args:
            category_id: MongoDB ObjectId as string
            name: New name (optional)
            description: New description (optional)

        Returns:
            Updated category document if found and updated, None otherwise
        """
        try:
            update_data: dict[str, Any] = {}
            if name is not None:
                # Check if new name already exists
                existing = await self.collection.find_one(
                    {"name": name, "_id": {"$ne": ObjectId(category_id)}}
                )
                if existing:
                    raise ValueError(f"Category with name '{name}' already exists")
                update_data["name"] = name

            if description is not None:
                update_data["description"] = description

            if not update_data:
                # No changes to make
                return await self.find_by_id(category_id)

            update_data["updated_at"] = ObjectId().generation_time

            result = await self.collection.find_one_and_update(
                {"_id": ObjectId(category_id)},
                {"$set": update_data},
                return_document=True,
            )
            return result
        except ValueError:
            raise
        except Exception:
            return None

    async def delete_category(self, category_id: str) -> bool:
        """
        Delete a course category from database.

        Args:
            category_id: MongoDB ObjectId as string

        Returns:
            True if deleted, False if category not found
        """
        try:
            result = await self.collection.delete_one({"_id": ObjectId(category_id)})
            return result.deleted_count > 0
        except Exception:
            return False

    async def create_indexes(self) -> None:
        """Create necessary database indexes for performance."""
        # Create unique index on name for fast lookups and uniqueness
        await self.collection.create_index("name", unique=True)
