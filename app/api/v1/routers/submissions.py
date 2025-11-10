"""Student submission management endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.dependencies import get_current_user_id, require_student, require_tutor
from app.domain.users.value_objects import UserRole

router = APIRouter(prefix="/submissions", tags=["submissions"])


@router.get("")
async def list_submissions(
    user_id: str = Depends(get_current_user_id),
    _: UserRole = Depends(require_student),
) -> dict[str, str | list[dict[str, str]]]:
    """
    List submissions for current user.

    Requires student or higher role.
    """
    return {"user_id": user_id, "submissions": []}


@router.post("")
async def submit_assignment(
    user_id: str = Depends(get_current_user_id),
    _: UserRole = Depends(require_student),
) -> dict[str, str]:
    """
    Submit an assignment.

    Requires student or higher role.
    """
    return {"message": "Submission created", "submitted_by": user_id}


@router.get("/{submission_id}")
async def get_submission(
    submission_id: str,
    user_id: str = Depends(get_current_user_id),
) -> dict[str, str]:
    """
    Get submission details.

    Requires authentication.
    """
    return {"submission_id": submission_id, "requested_by": user_id}


@router.put("/{submission_id}")
async def update_submission(
    submission_id: str,
    user_id: str = Depends(get_current_user_id),
    _: UserRole = Depends(require_student),
) -> dict[str, str]:
    """
    Update a submission (before grading).

    Requires student or higher role.
    """
    return {"message": "Submission updated", "submission_id": submission_id, "updated_by": user_id}


@router.get("/{submission_id}/feedback")
async def get_submission_feedback(
    submission_id: str,
    user_id: str = Depends(get_current_user_id),
) -> dict[str, str]:
    """
    Get grading feedback for a submission.

    Requires authentication.
    """
    return {"submission_id": submission_id, "feedback": "No feedback yet"}


@router.post("/{submission_id}/comments")
async def add_submission_comment(
    submission_id: str,
    user_id: str = Depends(get_current_user_id),
    _: UserRole = Depends(require_tutor),
) -> dict[str, str]:
    """
    Add a comment to a submission.

    Requires tutor or admin role.
    """
    return {"message": "Comment added", "submission_id": submission_id, "commented_by": user_id}
