"""Schedule router."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.v1.schemas.schedule_dto import (
    ScheduleCreateRequest,
    ScheduleResponse,
    ScheduleUpdateRequest,
)
from app.core.dependencies import require_admin
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
    return Schedule.from_mongo(schedule_doc).model_dump()


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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Schedule not found"
        )
    return Schedule.from_mongo(schedule_doc).model_dump()


@router.get(
    "/",
    response_model=list[ScheduleResponse],
    summary="Get schedules",
)
async def get_schedules(
    repo: Annotated[ScheduleRepository, Depends(get_schedule_repository)],
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

    return [Schedule.from_mongo(doc).model_dump() for doc in docs]


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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Schedule not found"
        )
    return Schedule.from_mongo(updated_doc).model_dump()


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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Schedule not found"
        )
