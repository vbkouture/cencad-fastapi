"""Enrollment repository for MongoDB persistence."""

from __future__ import annotations

from typing import Any

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection, AsyncIOMotorDatabase


class EnrollmentRepository:
    """Repository for Enrollment aggregate using MongoDB."""

    def __init__(self, db: AsyncIOMotorDatabase[Any]) -> None:
        """Initialize with MongoDB database instance."""
        self.collection: AsyncIOMotorCollection[dict[str, Any]] = db["enrollments"]

    async def create_enrollment(
        self,
        user_id: str,
        schedule_id: str,
        course_id: str,
        payment_transaction_id: str | None = None,
    ) -> dict[str, Any]:
        """Create a new enrollment."""
        enrollment_doc: dict[str, Any] = {
            "user_id": ObjectId(user_id),
            "schedule_id": ObjectId(schedule_id),
            "course_id": ObjectId(course_id),
            "status": "ENROLLED",
            "payment_status": "PENDING",
            "payment_transaction_id": payment_transaction_id,
            "enrolled_at": ObjectId().generation_time,
            "instructor_notes": [],
        }

        result = await self.collection.insert_one(enrollment_doc)
        enrollment_doc["_id"] = result.inserted_id

        return enrollment_doc

    async def find_by_id(self, enrollment_id: str) -> dict[str, Any] | None:
        """Find an enrollment by ID."""
        try:
            return await self.collection.find_one({"_id": ObjectId(enrollment_id)})
        except Exception:
            return None

    async def get_enrollments_by_student(self, user_id: str) -> list[dict[str, Any]]:
        """Get all enrollments for a student."""
        try:
            return await self.collection.find({"user_id": ObjectId(user_id)}).to_list(length=None)
        except Exception:
            return []

    async def get_enrollments_by_schedule(self, schedule_id: str) -> list[dict[str, Any]]:
        """Get all enrollments for a schedule."""
        try:
            return await self.collection.find({"schedule_id": ObjectId(schedule_id)}).to_list(
                length=None
            )
        except Exception:
            return []

    async def update_enrollment(
        self,
        enrollment_id: str,
        status: str | None = None,
        payment_status: str | None = None,
        completed_at: Any | None = None,
        grade: float | None = None,
        certificate_url: str | None = None,
        instructor_notes: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any] | None:
        """Update an enrollment."""
        try:
            update_data: dict[str, Any] = {}

            if status is not None:
                update_data["status"] = status
            if payment_status is not None:
                update_data["payment_status"] = payment_status
            if completed_at is not None:
                update_data["completed_at"] = completed_at
            if grade is not None:
                update_data["grade"] = grade
            if certificate_url is not None:
                update_data["certificate_url"] = certificate_url
            if instructor_notes is not None:
                update_data["instructor_notes"] = instructor_notes

            if not update_data:
                return await self.find_by_id(enrollment_id)

            result = await self.collection.find_one_and_update(
                {"_id": ObjectId(enrollment_id)},
                {"$set": update_data},
                return_document=True,
            )
            return result
        except Exception:
            return None

    async def delete_enrollment(self, enrollment_id: str) -> bool:
        """Delete an enrollment."""
        try:
            result = await self.collection.delete_one({"_id": ObjectId(enrollment_id)})
            return result.deleted_count > 0
        except Exception:
            return False

    async def create_indexes(self) -> None:
        """Create indexes."""
        await self.collection.create_index("user_id")
        await self.collection.create_index("schedule_id")
        await self.collection.create_index("course_id")
        # Compound index for unique enrollment per student per schedule
        await self.collection.create_index([("user_id", 1), ("schedule_id", 1)], unique=True)
