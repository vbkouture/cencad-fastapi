"""Schedule repository for MongoDB persistence."""

from __future__ import annotations

from typing import Any

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection, AsyncIOMotorDatabase  # type: ignore[import-untyped]


class ScheduleRepository:
    """Repository for Schedule aggregate using MongoDB."""

    def __init__(self, db: AsyncIOMotorDatabase) -> None:  # type: ignore[name-defined]
        """Initialize with MongoDB database instance."""
        self.collection: AsyncIOMotorCollection[dict[str, Any]] = db["schedules"]  # type: ignore[index,assignment]

    async def create_schedule(
        self,
        course_id: str,
        tutor_id: str,
        sessions: list[dict[str, Any]],
        capacity: int,
        meeting_url: str | None = None,
        timezone: str = "UTC",
    ) -> dict[str, Any]:
        """Create a new schedule."""
        schedule_doc: dict[str, Any] = {
            "course_id": ObjectId(course_id),
            "tutor_id": ObjectId(tutor_id),
            "sessions": sessions,
            "capacity": capacity,
            "enrollment_count": 0,
            "status": "UPCOMING",
            "meeting_url": meeting_url,
            "timezone": timezone,
            "created_at": ObjectId().generation_time,
            "updated_at": ObjectId().generation_time,
        }

        result = await self.collection.insert_one(schedule_doc)
        schedule_doc["_id"] = result.inserted_id

        return schedule_doc

    async def find_by_id(self, schedule_id: str) -> dict[str, Any] | None:
        """Find a schedule by ID."""
        try:
            return await self.collection.find_one({"_id": ObjectId(schedule_id)})
        except Exception:
            return None

    async def get_schedules_by_course(self, course_id: str) -> list[dict[str, Any]]:
        """Get all schedules for a course."""
        try:
            return await self.collection.find({"course_id": ObjectId(course_id)}).to_list(length=None)  # type: ignore[return-value]
        except Exception:
            return []

    async def get_schedules_by_tutor(self, tutor_id: str) -> list[dict[str, Any]]:
        """Get all schedules for a tutor."""
        try:
            return await self.collection.find({"tutor_id": ObjectId(tutor_id)}).to_list(length=None)  # type: ignore[return-value]
        except Exception:
            return []

    async def update_schedule(
        self,
        schedule_id: str,
        tutor_id: str | None = None,
        sessions: list[dict[str, Any]] | None = None,
        capacity: int | None = None,
        status: str | None = None,
        meeting_url: str | None = None,
        timezone: str | None = None,
    ) -> dict[str, Any] | None:
        """Update a schedule."""
        try:
            update_data: dict[str, Any] = {}

            if tutor_id is not None:
                update_data["tutor_id"] = ObjectId(tutor_id)
            if sessions is not None:
                update_data["sessions"] = sessions
            if capacity is not None:
                update_data["capacity"] = capacity
            if status is not None:
                update_data["status"] = status
            if meeting_url is not None:
                update_data["meeting_url"] = meeting_url
            if timezone is not None:
                update_data["timezone"] = timezone

            if not update_data:
                return await self.find_by_id(schedule_id)

            update_data["updated_at"] = ObjectId().generation_time

            result = await self.collection.find_one_and_update(
                {"_id": ObjectId(schedule_id)},
                {"$set": update_data},
                return_document=True,
            )
            return result
        except Exception:
            return None

    async def delete_schedule(self, schedule_id: str) -> bool:
        """Delete a schedule."""
        try:
            result = await self.collection.delete_one({"_id": ObjectId(schedule_id)})
            return result.deleted_count > 0
        except Exception:
            return False

    async def create_indexes(self) -> None:
        """Create indexes."""
        await self.collection.create_index("course_id")
        await self.collection.create_index("tutor_id")
        await self.collection.create_index("status")
