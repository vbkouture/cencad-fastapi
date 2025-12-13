
import json
import sys
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator

# --- Copied DTOs ---

class SyllabusWeekDTO(BaseModel):
    """DTO for a week in course syllabus."""

    week: str = Field(min_length=1, max_length=100, description="Week identifier")
    title: str = Field(min_length=1, max_length=200, description="Week title")
    topics: list[str] = Field(description="Topics covered in this week")

    @field_validator("topics")
    @classmethod
    def validate_topics(cls, v: list[str]) -> list[str]:
        """Validate topics list."""
        if len(v) > 50:
            raise ValueError("Topics must have 0-50 items")
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

# --- Copied Mapping Logic ---

def _course_doc_to_response(course_doc: dict[str, Any]) -> CourseResponse:
    """Convert a course document from DB to CourseResponse DTO."""
    # job_role_ids are already strings in the database
    job_role_ids = course_doc.get("job_role_ids") or []

    # Build CourseDetailsDTO
    course_details_data = course_doc.get("course_details", {})
    syllabus_weeks = []
    for w in course_details_data.get("syllabus", []):
        syllabus_weeks.append(
            SyllabusWeekDTO(
                week=w.get("week", "1"), title=w.get("title", ""), topics=w.get("topics", [])
            )
        )

    course_details = CourseDetailsDTO(
        overview=course_details_data.get("overview", ""),
        objectives=course_details_data.get("objectives", []),
        prerequisites=course_details_data.get("prerequisites", []),
        syllabus=syllabus_weeks,
    )

    created_at = course_doc.get("created_at")
    if not created_at:
        created_at = datetime.now()

    updated_at = course_doc.get("updated_at")
    if not updated_at:
        updated_at = datetime.now()

    return CourseResponse(
        id=str(course_doc.get("_id", "")),
        title=course_doc.get("title", "Untitled Course"),
        description=course_doc.get("description", "No description available"),
        duration=course_doc.get("duration", "N/A"),
        level=course_doc.get("level", "BEGINNER"),
        url=course_doc.get("url"),
        language=course_doc.get("language"),
        image=course_doc.get("image"),
        rating=course_doc.get("rating"),
        students=course_doc.get("students"),
        certifications=course_doc.get("certifications", []),
        cost=course_doc.get("cost"),
        category_id=str(course_doc.get("category_id")) if course_doc.get("category_id") else None,
        vendor_id=str(course_doc.get("vendor_id")) if course_doc.get("vendor_id") else None,
        job_role_ids=job_role_ids,
        resources=[
            ResourceDTO(**r) for r in course_doc.get("resources", [])
        ],
        notice=course_doc.get("notice"),
        tags=course_doc.get("tags", []),
        status=course_doc.get("status", "DRAFT"),
        course_details=course_details,
        created_at=created_at,
        updated_at=updated_at,
    )

def main():
    try:
        with open('seed/courses.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print("seed/courses.json not found")
        sys.exit(1)

    print(f"Loaded {len(data)} courses from seed.")

    for i, course in enumerate(data):
        print(f"Processing course {i+1}: {course.get('title')}")
        try:
            # Simulate date addition by seed script
            course['created_at'] = datetime.now()
            course['updated_at'] = datetime.now()
            _course_doc_to_response(course)
            print("  OK")
        except Exception as e:
            print(f"  FAILED: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    main()
