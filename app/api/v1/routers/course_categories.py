"""Course categories endpoints: CRUD operations with role-based access control."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status, Depends

from app.api.v1.schemas.course_category_dto import (
    CourseCategoryCreateRequest,
    CourseCategoryUpdateRequest,
    CourseCategoryResponse,
)
from app.core.dependencies import require_admin
from app.db import CourseCategoryRepository, get_database
from fastapi.security import HTTPBearer

router = APIRouter(prefix="/course-categories", tags=["course-categories"])
security = HTTPBearer(auto_error=False)


@router.get("", response_model=list[CourseCategoryResponse])
async def get_all_categories() -> list[CourseCategoryResponse]:
    """
    Get all course categories.

    No authentication required - anyone can read course categories.

    Returns:
        List of all course categories.
    """
    db = get_database()
    repo = CourseCategoryRepository(db)

    categories = await repo.get_all_categories()

    return [
        CourseCategoryResponse(
            id=str(category["_id"]),
            name=category["name"],
            description=category["description"],
            created_at=category["created_at"],
            updated_at=category["updated_at"],
        )
        for category in categories
    ]


@router.get("/{category_id}", response_model=CourseCategoryResponse)
async def get_category(category_id: str) -> CourseCategoryResponse:
    """
    Get a specific course category by ID.

    No authentication required - anyone can read course categories.

    Args:
        category_id: MongoDB ObjectId as string

    Returns:
        Course category details.

    Raises:
        HTTPException: If category not found.
    """
    db = get_database()
    repo = CourseCategoryRepository(db)

    category = await repo.find_by_id(category_id)

    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course category not found",
        )

    return CourseCategoryResponse(
        id=str(category["_id"]),
        name=category["name"],
        description=category["description"],
        created_at=category["created_at"],
        updated_at=category["updated_at"],
    )


@router.post(
    "",
    response_model=CourseCategoryResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_category(
    request: CourseCategoryCreateRequest,
    _: str = Depends(require_admin),
) -> CourseCategoryResponse:
    """
    Create a new course category.

    **Admin only** - requires valid JWT token with admin role.

    Args:
        request: Category creation request with name and description
        _: Admin role requirement (validates JWT token and role)

    Returns:
        Created course category.

    Raises:
        HTTPException: If name already exists or validation fails.
    """
    db = get_database()
    repo = CourseCategoryRepository(db)

    try:
        category = await repo.create_category(
            name=request.name,
            description=request.description,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )

    return CourseCategoryResponse(
        id=str(category["_id"]),
        name=category["name"],
        description=category["description"],
        created_at=category["created_at"],
        updated_at=category["updated_at"],
    )


@router.put("/{category_id}", response_model=CourseCategoryResponse)
async def update_category(
    category_id: str,
    request: CourseCategoryUpdateRequest,
    _: str = Depends(require_admin),
) -> CourseCategoryResponse:
    """
    Update a course category.

    **Admin only** - requires valid JWT token with admin role.

    Args:
        category_id: MongoDB ObjectId as string
        request: Update request with optional name and/or description
        _: Admin role requirement (validates JWT token and role)

    Returns:
        Updated course category.

    Raises:
        HTTPException: If category not found, validation fails, or name already exists.
    """
    db = get_database()
    repo = CourseCategoryRepository(db)

    try:
        updated_category = await repo.update_category(
            category_id=category_id,
            name=request.name,
            description=request.description,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )

    if updated_category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course category not found",
        )

    return CourseCategoryResponse(
        id=str(updated_category["_id"]),
        name=updated_category["name"],
        description=updated_category["description"],
        created_at=updated_category["created_at"],
        updated_at=updated_category["updated_at"],
    )


@router.delete("/{category_id}")
async def delete_category(
    category_id: str,
    _: str = Depends(require_admin),
) -> None:
    """
    Delete a course category.

    **Admin only** - requires valid JWT token with admin role.

    Args:
        category_id: MongoDB ObjectId as string
        _: Admin role requirement (validates JWT token and role)

    Raises:
        HTTPException: If category not found.
    """
    db = get_database()
    repo = CourseCategoryRepository(db)

    deleted = await repo.delete_category(category_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course category not found",
        )
