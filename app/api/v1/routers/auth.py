"""Authentication endpoints: signup and login with MongoDB."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.v1.schemas.auth_dto import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    LoginRequest,
    LoginResponse,
    MessageResponse,
    ResetPasswordRequest,
    SignupRequest,
    UpdateProfileRequest,
)
from app.core.dependencies import get_current_user_id
from app.core.email_service import send_password_reset_email
from app.core.security import (
    create_access_token,
    create_reset_token_expiry,
    generate_reset_token,
    hash_password,
    verify_password,
)
from app.db import UserRepository, get_database
from app.domain.users.value_objects import UserRole

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=LoginResponse, status_code=status.HTTP_201_CREATED)
async def signup(request: SignupRequest) -> LoginResponse:
    """
    Create a new user account.

    - **email**: User email (must be unique)
    - **password**: Password (min 8 characters)
    - **name**: User's full name

    New users are created as **student** by default.
    Admins can promote users to tutor/admin roles using admin endpoints.

    Returns a JWT token and user info on success.
    """
    db = get_database()
    user_repo = UserRepository(db)

    hashed_pwd = hash_password(request.password)

    try:
        # Create new user in MongoDB (always as STUDENT)
        user_doc = await user_repo.create_user(
            email=request.email.lower(),
            name=request.name,
            hashed_password=hashed_pwd,
            role=UserRole.STUDENT,
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    # Convert MongoDB ObjectId to string
    user_id = str(user_doc["_id"])

    # Generate JWT token
    token = create_access_token(data={"sub": user_id, "role": UserRole.STUDENT})

    return LoginResponse(
        access_token=token,
        user_id=user_id,
        email=request.email.lower(),
        name=request.name,
        role=UserRole.STUDENT,
    )


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest) -> LoginResponse:
    """
    Authenticate user and receive JWT token.

    - **email**: User email
    - **password**: User password

    Returns a JWT token and user info on successful authentication.
    """
    db = get_database()
    user_repo = UserRepository(db)

    # Find user by email in MongoDB
    user_doc = await user_repo.find_by_email(request.email)

    if user_doc is None or not user_doc.get("is_active"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    # Verify password
    if not verify_password(request.password, user_doc["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    # Convert MongoDB ObjectId to string
    user_id = str(user_doc["_id"])

    # Generate JWT token
    token = create_access_token(data={"sub": user_id, "role": user_doc["role"]})

    return LoginResponse(
        access_token=token,
        user_id=user_id,
        email=user_doc["email"],
        name=user_doc["name"],
        role=UserRole(user_doc["role"]),
    )


@router.post("/change-password", response_model=MessageResponse)
async def change_password(
    request: ChangePasswordRequest,
    current_user_id: str = Depends(get_current_user_id),
) -> MessageResponse:
    """
    Change user password (requires authentication).

    - **current_password**: Current password for verification
    - **new_password**: New password (min 8 characters)

    Returns success message on password change.
    """
    db = get_database()
    user_repo = UserRepository(db)

    # Get user document
    user_doc = await user_repo.find_by_id(current_user_id)
    if not user_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Verify current password
    if not verify_password(request.current_password, user_doc["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect",
        )

    # Hash new password
    new_hashed_password = hash_password(request.new_password)

    # Update password
    success = await user_repo.update_password(current_user_id, new_hashed_password)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update password",
        )

    return MessageResponse(message="Password changed successfully")


@router.patch("/profile", response_model=MessageResponse)
async def update_profile(
    request: UpdateProfileRequest,
    current_user_id: str = Depends(get_current_user_id),
) -> MessageResponse:
    """
    Update user profile information (requires authentication).

    - **name**: Updated user name

    Returns success message on profile update.
    """
    db = get_database()
    user_repo = UserRepository(db)

    # Update name
    success = await user_repo.update_name(current_user_id, request.name)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update profile",
        )

    return MessageResponse(message="Profile updated successfully")


@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(request: ForgotPasswordRequest) -> MessageResponse:
    """
    Request password reset email.

    - **email**: Email address to send reset link

    Returns success message (always, even if email doesn't exist for security).
    """
    db = get_database()
    user_repo = UserRepository(db)

    # Find user by email
    user_doc = await user_repo.find_by_email(request.email)

    # Always return success to prevent email enumeration
    if user_doc:
        # Generate reset token
        reset_token = generate_reset_token()
        expires_at = create_reset_token_expiry()

        # Store token in database
        await user_repo.create_password_reset_token(
            user_id=str(user_doc["_id"]),
            token=reset_token,
            expires_at=expires_at,
        )

        # Send reset email
        await send_password_reset_email(
            recipient_email=user_doc["email"],
            recipient_name=user_doc["name"],
            reset_token=reset_token,
        )

    return MessageResponse(message="If the email exists, a password reset link has been sent")


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(request: ResetPasswordRequest) -> MessageResponse:
    """
    Reset password using token from email.

    - **token**: Password reset token from email
    - **new_password**: New password (min 8 characters)

    Returns success message on password reset.
    """
    db = get_database()
    user_repo = UserRepository(db)

    # Find valid token
    token_doc = await user_repo.find_password_reset_token(request.token)
    if not token_doc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )

    # Hash new password
    new_hashed_password = hash_password(request.new_password)

    # Update password
    success = await user_repo.update_password(
        token_doc["user_id"],
        new_hashed_password,
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset password",
        )

    # Mark token as used
    await user_repo.delete_password_reset_token(request.token)

    return MessageResponse(message="Password reset successfully")
