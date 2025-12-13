"""Certification repository for MongoDB persistence."""

from __future__ import annotations

from typing import Any

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection, AsyncIOMotorDatabase

from app.db.vendor_repository import VendorRepository


class CertificationRepository:
    """Repository for Certification aggregate using MongoDB."""

    def __init__(self, db: AsyncIOMotorDatabase[Any]) -> None:
        """Initialize with MongoDB database instance."""
        self.collection: AsyncIOMotorCollection[dict[str, Any]] = db["certifications"]
        self.vendor_repo = VendorRepository(db)

    async def create_certification(
        self,
        vendor_id: str,
        description: str | None = None,
        url: str | None = None,
    ) -> dict[str, Any]:
        """
        Create a new certification in the database.

        Args:
            vendor_id: existing Vendor ObjectId string
            description: Optional description
            url: Optional URL

        Returns:
            Created certification document with _id

        Raises:
            ValueError: If vendor_id does not exist
        """
        # Validate vendor existence
        vendor = await self.vendor_repo.find_by_id(vendor_id)
        if not vendor:
            raise ValueError(f"Vendor with id '{vendor_id}' does not exist")

        cert_doc: dict[str, Any] = {
            "vendor_id": ObjectId(vendor_id),
            "description": description,
            "url": url,
            "created_at": ObjectId().generation_time,
            "updated_at": ObjectId().generation_time,
        }

        result = await self.collection.insert_one(cert_doc)
        cert_doc["_id"] = result.inserted_id

        return cert_doc

    async def find_by_id(self, cert_id: str) -> dict[str, Any] | None:
        """
        Find a certification by ID.

        Args:
            cert_id: MongoDB ObjectId as string

        Returns:
            Certification document if found, None otherwise
        """
        try:
            return await self.collection.find_one({"_id": ObjectId(cert_id)})
        except Exception:
            return None

    async def get_all_certifications(self) -> list[dict[str, Any]]:
        """Get all certifications from database."""
        return await self.collection.find().to_list(length=None)

    async def update_certification(
        self,
        cert_id: str,
        vendor_id: str | None = None,
        description: str | None = None,
        url: str | None = None,
    ) -> dict[str, Any] | None:
        """
        Update a certification.

        Args:
            cert_id: MongoDB ObjectId as string
            vendor_id: New vendor ID (optional)
            description: New description (optional)
            url: New URL (optional)

        Returns:
            Updated certification document if found and updated, None otherwise
        """
        try:
            update_data: dict[str, Any] = {}
            if vendor_id is not None:
                # Check if new vendor exists
                vendor = await self.vendor_repo.find_by_id(vendor_id)
                if not vendor:
                    raise ValueError(f"Vendor with id '{vendor_id}' does not exist")
                update_data["vendor_id"] = ObjectId(vendor_id)

            if description is not None:
                update_data["description"] = description

            if url is not None:
                update_data["url"] = url

            if not update_data:
                # No changes to make
                return await self.find_by_id(cert_id)

            update_data["updated_at"] = ObjectId().generation_time

            result = await self.collection.find_one_and_update(
                {"_id": ObjectId(cert_id)},
                {"$set": update_data},
                return_document=True,
            )
            return result
        except ValueError:
            raise
        except Exception:
            return None

    async def delete_certification(self, cert_id: str) -> bool:
        """
        Delete a certification from database.
        """
        try:
            result = await self.collection.delete_one({"_id": ObjectId(cert_id)})
            return result.deleted_count > 0
        except Exception:
            return False
