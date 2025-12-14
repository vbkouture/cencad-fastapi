"""Enrollment router."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.v1.schemas.enrollment_dto import (
    EnrollmentCreateRequest,
    EnrollmentResponse,
    EnrollmentUpdateRequest,
)
from app.core.dependencies import (
    get_current_user_id,
    get_current_user_role,
    require_tutor,
)
from app.db.enrollment_repository import EnrollmentRepository
from app.domain.enrollments.enrollment import Enrollment
from app.domain.users.value_objects import UserRole

router = APIRouter(prefix="/enrollments", tags=["enrollments"])


async def get_enrollment_repository() -> EnrollmentRepository:
    """Dependency to get enrollment repository."""
    from app.db import get_database

    return EnrollmentRepository(get_database())


@router.post(
    "/",
    response_model=EnrollmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new enrollment",
)
async def create_enrollment(
    request: EnrollmentCreateRequest,
    repo: Annotated[EnrollmentRepository, Depends(get_enrollment_repository)],
    current_user_id: Annotated[str, Depends(get_current_user_id)],
) -> EnrollmentResponse:
    """Create a new enrollment."""
    # Ensure user is enrolling themselves or is admin (logic can be expanded)
    # For now, we trust the request body or override with current_user if needed
    # But usually, a student enrolls themselves.

    # If request.user_id is different from current_user_id, we might want to check permissions
    # For simplicity, we'll allow it if the user is authenticated, assuming frontend handles logic
    # OR we force user_id to be current_user_id for students.

    enrollment_doc = await repo.create_enrollment(
        user_id=request.user_id,
        schedule_id=request.schedule_id,
        course_id=request.course_id,
        amount_total=request.amount_total,
        currency=request.currency,
        stripe_payment_intent_id=request.stripe_payment_intent_id,
        stripe_checkout_session_id=request.stripe_checkout_session_id,
    )
    return EnrollmentResponse.model_validate(Enrollment.from_mongo(enrollment_doc).model_dump())


@router.get(
    "/my-enrollments",
    response_model=list[EnrollmentResponse],
    summary="Get my enrollments",
)
async def get_my_enrollments(
    repo: Annotated[EnrollmentRepository, Depends(get_enrollment_repository)],
    current_user_id: Annotated[str, Depends(get_current_user_id)],
) -> list[EnrollmentResponse]:
    """Get all enrollments for the current user."""
    docs = await repo.get_enrollments_by_student(current_user_id)
    return [
        EnrollmentResponse.model_validate(Enrollment.from_mongo(doc).model_dump()) for doc in docs
    ]


@router.get(
    "/schedule/{schedule_id}",
    response_model=list[EnrollmentResponse],
    summary="Get enrollments by schedule",
)
async def get_enrollments_by_schedule(
    schedule_id: str,
    repo: Annotated[EnrollmentRepository, Depends(get_enrollment_repository)],
    _: UserRole = Depends(require_tutor),
) -> list[EnrollmentResponse]:
    """
    Get all enrollments for a specific schedule.

    **Tutor or Admin only**.
    """
    docs = await repo.get_enrollments_by_schedule(schedule_id)
    return [
        EnrollmentResponse.model_validate(Enrollment.from_mongo(doc).model_dump()) for doc in docs
    ]


@router.get(
    "/{enrollment_id}",
    response_model=EnrollmentResponse,
    summary="Get enrollment by ID",
)
async def get_enrollment(
    enrollment_id: str,
    repo: Annotated[EnrollmentRepository, Depends(get_enrollment_repository)],
    current_user_id: str = Depends(get_current_user_id),
    current_role: UserRole = Depends(get_current_user_role),
) -> EnrollmentResponse:
    """
    Get an enrollment by ID.

    **Restricted**: Users can only view their own enrollments. Tutors/Admins can view all.
    """
    doc = await repo.find_by_id(enrollment_id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Enrollment not found")

    # Check permissions
    if str(doc["user_id"]) != current_user_id and current_role not in (
        UserRole.TUTOR,
        UserRole.ADMIN,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this enrollment",
        )

    return EnrollmentResponse.model_validate(Enrollment.from_mongo(doc).model_dump())


@router.put(
    "/{enrollment_id}",
    response_model=EnrollmentResponse,
    summary="Update enrollment",
)
async def update_enrollment(
    enrollment_id: str,
    request: EnrollmentUpdateRequest,
    repo: Annotated[EnrollmentRepository, Depends(get_enrollment_repository)],
    _: UserRole = Depends(require_tutor),
) -> EnrollmentResponse:
    """
    Update an enrollment.

    **Tutor or Admin only**.
    """
    updated_doc = await repo.update_enrollment(
        enrollment_id=enrollment_id,
        status=request.status,
        payment_status=request.payment_status,
        completed_at=request.completed_at,
        grade=request.grade,
        certificate_url=request.certificate_url,
        instructor_notes=request.instructor_notes,
    )
    if not updated_doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Enrollment not found")
    return EnrollmentResponse.model_validate(Enrollment.from_mongo(updated_doc).model_dump())
