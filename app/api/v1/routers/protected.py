"""Example endpoints demonstrating role-based access control."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.dependencies import get_current_user_id, require_admin, require_student, require_tutor
from app.domain.users.value_objects import UserRole

router = APIRouter(prefix="/protected", tags=["protected"])


@router.get("/user-info")
async def get_user_info(user_id: str = Depends(get_current_user_id)) -> dict[str, str]:
    """
    Example protected endpoint requiring any authenticated user.

    Returns the current user's ID.
    """
    return {"message": "Hello", "user_id": user_id}


@router.get("/admin-panel")
async def admin_panel(role: UserRole = Depends(require_admin)) -> dict[str, str]:
    """
    Example protected endpoint requiring admin role only.

    Only users with admin role can access this endpoint.
    """
    return {"message": "Admin panel", "role": role}


@router.get("/tutor-dashboard")
async def tutor_dashboard(role: UserRole = Depends(require_tutor)) -> dict[str, str]:
    """
    Example protected endpoint requiring tutor or admin role.

    Tutors and admins can access this endpoint.
    """
    return {"message": "Tutor dashboard", "role": role}


@router.get("/student-courses")
async def student_courses(role: UserRole = Depends(require_student)) -> dict[str, str]:
    """
    Example protected endpoint requiring student role or higher.

    Students, tutors, and admins can access this endpoint.
    """
    return {"message": "Student courses", "role": role}
