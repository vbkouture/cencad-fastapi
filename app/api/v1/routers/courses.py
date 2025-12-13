"""Courses endpoints: CRUD operations with role-based access control."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPBearer

from app.api.v1.schemas.course_dto import (
    CourseCreateRequest,
    CourseDetailsDTO,
    CourseResponse,
    CourseUpdateRequest,
    PaginatedCourseResponse,
    ResourceDTO,
    SyllabusWeekDTO,
)
from app.core.dependencies import require_admin
from app.db import get_database
from app.db.course_repository import CourseRepository
from app.domain.courses.course import CourseLevel

router = APIRouter(prefix="/courses", tags=["courses"])
security = HTTPBearer(auto_error=False)


@router.get("", response_model=PaginatedCourseResponse)
async def get_courses(
    category_id: str | None = Query(None, description="Filter by category ID"),
    level: str | None = Query(
        None, description="Filter by course level (BEGINNER, INTERMEDIATE, ADVANCED, EXPERT)"
    ),
    language: str | None = Query(None, description="Filter by language"),
    certifications: list[str] | None = Query(
        None, description="Filter by one or more certifications"
    ),
    job_role_ids: list[str] | None = Query(None, description="Filter by one or more job role IDs"),
    vendor_ids: list[str] | None = Query(None, description="Filter by one or more vendor IDs"),
    skip: int = Query(0, ge=0, description="Number of results to skip (pagination)"),
    limit: int = Query(20, ge=1, le=100, description="Number of results to return (max 100)"),
) -> PaginatedCourseResponse:
    """
    Get courses with optional filters and pagination.

    No authentication required - anyone can read courses.

    Query Parameters:
        category_id: Optional course category ID
        level: Optional course level (BEGINNER, INTERMEDIATE, ADVANCED, EXPERT)
        language: Optional course language
        certifications: Optional list of certification names to filter by
        job_role_ids: Optional list of job role IDs to filter by
        vendor_ids: Optional list of vendor IDs to filter by
        skip: Pagination offset (default 0)
        limit: Pagination limit (default 20, max 100)

    Returns:
        List of courses matching the filters.

    Raises:
        HTTPException: If level is invalid.
    """
    # Validate level if provided
    if level:
        valid_levels = {lvl.value for lvl in CourseLevel}
        if level not in valid_levels:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid level. Must be one of: {', '.join(valid_levels)}",
            )

    db = get_database()
    repo = CourseRepository(db)

    # Build filter dict based on provided parameters
    filters: dict[str, Any] = {}
    if category_id:
        filters["category_id"] = category_id
    if level:
        filters["level"] = level
    if language:
        filters["language"] = language
    if certifications and len(certifications) > 0:
        filters["certifications"] = certifications
    if job_role_ids and len(job_role_ids) > 0:
        filters["job_role_ids"] = job_role_ids
    if vendor_ids and len(vendor_ids) > 0:
        filters["vendor_ids"] = vendor_ids

    # Get all courses first (we'll apply filters in memory for now)
    # TODO: Optimize with database-level filtering
    all_courses = await repo.get_all_courses()

    # Apply filters
    filtered_courses = all_courses

    if filters.get("category_id"):
        filtered_courses = [
            c
            for c in filtered_courses
            if c.get("category_id") and str(c["category_id"]) == filters["category_id"]
        ]

    if filters.get("level"):
        filtered_courses = [c for c in filtered_courses if c.get("level") == filters["level"]]

    if filters.get("language"):
        filtered_courses = [c for c in filtered_courses if c.get("language") == filters["language"]]

    if filters.get("certifications"):
        filtered_courses = [
            c
            for c in filtered_courses
            if any(cert in c.get("certifications", []) for cert in filters["certifications"])
        ]

    if filters.get("job_role_ids"):
        filtered_courses = [
            c
            for c in filtered_courses
            if any(jid in c.get("job_role_ids", []) for jid in filters["job_role_ids"])
        ]

    if filters.get("vendor_ids"):
        filtered_courses = [
            c for c in filtered_courses if c.get("vendor_id") in filters["vendor_ids"]
        ]

    # Apply pagination
    paginated_courses = filtered_courses[skip : skip + limit]

    return PaginatedCourseResponse(
        data=[_course_doc_to_response(course) for course in paginated_courses],
        total=len(filtered_courses),
        skip=skip,
        limit=limit,
        pages=(len(filtered_courses) + limit - 1) // limit,  # Ceiling division
    )


@router.get("/{course_id}", response_model=CourseResponse)
async def get_course(course_id: str) -> CourseResponse:
    """
    Get a specific course by ID.

    No authentication required - anyone can read courses.

    Args:
        course_id: MongoDB ObjectId as string

    Returns:
        Course details.

    Raises:
        HTTPException: If course not found.
    """
    db = get_database()
    repo = CourseRepository(db)

    course = await repo.find_by_id(course_id)

    if course is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found",
        )

    return _course_doc_to_response(course)


@router.post(
    "",
    response_model=CourseResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_course(
    request: CourseCreateRequest,
    _: str = Depends(require_admin),
) -> CourseResponse:
    """
    Create a new course.

    **Admin only** - requires valid JWT token with admin role.

    Args:
        request: Course creation request with all details
        _: Admin role requirement (validates JWT token and role)

    Returns:
        Created course.

    Raises:
        HTTPException: If title already exists or validation fails.
    """
    # Validate level
    valid_levels = {lvl.value for lvl in CourseLevel}
    if request.level not in valid_levels:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid level. Must be one of: {', '.join(valid_levels)}",
        )

    db = get_database()
    repo = CourseRepository(db)

    try:
        course_details_dict = request.course_details.model_dump()
        course = await repo.create_course(
            title=request.title,
            description=request.description,
            duration=request.duration,
            level=request.level,
            course_details=course_details_dict,
            url=request.url,
            language=request.language,
            image=request.image,
            rating=request.rating,
            students=request.students,
            certifications=request.certifications,
            cost=request.cost,
            category_id=request.category_id,
            vendor_id=request.vendor_id,
            job_role_ids=request.job_role_ids,
            resources=[r.model_dump() for r in request.resources] if request.resources else None,
            notice=request.notice,
            tags=request.tags,
            status=request.status or "DRAFT",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )

    return _course_doc_to_response(course)


@router.put("/{course_id}", response_model=CourseResponse)
async def update_course(
    course_id: str,
    request: CourseUpdateRequest,
    _: str = Depends(require_admin),
) -> CourseResponse:
    """
    Update a course.

    **Admin only** - requires valid JWT token with admin role.

    Args:
        course_id: MongoDB ObjectId as string
        request: Update request with optional fields
        _: Admin role requirement (validates JWT token and role)

    Returns:
        Updated course.

    Raises:
        HTTPException: If course not found, validation fails, or title already exists.
    """
    # Validate level if provided
    if request.level:
        valid_levels = {lvl.value for lvl in CourseLevel}
        if request.level not in valid_levels:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid level. Must be one of: {', '.join(valid_levels)}",
            )

    db = get_database()
    repo = CourseRepository(db)

    try:
        course_details_dict = (
            request.course_details.model_dump() if request.course_details else None
        )
        updated_course = await repo.update_course(
            course_id=course_id,
            title=request.title,
            description=request.description,
            duration=request.duration,
            level=request.level,
            course_details=course_details_dict,
            url=request.url,
            language=request.language,
            image=request.image,
            rating=request.rating,
            students=request.students,
            certifications=request.certifications,
            cost=request.cost,
            category_id=request.category_id,
            vendor_id=request.vendor_id,
            job_role_ids=request.job_role_ids,
            resources=[r.model_dump() for r in request.resources] if request.resources else None,
            notice=request.notice,
            tags=request.tags,
            status=request.status,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )

    if updated_course is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found",
        )

    return _course_doc_to_response(updated_course)


@router.delete("/{course_id}")
async def delete_course(
    course_id: str,
    _: str = Depends(require_admin),
) -> None:
    """
    Delete a course.

    **Admin only** - requires valid JWT token with admin role.

    Args:
        course_id: MongoDB ObjectId as string
        _: Admin role requirement (validates JWT token and role)

    Raises:
        HTTPException: If course not found.
    """
    db = get_database()
    repo = CourseRepository(db)

    deleted = await repo.delete_course(course_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found",
        )


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
