"""Authentication request/response schemas."""

from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field

from app.domain.users.value_objects import UserRole


class SignupRequest(BaseModel):
    """Request to create a new user account."""

    email: EmailStr = Field(...)
    password: str = Field(min_length=8, max_length=100)
    name: str = Field(min_length=1, max_length=200)


class LoginRequest(BaseModel):
    """Request to authenticate and receive a JWT token."""

    email: EmailStr = Field(...)
    password: str = Field(...)


class LoginResponse(BaseModel):
    """Response after successful authentication."""

    access_token: str = Field(...)
    token_type: str = Field(default="bearer")
    user_id: str = Field(...)
    email: str = Field(...)
    name: str = Field(...)
    role: UserRole = Field(...)


class ChangePasswordRequest(BaseModel):
    """Request to change user password."""

    current_password: str = Field(..., description="Current password for verification")
    new_password: str = Field(min_length=8, max_length=100, description="New password")


class UpdateProfileRequest(BaseModel):
    """Request to update user profile information."""

    name: str = Field(min_length=1, max_length=200, description="Updated user name")


class ForgotPasswordRequest(BaseModel):
    """Request to initiate password reset flow."""

    email: EmailStr = Field(..., description="Email address to send reset link")


class ResetPasswordRequest(BaseModel):
    """Request to reset password with token."""

    token: str = Field(..., description="Password reset token from email")
    new_password: str = Field(min_length=8, max_length=100, description="New password")


class MessageResponse(BaseModel):
    """Generic message response."""

    message: str = Field(..., description="Response message")
