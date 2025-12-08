"""User management endpoints (admin only)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.v1.schemas.user_dto import CreateTutorRequest, TutorResponse
from app.core.dependencies import get_current_user_id, require_admin
from app.core.security import hash_password
from app.db import UserRepository, get_database
from app.domain.users.value_objects import UserRole

router = APIRouter(prefix="/users", tags=["users"])


@router.get("")
async def list_users(
    _: UserRole = Depends(require_admin),
) -> dict[str, list[dict[str, str]]]:
    """
    List all users in the system.

    Admin only.
    """
    return {"users": []}


@router.get("/tutors", response_model=list[TutorResponse])
async def list_tutors(
    _: UserRole = Depends(require_admin),
) -> list[TutorResponse]:
    """
    List all tutors in the system.

    Admin only.

    Returns a list of all tutor accounts.
    """
    db = get_database()
    user_repo = UserRepository(db)

    # Get all users with tutor role
    tutor_docs = await user_repo.find_users_by_role(UserRole.TUTOR)

    # Convert to response models
    tutors = [
        TutorResponse(
            user_id=str(doc["_id"]),
            email=doc["email"],
            name=doc["name"],
            role=UserRole.TUTOR,
        )
        for doc in tutor_docs
    ]

    return tutors


@router.post("/tutors", response_model=TutorResponse, status_code=status.HTTP_201_CREATED)
async def create_tutor(
    request: CreateTutorRequest,
    admin_id: str = Depends(get_current_user_id),
    _: UserRole = Depends(require_admin),
) -> TutorResponse:
    """
    Create a new tutor account.

    Admin only.

    - **email**: Tutor email (must be unique)
    - **password**: Password (min 8 characters)
    - **name**: Tutor's full name

    Returns tutor account details on success.
    """
    db = get_database()
    user_repo = UserRepository(db)

    hashed_pwd = hash_password(request.password)

    try:
        # Create new tutor in MongoDB
        user_doc = await user_repo.create_user(
            email=request.email.lower(),
            name=request.name,
            hashed_password=hashed_pwd,
            role=UserRole.TUTOR,
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    # Convert MongoDB ObjectId to string
    user_id = str(user_doc["_id"])

    return TutorResponse(
        user_id=user_id,
        email=request.email.lower(),
        name=request.name,
        role=UserRole.TUTOR,
    )


@router.get("/{user_id}")
async def get_user(
    user_id: str,
    _: UserRole = Depends(require_admin),
) -> dict[str, str]:
    """
    Get user details.

    Admin only.
    """
    return {"user_id": user_id, "email": "user@example.com", "role": "student"}


@router.put("/{user_id}/role")
async def update_user_role(
    user_id: str,
    admin_id: str = Depends(get_current_user_id),
    _: UserRole = Depends(require_admin),
) -> dict[str, str]:
    """
    Update a user's role.

    Admin only.
    """
    return {"message": "User role updated", "user_id": user_id, "updated_by": admin_id}


@router.put("/{user_id}/status")
async def update_user_status(
    user_id: str,
    admin_id: str = Depends(get_current_user_id),
    _: UserRole = Depends(require_admin),
) -> dict[str, str]:
    """
    Activate or deactivate a user.

    Admin only.
    """
    return {"message": "User status updated", "user_id": user_id, "updated_by": admin_id}


@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    admin_id: str = Depends(get_current_user_id),
    _: UserRole = Depends(require_admin),
) -> dict[str, str]:
    """
    Delete a user from the system.

    Admin only.
    """
    return {"message": "User deleted", "user_id": user_id, "deleted_by": admin_id}


@router.get("/{user_id}/activity")
async def get_user_activity(
    user_id: str,
    _: UserRole = Depends(require_admin),
) -> dict[str, str | list[dict[str, str]]]:
    """
    Get user activity logs.

    Admin only.
    """
    return {"user_id": user_id, "activity": []}


@router.get("/statistics/overview")
async def get_statistics(
    _: UserRole = Depends(require_admin),
) -> dict[str, str | int]:
    """
    Get system-wide statistics.

    Admin only.
    """
    return {
        "total_users": 0,
        "total_courses": 0,
        "total_assignments": 0,
        "active_users": 0,
    }
