"""User aggregate root.

Represents a user in the system with role-based access control.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field
from pydantic.config import ConfigDict

from .value_objects import UserRole, utcnow


class User(BaseModel):
    """User aggregate root."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str = Field(...)
    email: EmailStr = Field(...)
    name: str = Field(min_length=1, max_length=200)
    hashed_password: str = Field(...)
    role: UserRole = Field(default=UserRole.STUDENT)
    is_active: bool = Field(default=True)
    force_password_change: bool = Field(default=False)
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    @classmethod
    def create(
        cls,
        id: str,
        email: str,
        name: str,
        hashed_password: str,
        role: UserRole = UserRole.STUDENT,
        force_password_change: bool = False,
    ) -> User:
        """Create a new user."""
        now = utcnow()
        return cls(
            id=id,
            email=email,
            name=name,
            hashed_password=hashed_password,
            role=role,
            is_active=True,
            force_password_change=force_password_change,
            created_at=now,
            updated_at=now,
        )
