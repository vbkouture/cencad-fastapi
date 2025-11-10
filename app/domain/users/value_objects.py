from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import NewType

from pydantic import BaseModel, EmailStr, Field
from pydantic.config import ConfigDict

UserId = NewType("UserId", str)


class UserRole(str, Enum):
    """Enumeration of user roles in the system."""

    ADMIN = "admin"
    TUTOR = "tutor"
    STUDENT = "student"


class EmailAddress(BaseModel):
    """Value object that ensures lowercase normalized emails."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    value: EmailStr = Field(alias="email")

    @property
    def email(self) -> str:
        return str(self.value)

    @classmethod
    def normalize(cls, email: str) -> "EmailAddress":
        # EmailStr validates; we then lowercase for canonical form
        return cls(email=email.lower())


def utcnow() -> datetime:
    return datetime.now(timezone.utc)
