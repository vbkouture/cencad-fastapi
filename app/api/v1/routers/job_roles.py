"""Job roles endpoints: CRUD operations with role-based access control."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer

from app.api.v1.schemas.job_role_dto import (
    JobRoleCreateRequest,
    JobRoleResponse,
    JobRoleUpdateRequest,
)
from app.core.dependencies import require_admin
from app.db import get_database
from app.db.job_role_repository import JobRoleRepository

router = APIRouter(prefix="/job-roles", tags=["job-roles"])
security = HTTPBearer(auto_error=False)


@router.get("", response_model=list[JobRoleResponse])
async def get_all_job_roles() -> list[JobRoleResponse]:
    """
    Get all job roles.

    No authentication required - anyone can read job roles.

    Returns:
        List of all job roles.
    """
    db = get_database()
    repo = JobRoleRepository(db)

    job_roles = await repo.get_all_job_roles()

    return [
        JobRoleResponse(
            id=str(job_role["_id"]),
            name=job_role["name"],
            description=job_role["description"],
            created_at=job_role["created_at"],
            updated_at=job_role["updated_at"],
        )
        for job_role in job_roles
    ]


@router.get("/{job_role_id}", response_model=JobRoleResponse)
async def get_job_role(job_role_id: str) -> JobRoleResponse:
    """
    Get a specific job role by ID.

    No authentication required - anyone can read job roles.

    Args:
        job_role_id: MongoDB ObjectId as string

    Returns:
        Job role details.

    Raises:
        HTTPException: If job role not found.
    """
    db = get_database()
    repo = JobRoleRepository(db)

    job_role = await repo.find_by_id(job_role_id)

    if job_role is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job role not found",
        )

    return JobRoleResponse(
        id=str(job_role["_id"]),
        name=job_role["name"],
        description=job_role["description"],
        created_at=job_role["created_at"],
        updated_at=job_role["updated_at"],
    )


@router.post(
    "",
    response_model=JobRoleResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_job_role(
    request: JobRoleCreateRequest,
    _: str = Depends(require_admin),
) -> JobRoleResponse:
    """
    Create a new job role.

    **Admin only** - requires valid JWT token with admin role.

    Args:
        request: Job role creation request with name and description
        _: Admin role requirement (validates JWT token and role)

    Returns:
        Created job role.

    Raises:
        HTTPException: If name already exists or validation fails.
    """
    db = get_database()
    repo = JobRoleRepository(db)

    try:
        job_role = await repo.create_job_role(
            name=request.name,
            description=request.description,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )

    return JobRoleResponse(
        id=str(job_role["_id"]),
        name=job_role["name"],
        description=job_role["description"],
        created_at=job_role["created_at"],
        updated_at=job_role["updated_at"],
    )


@router.put("/{job_role_id}", response_model=JobRoleResponse)
async def update_job_role(
    job_role_id: str,
    request: JobRoleUpdateRequest,
    _: str = Depends(require_admin),
) -> JobRoleResponse:
    """
    Update a job role.

    **Admin only** - requires valid JWT token with admin role.

    Args:
        job_role_id: MongoDB ObjectId as string
        request: Update request with optional name and/or description
        _: Admin role requirement (validates JWT token and role)

    Returns:
        Updated job role.

    Raises:
        HTTPException: If job role not found, validation fails, or name already exists.
    """
    db = get_database()
    repo = JobRoleRepository(db)

    try:
        updated_job_role = await repo.update_job_role(
            job_role_id=job_role_id,
            name=request.name,
            description=request.description,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )

    if updated_job_role is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job role not found",
        )

    return JobRoleResponse(
        id=str(updated_job_role["_id"]),
        name=updated_job_role["name"],
        description=updated_job_role["description"],
        created_at=updated_job_role["created_at"],
        updated_at=updated_job_role["updated_at"],
    )


@router.delete("/{job_role_id}")
async def delete_job_role(
    job_role_id: str,
    _: str = Depends(require_admin),
) -> None:
    """
    Delete a job role.

    **Admin only** - requires valid JWT token with admin role.

    Args:
        job_role_id: MongoDB ObjectId as string
        _: Admin role requirement (validates JWT token and role)

    Raises:
        HTTPException: If job role not found.
    """
    db = get_database()
    repo = JobRoleRepository(db)

    deleted = await repo.delete_job_role(job_role_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job role not found",
        )
