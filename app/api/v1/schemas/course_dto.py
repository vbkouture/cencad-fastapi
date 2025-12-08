"""Course DTOs for API requests/responses."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class SyllabusWeekDTO(BaseModel):
    """DTO for a week in course syllabus."""

    week: str = Field(min_length=1, max_length=100, description="Week identifier")
    title: str = Field(min_length=1, max_length=200, description="Week title")
    topics: list[str] = Field(description="Topics covered in this week")

    @field_validator("topics")
    @classmethod
    def validate_topics(cls, v: list[str]) -> list[str]:
        """Validate topics list."""
        if not v or len(v) > 50:
            raise ValueError("Topics must have 1-50 items")
        return v


class CourseDetailsDTO(BaseModel):
    """DTO for detailed course information."""

    overview: str = Field(default="", max_length=10000, description="Course overview")
    objectives: list[str] = Field(
        default_factory=list,
        description="Learning objectives (optional)",
    )
    prerequisites: list[str] = Field(
        default_factory=list,
        description="Course prerequisites (optional)",
    )
    syllabus: list[SyllabusWeekDTO] = Field(
        default_factory=list,
        description="Course syllabus by week (optional)",
    )

    @field_validator("objectives")
    @classmethod
    def validate_objectives(cls, v: list[str]) -> list[str]:
        """Validate objectives list."""
        if len(v) > 20:
            raise ValueError("Objectives must have 0-20 items")
        return v

    @field_validator("prerequisites")
    @classmethod
    def validate_prerequisites(cls, v: list[str]) -> list[str]:
        """Validate prerequisites list."""
        if len(v) > 20:
            raise ValueError("Prerequisites must have 0-20 items")
        return v

    @field_validator("syllabus")
    @classmethod
    def validate_syllabus(cls, v: list[SyllabusWeekDTO]) -> list[SyllabusWeekDTO]:
        """Validate syllabus list."""
        if len(v) > 52:
            raise ValueError("Syllabus must have 0-52 weeks")
        return v


class ResourceDTO(BaseModel):
    """DTO for course resource."""

    title: str = Field(min_length=1, max_length=200, description="Resource title")
    url: str = Field(min_length=1, max_length=2048, description="Resource URL")


class CourseCreateRequest(BaseModel):
    """Request DTO for creating a course."""

    title: str = Field(min_length=1, max_length=500, description="Course title")
    description: str = Field(min_length=10, max_length=5000, description="Course description")
    duration: str = Field(
        min_length=1, max_length=100, description="Course duration (e.g., '8 Weeks')"
    )
    level: str = Field(description="Course level (BEGINNER, INTERMEDIATE, ADVANCED, EXPERT)")
    course_details: CourseDetailsDTO = Field(description="Detailed course information")
    url: str | None = Field(None, description="Optional course URL")
    language: str | None = Field(None, max_length=50, description="Course language")
    image: str | None = Field(None, max_length=2048, description="Course image URL")
    rating: float | None = Field(None, ge=0, le=5, description="Course rating")
    students: int | None = Field(None, ge=0, description="Number of students")
    certifications: list[str] = Field(
        default_factory=list,
        description="Associated certifications",
    )
    cost: float | None = Field(None, ge=0, description="Course cost/price")
    category_id: str | None = Field(None, description="Optional category ID")
    vendor_id: str | None = Field(None, description="Optional vendor ID")
    job_role_ids: list[str] = Field(default_factory=list, description="Related job role IDs")
    resources: list[ResourceDTO] | None = Field(None, description="Course resources")
    notice: str | None = Field(None, max_length=2000, description="Important notice")
    tags: list[str] | None = Field(None, description="Search tags")
    status: str | None = Field(None, description="Course status (DRAFT, PUBLISHED, ARCHIVED)")

    @field_validator("certifications")
    @classmethod
    def validate_certifications(cls, v: list[str]) -> list[str]:
        """Validate certifications list."""
        if len(v) > 10:
            raise ValueError("Certifications must have 0-10 items")
        return v


class CourseUpdateRequest(BaseModel):
    """Request DTO for updating a course."""

    title: str | None = Field(None, min_length=1, max_length=500, description="Course title")
    description: str | None = Field(
        None, min_length=10, max_length=5000, description="Course description"
    )
    duration: str | None = Field(None, min_length=1, max_length=100, description="Course duration")
    level: str | None = Field(
        None, description="Course level (BEGINNER, INTERMEDIATE, ADVANCED, EXPERT)"
    )
    course_details: CourseDetailsDTO | None = Field(None, description="Detailed course information")
    url: str | None = Field(None, description="Course URL")
    language: str | None = Field(None, max_length=50, description="Course language")
    image: str | None = Field(None, max_length=2048, description="Course image URL")
    rating: float | None = Field(None, ge=0, le=5, description="Course rating")
    students: int | None = Field(None, ge=0, description="Number of students")
    certifications: list[str] | None = Field(None, description="Associated certifications")
    cost: float | None = Field(None, ge=0, description="Course cost/price")
    category_id: str | None = Field(None, description="Category ID")
    vendor_id: str | None = Field(None, description="Vendor ID")
    job_role_ids: list[str] | None = Field(None, description="Related job role IDs")
    resources: list[ResourceDTO] | None = Field(None, description="Course resources")
    notice: str | None = Field(None, max_length=2000, description="Important notice")
    tags: list[str] | None = Field(None, description="Search tags")
    status: str | None = Field(None, description="Course status (DRAFT, PUBLISHED, ARCHIVED)")


class CourseResponse(BaseModel):
    """Response DTO for course."""

    id: str = Field(description="Course ID (MongoDB ObjectId as string)")
    title: str = Field(description="Course title")
    description: str = Field(description="Course description")
    duration: str = Field(description="Course duration")
    level: str = Field(description="Course level")
    url: str | None = Field(description="Course URL")
    language: str | None = Field(description="Course language")
    image: str | None = Field(description="Course image URL")
    rating: float | None = Field(description="Course rating")
    students: int | None = Field(description="Number of students")
    certifications: list[str] = Field(default_factory=list, description="Associated certifications")
    cost: float | None = Field(description="Course cost/price")
    category_id: str | None = Field(description="Category ID")
    vendor_id: str | None = Field(description="Vendor ID")
    job_role_ids: list[str] = Field(default_factory=list, description="Related job role IDs")
    resources: list[ResourceDTO] = Field(default_factory=list, description="Course resources")
    notice: str | None = Field(description="Important notice")
    tags: list[str] = Field(default_factory=list, description="Search tags")
    status: str = Field(description="Course status")
    course_details: CourseDetailsDTO = Field(description="Detailed course information")
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")


class PaginatedCourseResponse(BaseModel):
    """Response DTO for paginated courses list."""

    data: list[CourseResponse] = Field(description="List of courses")
    total: int = Field(description="Total number of courses matching filters")
    skip: int = Field(description="Number of results skipped (offset)")
    limit: int = Field(description="Number of results in this page")
    pages: int = Field(description="Total number of pages")
