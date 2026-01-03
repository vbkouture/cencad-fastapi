"""Schedule router."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.v1.schemas.schedule_dto import (
    PublicScheduleResponse,
    ResourceCreateRequest,
    ResourceDTO,
    ResourceUpdateRequest,
    ScheduleCreateRequest,
    ScheduleResponse,
    ScheduleUpdateRequest,
    SessionDTO,
)
from app.core.dependencies import (
    get_current_user_id,
    get_current_user_role,
    require_admin,
    require_tutor,
)
from app.db.schedule_repository import ScheduleRepository
from app.domain.schedules.schedule import Schedule
from app.domain.users.value_objects import UserRole

router = APIRouter(prefix="/schedules", tags=["schedules"])


async def get_schedule_repository() -> ScheduleRepository:
    """Dependency to get schedule repository."""
    from app.db import get_database

    return ScheduleRepository(get_database())


@router.post(
    "/",
    response_model=ScheduleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new schedule",
)
async def create_schedule(
    request: ScheduleCreateRequest,
    repo: Annotated[ScheduleRepository, Depends(get_schedule_repository)],
    _: UserRole = Depends(require_admin),
) -> ScheduleResponse:
    """
    Create a new schedule.

    **Admin only**.
    """
    schedule_doc = await repo.create_schedule(
        course_id=request.course_id,
        tutor_id=request.tutor_id,
        sessions=[s.model_dump() for s in request.sessions],
        capacity=request.capacity,
        meeting_url=request.meeting_url,
        timezone=request.timezone,
    )
    return ScheduleResponse.model_validate(Schedule.from_mongo(schedule_doc).model_dump())


@router.get(
    "/upcoming-schedule",
    response_model=list[PublicScheduleResponse],
    summary="Get upcoming schedules",
)
async def get_upcoming_schedules(
    repo: Annotated[ScheduleRepository, Depends(get_schedule_repository)],
    course_id: str | None = Query(None, description="Filter by course ID"),
    tutor_id: str | None = Query(None, description="Filter by tutor ID"),
) -> list[PublicScheduleResponse]:
    """
    Get upcoming schedules.

    Public endpoint.
    Only returns UPCOMING sessions.
    """
    docs = await repo.get_upcoming_schedules(course_id=course_id, tutor_id=tutor_id)

    # helper to map doc to PublicScheduleResponse
    # helper to map doc to PublicScheduleResponse
    results = []
    for doc in docs:
        schedule = Schedule.from_mongo(doc)
        results.append(
            PublicScheduleResponse(
                id=schedule.id,
                course_id=schedule.course_id,
                sessions=[SessionDTO.model_validate(s.model_dump()) for s in schedule.sessions],
                capacity=schedule.capacity,
                timezone=schedule.timezone,
            )
        )

    return results


@router.get(
    "/my-schedules",
    response_model=list[ScheduleResponse],
    summary="Get my schedules (tutor)",
)
async def get_my_schedules(
    repo: Annotated[ScheduleRepository, Depends(get_schedule_repository)],
    current_user_id: str = Depends(get_current_user_id),
    _: UserRole = Depends(require_tutor),
) -> list[ScheduleResponse]:
    """
    Get schedules for the currently authenticated tutor.

    **Tutor only** - Returns all schedules where the tutor is assigned.
    """
    docs = await repo.get_schedules_by_tutor(current_user_id)
    return [ScheduleResponse.model_validate(Schedule.from_mongo(doc).model_dump()) for doc in docs]


@router.get(
    "/{schedule_id}",
    response_model=ScheduleResponse,
    summary="Get schedule by ID",
)
async def get_schedule(
    schedule_id: str,
    repo: Annotated[ScheduleRepository, Depends(get_schedule_repository)],
) -> ScheduleResponse:
    """Get a schedule by ID."""
    schedule_doc = await repo.find_by_id(schedule_id)
    if not schedule_doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Schedule not found")
    return ScheduleResponse.model_validate(Schedule.from_mongo(schedule_doc).model_dump())


@router.get(
    "/",
    response_model=list[ScheduleResponse],
    summary="Get schedules",
)
async def get_schedules(
    repo: Annotated[ScheduleRepository, Depends(get_schedule_repository)],
    _: UserRole = Depends(require_admin),
    course_id: str | None = Query(None, description="Filter by course ID"),
    tutor_id: str | None = Query(None, description="Filter by tutor ID"),
) -> list[ScheduleResponse]:
    """Get schedules, optionally filtered by course or tutor."""
    if course_id:
        docs = await repo.get_schedules_by_course(course_id)
    elif tutor_id:
        docs = await repo.get_schedules_by_tutor(tutor_id)
    else:
        # Return all schedules if no filter provided
        docs = await repo.get_all_schedules()

    return [ScheduleResponse.model_validate(Schedule.from_mongo(doc).model_dump()) for doc in docs]


@router.put(
    "/{schedule_id}",
    response_model=ScheduleResponse,
    summary="Update schedule",
)
async def update_schedule(
    schedule_id: str,
    request: ScheduleUpdateRequest,
    repo: Annotated[ScheduleRepository, Depends(get_schedule_repository)],
    _: UserRole = Depends(require_admin),
) -> ScheduleResponse:
    """
    Update a schedule.

    **Admin only**.
    """
    updated_doc = await repo.update_schedule(
        schedule_id=schedule_id,
        tutor_id=request.tutor_id,
        sessions=[s.model_dump() for s in request.sessions] if request.sessions else None,
        capacity=request.capacity,
        status=request.status,
        meeting_url=request.meeting_url,
        timezone=request.timezone,
    )
    if not updated_doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Schedule not found")
    return ScheduleResponse.model_validate(Schedule.from_mongo(updated_doc).model_dump())


@router.delete(
    "/{schedule_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete schedule",
)
async def delete_schedule(
    schedule_id: str,
    repo: Annotated[ScheduleRepository, Depends(get_schedule_repository)],
    _: UserRole = Depends(require_admin),
) -> None:
    """
    Delete a schedule.

    **Admin only**.
    """
    deleted = await repo.delete_schedule(schedule_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Schedule not found")


# Resource CRUD endpoints


async def verify_schedule_access(
    schedule_id: str,
    user_id: str,
    role: UserRole,
    repo: ScheduleRepository,
) -> dict[str, Any]:
    """
    Verify that the user has access to modify resources on a schedule.

    Returns the schedule if access is granted.
    Raises HTTPException if access is denied or schedule not found.
    """
    schedule_doc = await repo.find_by_id(schedule_id)
    if not schedule_doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Schedule not found")

    # Allow if admin
    if role == UserRole.ADMIN:
        return schedule_doc

    # Allow if the user is the assigned tutor
    tutor_id = str(schedule_doc.get("tutor_id", ""))
    if tutor_id == user_id:
        return schedule_doc

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Only admins or the assigned tutor can modify resources",
    )


@router.get(
    "/{schedule_id}/resources",
    response_model=list[ResourceDTO],
    summary="Get resources for a schedule",
)
async def get_schedule_resources(
    schedule_id: str,
    repo: Annotated[ScheduleRepository, Depends(get_schedule_repository)],
) -> list[ResourceDTO]:
    """
    Get all resources for a schedule.

    **Public endpoint**.
    """
    resources = await repo.get_resources(schedule_id)
    if resources is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Schedule not found")
    return [ResourceDTO.model_validate(r) for r in resources]


@router.post(
    "/{schedule_id}/resources",
    response_model=ResourceDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Add a resource to a schedule",
)
async def add_schedule_resource(
    schedule_id: str,
    request: ResourceCreateRequest,
    repo: Annotated[ScheduleRepository, Depends(get_schedule_repository)],
    current_user_id: str = Depends(get_current_user_id),
    current_role: UserRole = Depends(get_current_user_role),
) -> ResourceDTO:
    """
    Add a resource to a schedule.

    **Admin or assigned tutor only**.
    """
    await verify_schedule_access(schedule_id, current_user_id, current_role, repo)

    resource_data = request.model_dump()
    updated_doc = await repo.add_resource(schedule_id, resource_data)
    if not updated_doc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to add resource"
        )

    # Return the newly added resource (last one in the list)
    resources = updated_doc.get("resources", [])
    return ResourceDTO.model_validate(resources[-1])


@router.put(
    "/{schedule_id}/resources/{resource_index}",
    response_model=ResourceDTO,
    summary="Update a resource in a schedule",
)
async def update_schedule_resource(
    schedule_id: str,
    resource_index: int,
    request: ResourceUpdateRequest,
    repo: Annotated[ScheduleRepository, Depends(get_schedule_repository)],
    current_user_id: str = Depends(get_current_user_id),
    current_role: UserRole = Depends(get_current_user_role),
) -> ResourceDTO:
    """
    Update a resource at a specific index in a schedule.

    **Admin or assigned tutor only**.
    """
    schedule_doc = await verify_schedule_access(schedule_id, current_user_id, current_role, repo)

    # Validate index
    resources = schedule_doc.get("resources", [])
    if resource_index < 0 or resource_index >= len(resources):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found")

    update_data = request.model_dump(exclude_none=True)
    updated_doc = await repo.update_resource(schedule_id, resource_index, update_data)
    if not updated_doc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update resource"
        )

    # Return the updated resource
    updated_resources = updated_doc.get("resources", [])
    return ResourceDTO.model_validate(updated_resources[resource_index])


@router.delete(
    "/{schedule_id}/resources/{resource_index}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a resource from a schedule",
)
async def delete_schedule_resource(
    schedule_id: str,
    resource_index: int,
    repo: Annotated[ScheduleRepository, Depends(get_schedule_repository)],
    current_user_id: str = Depends(get_current_user_id),
    current_role: UserRole = Depends(get_current_user_role),
) -> None:
    """
    Delete a resource at a specific index from a schedule.

    **Admin or assigned tutor only**.
    """
    schedule_doc = await verify_schedule_access(schedule_id, current_user_id, current_role, repo)

    # Validate index
    resources = schedule_doc.get("resources", [])
    if resource_index < 0 or resource_index >= len(resources):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found")

    deleted_doc = await repo.delete_resource(schedule_id, resource_index)
    if not deleted_doc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete resource"
        )
