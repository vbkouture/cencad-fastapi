"""ContactForm repository for MongoDB persistence."""

from __future__ import annotations

from datetime import UTC
from typing import Any

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection, AsyncIOMotorDatabase

from app.domain.contact_forms.value_objects import ContactFormStatus


class ContactFormRepository:
    """Repository for ContactForm aggregate using MongoDB."""

    def __init__(self, db: AsyncIOMotorDatabase[Any]) -> None:
        """Initialize with MongoDB database instance."""
        self.collection: AsyncIOMotorCollection[dict[str, Any]] = db["contact-forms"]

    async def create(
        self,
        name: str,
        email: str,
        subject: str,
        message: str,
    ) -> dict[str, Any]:
        """
        Create a new contact form submission in the database.

        Args:
            name: Submitter's name
            email: Submitter's email
            subject: Contact form subject
            message: Contact form message

        Returns:
            Created contact form document with _id
        """
        from datetime import datetime

        contact_form_doc: dict[str, Any] = {
            "name": name,
            "email": email.lower(),
            "subject": subject,
            "message": message,
            "status": ContactFormStatus.PENDING,
            "history": [],
            "created_at": datetime.now(UTC),
            "updated_at": None,
        }

        result = await self.collection.insert_one(contact_form_doc)
        contact_form_doc["_id"] = result.inserted_id

        return contact_form_doc

    async def find_by_id(self, form_id: str) -> dict[str, Any] | None:
        """
        Find a contact form by ID.

        Args:
            form_id: MongoDB ObjectId as string

        Returns:
            Contact form document if found, None otherwise
        """
        try:
            return await self.collection.find_one({"_id": ObjectId(form_id)})
        except Exception:
            return None

    async def get_all(self) -> list[dict[str, Any]]:
        """Get all contact form submissions from database."""
        return await self.collection.find().sort("created_at", -1).to_list(length=None)

    async def update_status(
        self,
        form_id: str,
        status: ContactFormStatus,
        user_id: str,
        note: str | None = None,
    ) -> dict[str, Any] | None:
        """
        Update the status of a contact form.

        Args:
            form_id: MongoDB ObjectId as string
            status: New status to set
            user_id: ID of the user (admin) making the change
            note: Optional note explaining the change

        Returns:
            Updated contact form document if found, None otherwise
        """
        from datetime import datetime

        history_entry = {
            "status": status,
            "changed_by": user_id,
            "changed_at": datetime.now(UTC),
            "note": note,
        }

        try:
            result = await self.collection.find_one_and_update(
                {"_id": ObjectId(form_id)},
                {
                    "$set": {
                        "status": status,
                        "updated_at": datetime.now(UTC),
                    },
                    "$push": {"history": history_entry},
                },
                return_document=True,
            )
            return result
        except Exception:
            return None

    async def delete(self, form_id: str) -> bool:
        """
        Delete a contact form submission from database.

        Args:
            form_id: MongoDB ObjectId as string

        Returns:
            True if deleted, False if not found
        """
        try:
            result = await self.collection.delete_one({"_id": ObjectId(form_id)})
            return result.deleted_count > 0
        except Exception:
            return False

    async def create_indexes(self) -> None:
        """Create necessary database indexes for performance."""
        # Create index on created_at for sorting
        await self.collection.create_index("created_at")

        # Create index on email for potential lookups
        await self.collection.create_index("email")

        # Create index on status for filtering
        await self.collection.create_index("status")
