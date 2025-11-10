"""Course aggregate root."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any


class CourseLevel(str, Enum):
    """Course difficulty levels."""

    BEGINNER = "BEGINNER"
    INTERMEDIATE = "INTERMEDIATE"
    ADVANCED = "ADVANCED"
    EXPERT = "EXPERT"


class SyllabusWeek:
    """Represents a week in the course syllabus."""

    def __init__(
        self,
        week: str,
        title: str,
        topics: list[str],
    ) -> None:
        """
        Initialize a SyllabusWeek.

        Args:
            week: Week number or identifier (e.g., "Week 1")
            title: Week title
            topics: List of topics covered in this week
        """
        self.week = week
        self.title = title
        self.topics = topics

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "week": self.week,
            "title": self.title,
            "topics": self.topics,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SyllabusWeek:
        """Create from dictionary representation."""
        return cls(
            week=data["week"],
            title=data["title"],
            topics=data["topics"],
        )


class CourseDetails:
    """Represents detailed course information."""

    def __init__(
        self,
        overview: str,
        objectives: list[str],
        prerequisites: list[str],
        syllabus: list[SyllabusWeek],
    ) -> None:
        """
        Initialize CourseDetails.

        Args:
            overview: Course overview/description
            objectives: Learning objectives
            prerequisites: Course prerequisites
            syllabus: List of SyllabusWeek objects
        """
        self.overview = overview
        self.objectives = objectives
        self.prerequisites = prerequisites
        self.syllabus = syllabus

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "overview": self.overview,
            "objectives": self.objectives,
            "prerequisites": self.prerequisites,
            "syllabus": [week.to_dict() for week in self.syllabus],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CourseDetails:
        """Create from dictionary representation."""
        syllabus = [
            SyllabusWeek.from_dict(week) for week in data.get("syllabus", [])
        ]
        return cls(
            overview=data["overview"],
            objectives=data["objectives"],
            prerequisites=data.get("prerequisites", []),
            syllabus=syllabus,
        )


class Course:
    """
    Course aggregate.

    Represents a course in the system with detailed information,
    relationships to vendors, job roles, and categories.
    """

    def __init__(
        self,
        id: str,
        title: str,
        description: str,
        duration: str,
        level: CourseLevel,
        course_details: CourseDetails,
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
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ) -> None:
        """
        Initialize a Course.

        Args:
            id: Unique identifier (MongoDB ObjectId as string)
            title: Course title (unique, required)
            description: Course description
            duration: Course duration (e.g., "8 Weeks")
            level: Course difficulty level
            course_details: Detailed course information
            url: Optional course URL
            language: Optional language (e.g., "English", "Spanish")
            image: Optional course image URL
            rating: Optional course rating (0-5)
            students: Optional number of enrolled students
            certifications: Optional list of certification names/codes
            cost: Optional course cost/price
            category_id: Optional reference to course category
            vendor_id: Optional reference to vendor
            job_role_ids: Optional list of related job role IDs
            created_at: Creation timestamp
            updated_at: Last update timestamp
        """
        self.id = id
        self.title = title
        self.description = description
        self.duration = duration
        self.level = level
        self.course_details = course_details
        self.url = url
        self.language = language
        self.image = image
        self.rating = rating
        self.students = students
        self.certifications = certifications or []
        self.cost = cost
        self.category_id = category_id
        self.vendor_id = vendor_id
        self.job_role_ids = job_role_ids or []
        self.created_at = created_at
        self.updated_at = updated_at

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "duration": self.duration,
            "level": self.level.value,
            "url": self.url,
            "language": self.language,
            "image": self.image,
            "rating": self.rating,
            "students": self.students,
            "certifications": self.certifications,
            "cost": self.cost,
            "categoryId": self.category_id,
            "vendorId": self.vendor_id,
            "jobRoleIds": self.job_role_ids,
            "courseDetails": self.course_details.to_dict(),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
