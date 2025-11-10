from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field
from pydantic.config import ConfigDict

from app.domain.users.value_objects import UserRole


def _to_camel(s: str) -> str:
    parts = s.split("_")
    return parts[0] + "".join(p.title() for p in parts[1:])


class UserCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    email: EmailStr
    name: str = Field(min_length=1, max_length=200)


class UserUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=200)
    is_active: bool | None = None


class UserOut(BaseModel):
    """HTTP response shape for a User (camelCase)."""

    model_config = ConfigDict(
        alias_generator=_to_camel,
        populate_by_name=True,
        frozen=True,
        extra="forbid",
    )

    id: str
    email: EmailStr
    name: str
    created_at: str  # ISO-8601 string (UTC) for clients
    is_active: bool


class CreateTutorRequest(BaseModel):
    """Request to create a tutor account (admin only)."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    email: EmailStr = Field(...)
    password: str = Field(min_length=8, max_length=100)
    name: str = Field(min_length=1, max_length=200)


class TutorResponse(BaseModel):
    """Response after creating a tutor account."""

    user_id: str = Field(...)
    email: str = Field(...)
    name: str = Field(...)
    role: UserRole = Field(default=UserRole.TUTOR)
