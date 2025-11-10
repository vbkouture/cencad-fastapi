"""Assignment management endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.dependencies import get_current_user_id, require_student, require_tutor
from app.domain.users.value_objects import UserRole

router = APIRouter(prefix="/assignments", tags=["assignments"])


@router.get("/my-assignments")
async def get_my_assignments(
    user_id: str = Depends(get_current_user_id),
    _: UserRole = Depends(require_student),
) -> dict[str, str | list[dict[str, str]]]:
    """
    Get assignments for current user.

    Requires student or higher role.
    """
    return {"user_id": user_id, "assignments": []}


@router.post("")
async def create_assignment(
    user_id: str = Depends(get_current_user_id),
    _: UserRole = Depends(require_tutor),
) -> dict[str, str]:
    """
    Create a new assignment.

    Requires tutor or admin role.
    """
    return {"message": "Assignment created", "created_by": user_id}


@router.get("/{assignment_id}")
async def get_assignment(
    assignment_id: str,
    user_id: str = Depends(get_current_user_id),
) -> dict[str, str]:
    """
    Get assignment details.

    Requires authentication.
    """
    return {"assignment_id": assignment_id, "requested_by": user_id}


@router.put("/{assignment_id}")
async def update_assignment(
    assignment_id: str,
    user_id: str = Depends(get_current_user_id),
    _: UserRole = Depends(require_tutor),
) -> dict[str, str]:
    """
    Update assignment details.

    Requires tutor or admin role.
    """
    return {"message": "Assignment updated", "assignment_id": assignment_id, "updated_by": user_id}


@router.delete("/{assignment_id}")
async def delete_assignment(
    assignment_id: str,
    user_id: str = Depends(get_current_user_id),
    _: UserRole = Depends(require_tutor),
) -> dict[str, str]:
    """
    Delete an assignment.

    Requires tutor or admin role.
    """
    return {"message": "Assignment deleted", "assignment_id": assignment_id, "deleted_by": user_id}


@router.get("/{assignment_id}/submissions")
async def get_assignment_submissions(
    assignment_id: str,
    _: UserRole = Depends(require_tutor),
) -> dict[str, str | list[dict[str, str]]]:
    """
    Get all submissions for an assignment.

    Requires tutor or admin role.
    """
    return {"assignment_id": assignment_id, "submissions": []}


@router.put("/{assignment_id}/submissions/{submission_id}/grade")
async def grade_submission(
    assignment_id: str,
    submission_id: str,
    tutor_id: str = Depends(get_current_user_id),
    _: UserRole = Depends(require_tutor),
) -> dict[str, str]:
    """
    Grade a student submission.

    Requires tutor or admin role.
    """
    return {
        "message": "Submission graded",
        "assignment_id": assignment_id,
        "submission_id": submission_id,
        "graded_by": tutor_id,
    }
