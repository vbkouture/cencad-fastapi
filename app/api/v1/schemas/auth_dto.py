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
