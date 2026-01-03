"""Schedule repository for MongoDB persistence."""

from __future__ import annotations

from typing import Any

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection, AsyncIOMotorDatabase


class ScheduleRepository:
    """Repository for Schedule aggregate using MongoDB."""

    def __init__(self, db: AsyncIOMotorDatabase[Any]) -> None:
        """Initialize with MongoDB database instance."""
        self.collection: AsyncIOMotorCollection[dict[str, Any]] = db["schedules"]

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
            course_ids: list[Any] = [course_id]
            if ObjectId.is_valid(course_id):
                course_ids.append(ObjectId(course_id))
            return await self.collection.find({"course_id": {"$in": course_ids}}).to_list(
                length=None
            )
        except Exception:
            return []

    async def get_schedules_by_tutor(self, tutor_id: str) -> list[dict[str, Any]]:
        """Get all schedules for a tutor."""
        try:
            tutor_ids: list[Any] = [tutor_id]
            if ObjectId.is_valid(tutor_id):
                tutor_ids.append(ObjectId(tutor_id))
            return await self.collection.find({"tutor_id": {"$in": tutor_ids}}).to_list(length=None)
        except Exception:
            return []

    async def get_upcoming_schedules(
        self, course_id: str | None = None, tutor_id: str | None = None
    ) -> list[dict[str, Any]]:
        """
        Get upcoming schedules with optional filters.

        Args:
            course_id: Optional course ID filter
            tutor_id: Optional tutor ID filter

        Returns:
            List of upcoming schedules
        """
        try:
            query: dict[str, Any] = {"status": "UPCOMING"}

            if course_id:
                course_ids: list[Any] = [course_id]
                if ObjectId.is_valid(course_id):
                    course_ids.append(ObjectId(course_id))
                query["course_id"] = {"$in": course_ids}

            if tutor_id:
                tutor_ids: list[Any] = [tutor_id]
                if ObjectId.is_valid(tutor_id):
                    tutor_ids.append(ObjectId(tutor_id))
                query["tutor_id"] = {"$in": tutor_ids}

            return await self.collection.find(query).to_list(length=None)
        except Exception:
            return []

    async def get_all_schedules(self) -> list[dict[str, Any]]:
        """Get all schedules."""
        return await self.collection.find().to_list(length=None)

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

    # Resource CRUD methods

    async def add_resource(
        self, schedule_id: str, resource: dict[str, Any]
    ) -> dict[str, Any] | None:
        """Add a resource to a schedule."""
        try:
            result = await self.collection.find_one_and_update(
                {"_id": ObjectId(schedule_id)},
                {
                    "$push": {"resources": resource},
                    "$set": {"updated_at": ObjectId().generation_time},
                },
                return_document=True,
            )
            return result
        except Exception:
            return None

    async def update_resource(
        self, schedule_id: str, resource_index: int, resource_updates: dict[str, Any]
    ) -> dict[str, Any] | None:
        """Update a resource at a specific index in a schedule."""
        try:
            # Build the update dict with array index notation
            update_fields: dict[str, Any] = {}
            for key, value in resource_updates.items():
                if value is not None:
                    update_fields[f"resources.{resource_index}.{key}"] = value

            if not update_fields:
                return await self.find_by_id(schedule_id)

            update_fields["updated_at"] = ObjectId().generation_time

            result = await self.collection.find_one_and_update(
                {"_id": ObjectId(schedule_id)},
                {"$set": update_fields},
                return_document=True,
            )
            return result
        except Exception:
            return None

    async def delete_resource(self, schedule_id: str, resource_index: int) -> dict[str, Any] | None:
        """Delete a resource at a specific index from a schedule."""
        try:
            # First, get the current schedule to validate index
            schedule = await self.find_by_id(schedule_id)
            if not schedule:
                return None

            resources = schedule.get("resources", [])
            if resource_index < 0 or resource_index >= len(resources):
                return None

            # Remove the resource at the specified index
            resources.pop(resource_index)

            result = await self.collection.find_one_and_update(
                {"_id": ObjectId(schedule_id)},
                {
                    "$set": {
                        "resources": resources,
                        "updated_at": ObjectId().generation_time,
                    }
                },
                return_document=True,
            )
            return result
        except Exception:
            return None

    async def get_resources(self, schedule_id: str) -> list[dict[str, Any]] | None:
        """Get all resources for a schedule."""
        try:
            schedule = await self.find_by_id(schedule_id)
            if not schedule:
                return None
            resources: list[dict[str, Any]] = schedule.get("resources", [])
            return resources
        except Exception:
            return None
