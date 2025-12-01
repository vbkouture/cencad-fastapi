"""Course repository for MongoDB persistence."""

from __future__ import annotations

from typing import Any

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection, AsyncIOMotorDatabase  # type: ignore[import-untyped]


class CourseRepository:
    """Repository for Course aggregate using MongoDB."""

    def __init__(self, db: AsyncIOMotorDatabase) -> None:  # type: ignore[name-defined]
        """Initialize with MongoDB database instance."""
        self.collection: AsyncIOMotorCollection[dict[str, Any]] = db["courses"]  # type: ignore[index,assignment]

    async def create_course(
        self,
        title: str,
        description: str,
        duration: str,
        level: str,
        course_details: dict[str, Any],
        url: str | None = None,
        language: str | None = None,
        image: str | None = None,
        rating: float | None = None,
        students: int | None = None,
        certifications: list[str] | None = None,
        cost: float | None = None,
        category_id: str | None = None,
        vendor_id: str | None = None,
        job_role_ids: list[str] | None = None,
        resources: list[dict[str, str]] | None = None,
        notice: str | None = None,
        tags: list[str] | None = None,
        status: str = "DRAFT",
    ) -> dict[str, Any]:
        """
        Create a new course in the database.

        Args:
            title: Course title (unique)
            description: Course description
            duration: Course duration
            level: Course level
            course_details: Detailed course information
            url: Optional course URL
            language: Optional language
            image: Optional image URL
            rating: Optional rating
            students: Optional student count
            certifications: Optional list of certifications
            cost: Optional cost
            category_id: Optional category ID
            vendor_id: Optional vendor ID
            job_role_ids: Optional list of job role IDs
            resources: Optional list of resources
            notice: Optional notice
            tags: Optional list of tags
            status: Course status

        Returns:
            Created course document with _id

        Raises:
            ValueError: If course with same title already exists
        """
        # Check if course with same title already exists
        existing = await self.collection.find_one({"title": title})
        if existing:
            raise ValueError(f"Course with title '{title}' already exists")

        course_doc: dict[str, Any] = {
            "title": title,
            "description": description,
            "duration": duration,
            "level": level,
            "courseDetails": course_details,
            "url": url,
            "language": language,
            "image": image,
            "rating": rating,
            "students": students,
            "certifications": certifications,
            "cost": cost,
            "categoryId": ObjectId(category_id) if category_id else None,
            "vendorId": ObjectId(vendor_id) if vendor_id else None,
            "jobRoleIds": job_role_ids,
            "resources": resources,
            "notice": notice,
            "tags": tags,
            "status": status,
            "created_at": ObjectId().generation_time,
            "updated_at": ObjectId().generation_time,
        }

        result = await self.collection.insert_one(course_doc)
        course_doc["_id"] = result.inserted_id

        return course_doc

    async def find_by_id(self, course_id: str) -> dict[str, Any] | None:
        """
        Find a course by ID.

        Args:
            course_id: MongoDB ObjectId as string or string ID

        Returns:
            Course document if found, None otherwise
        """
        try:
            # First try as a string ID (current storage format)
            result = await self.collection.find_one({"_id": course_id})
            if result:
                return result
            
            # If not found, try as ObjectId in case of mixed format
            try:
                return await self.collection.find_one({"_id": ObjectId(course_id)})
            except Exception:
                return None
        except Exception:
            return None

    async def find_by_title(self, title: str) -> dict[str, Any] | None:
        """
        Find a course by title.

        Args:
            title: Course title

        Returns:
            Course document if found, None otherwise
        """
        return await self.collection.find_one({"title": title})

    async def get_all_courses(self) -> list[dict[str, Any]]:
        """Get all courses from database."""
        return await self.collection.find().to_list(length=None)  # type: ignore[return-value]

    async def get_courses_by_level(self, level: str) -> list[dict[str, Any]]:
        """
        Get courses by difficulty level.

        Args:
            level: Course level (BEGINNER, INTERMEDIATE, ADVANCED, EXPERT)

        Returns:
            List of courses matching the level
        """
        return await self.collection.find({"level": level}).to_list(length=None)  # type: ignore[return-value]

    async def get_courses_by_category(self, category_id: str) -> list[dict[str, Any]]:
        """
        Get courses by category.

        Args:
            category_id: MongoDB ObjectId as string

        Returns:
            List of courses in this category
        """
        try:
            return await self.collection.find({"categoryId": ObjectId(category_id)}).to_list(length=None)  # type: ignore[return-value]
        except Exception:
            return []

    async def get_courses_by_vendor(self, vendor_id: str) -> list[dict[str, Any]]:
        """
        Get courses by vendor.

        Args:
            vendor_id: MongoDB ObjectId as string

        Returns:
            List of courses from this vendor
        """
        try:
            return await self.collection.find({"vendorId": ObjectId(vendor_id)}).to_list(length=None)  # type: ignore[return-value]
        except Exception:
            return []

    async def get_courses_by_job_role(self, job_role_id: str) -> list[dict[str, Any]]:
        """
        Get courses related to a job role.

        Args:
            job_role_id: Job role ID (as string/UUID)

        Returns:
            List of courses related to this job role
        """
        try:
            return await self.collection.find({"jobRoleIds": job_role_id}).to_list(length=None)  # type: ignore[return-value]
        except Exception:
            return []

    async def update_course(
        self,
        course_id: str,
        title: str | None = None,
        description: str | None = None,
        duration: str | None = None,
        level: str | None = None,
        course_details: dict[str, Any] | None = None,
        url: str | None = None,
        language: str | None = None,
        image: str | None = None,
        rating: float | None = None,
        students: int | None = None,
        certifications: list[str] | None = None,
        cost: float | None = None,
        category_id: str | None = None,
        vendor_id: str | None = None,
        job_role_ids: list[str] | None = None,
        resources: list[dict[str, str]] | None = None,
        notice: str | None = None,
        tags: list[str] | None = None,
        status: str | None = None,
    ) -> dict[str, Any] | None:
        """
        Update a course.

        Args:
            course_id: MongoDB ObjectId as string
            title: New title (optional)
            description: New description (optional)
            duration: New duration (optional)
            level: New level (optional)
            course_details: New course details (optional)
            url: New URL (optional)
            language: New language (optional)
            image: New image URL (optional)
            rating: New rating (optional)
            students: New student count (optional)
            certifications: New certifications (optional)
            cost: New cost (optional)
            category_id: New category ID (optional)
            vendor_id: New vendor ID (optional)
            job_role_ids: New job role IDs (optional)
            resources: New resources (optional)
            notice: New notice (optional)
            tags: New tags (optional)
            status: New status (optional)

        Returns:
            Updated course document if found and updated, None otherwise
        """
        try:
            update_data: dict[str, Any] = {}
            
            if title is not None:
                # Check if new title already exists
                existing = await self.collection.find_one(
                    {"title": title, "_id": {"$ne": ObjectId(course_id)}}
                )
                if existing:
                    raise ValueError(f"Course with title '{title}' already exists")
                update_data["title"] = title

            if description is not None:
                update_data["description"] = description

            if duration is not None:
                update_data["duration"] = duration

            if level is not None:
                update_data["level"] = level

            if course_details is not None:
                update_data["courseDetails"] = course_details

            if url is not None:
                update_data["url"] = url

            if language is not None:
                update_data["language"] = language

            if image is not None:
                update_data["image"] = image

            if rating is not None:
                update_data["rating"] = rating

            if students is not None:
                update_data["students"] = students

            if certifications is not None:
                update_data["certifications"] = certifications

            if cost is not None:
                update_data["cost"] = cost

            if category_id is not None:
                update_data["categoryId"] = ObjectId(category_id) if category_id else None

            if vendor_id is not None:
                update_data["vendorId"] = ObjectId(vendor_id) if vendor_id else None

            if job_role_ids is not None:
                update_data["jobRoleIds"] = job_role_ids

            if resources is not None:
                update_data["resources"] = resources

            if notice is not None:
                update_data["notice"] = notice

            if tags is not None:
                update_data["tags"] = tags

            if status is not None:
                update_data["status"] = status

            if not update_data:
                # No changes to make
                return await self.find_by_id(course_id)

            update_data["updated_at"] = ObjectId().generation_time

            result = await self.collection.find_one_and_update(
                {"_id": ObjectId(course_id)},
                {"$set": update_data},
                return_document=True,
            )
            return result
        except ValueError:
            raise
        except Exception:
            return None

    async def delete_course(self, course_id: str) -> bool:
        """
        Delete a course from database.

        Args:
            course_id: MongoDB ObjectId as string

        Returns:
            True if deleted, False if course not found
        """
        try:
            result = await self.collection.delete_one({"_id": ObjectId(course_id)})
            return result.deleted_count > 0
        except Exception:
            return False

    async def create_indexes(self) -> None:
        """Create necessary database indexes for performance."""
        # Create unique index on title
        await self.collection.create_index("title", unique=True)
        # Index on level for filtering
        await self.collection.create_index("level")
        # Index on categoryId for joins
        await self.collection.create_index("categoryId")
        # Index on vendorId for joins
        await self.collection.create_index("vendorId")
        # Index on jobRoleIds for many-to-many queries
        await self.collection.create_index("jobRoleIds")
        # Index on tags for search
        await self.collection.create_index("tags")
        # Index on status for filtering
        await self.collection.create_index("status")
