"""Vendor repository for MongoDB persistence."""

from __future__ import annotations

from typing import Any

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection, AsyncIOMotorDatabase


class VendorRepository:
    """Repository for Vendor aggregate using MongoDB."""

    def __init__(self, db: AsyncIOMotorDatabase[Any]) -> None:
        """Initialize with MongoDB database instance."""
        self.collection: AsyncIOMotorCollection[dict[str, Any]] = db["vendors"]

    async def create_vendor(
        self,
        name: str,
        description: str,
        logo: str | None = None,
    ) -> dict[str, Any]:
        """
        Create a new vendor in the database.

        Args:
            name: Vendor name
            description: Vendor description
            logo: Optional vendor logo URL

        Returns:
            Created vendor document with _id

        Raises:
            ValueError: If vendor with same name already exists
        """
        # Check if vendor with same name already exists
        existing = await self.collection.find_one({"name": name})
        if existing:
            raise ValueError(f"Vendor with name '{name}' already exists")

        vendor_doc: dict[str, Any] = {
            "name": name,
            "description": description,
            "logo": logo,
            "created_at": ObjectId().generation_time,
            "updated_at": ObjectId().generation_time,
        }

        result = await self.collection.insert_one(vendor_doc)
        vendor_doc["_id"] = result.inserted_id

        return vendor_doc

    async def find_by_id(self, vendor_id: str) -> dict[str, Any] | None:
        """
        Find a vendor by ID.

        Args:
            vendor_id: MongoDB ObjectId as string

        Returns:
            Vendor document if found, None otherwise
        """
        try:
            return await self.collection.find_one({"_id": ObjectId(vendor_id)})
        except Exception:
            return None

    async def find_by_name(self, name: str) -> dict[str, Any] | None:
        """
        Find a vendor by name.

        Args:
            name: Vendor name

        Returns:
            Vendor document if found, None otherwise
        """
        return await self.collection.find_one({"name": name})

    async def get_all_vendors(self) -> list[dict[str, Any]]:
        """Get all vendors from database."""
        return await self.collection.find().to_list(length=None)

    async def update_vendor(
        self,
        vendor_id: str,
        name: str | None = None,
        description: str | None = None,
        logo: str | None = None,
    ) -> dict[str, Any] | None:
        """
        Update a vendor.

        Args:
            vendor_id: MongoDB ObjectId as string
            name: New name (optional)
            description: New description (optional)
            logo: New logo URL (optional)

        Returns:
            Updated vendor document if found and updated, None otherwise
        """
        try:
            update_data: dict[str, Any] = {}
            if name is not None:
                # Check if new name already exists
                existing = await self.collection.find_one(
                    {"name": name, "_id": {"$ne": ObjectId(vendor_id)}}
                )
                if existing:
                    raise ValueError(f"Vendor with name '{name}' already exists")
                update_data["name"] = name

            if description is not None:
                update_data["description"] = description

            if logo is not None:
                update_data["logo"] = logo

            if not update_data:
                # No changes to make
                return await self.find_by_id(vendor_id)

            update_data["updated_at"] = ObjectId().generation_time

            result = await self.collection.find_one_and_update(
                {"_id": ObjectId(vendor_id)},
                {"$set": update_data},
                return_document=True,
            )
            return result
        except ValueError:
            raise
        except Exception:
            return None

    async def delete_vendor(self, vendor_id: str) -> bool:
        """
        Delete a vendor from database.

        Args:
            vendor_id: MongoDB ObjectId as string

        Returns:
            True if deleted, False if vendor not found
        """
        try:
            result = await self.collection.delete_one({"_id": ObjectId(vendor_id)})
            return result.deleted_count > 0
        except Exception:
            return False

    async def create_indexes(self) -> None:
        """Create necessary database indexes for performance."""
        # Create unique index on name for fast lookups and uniqueness
        await self.collection.create_index("name", unique=True)
