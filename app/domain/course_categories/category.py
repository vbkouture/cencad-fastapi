"""Course Category aggregate root.

Represents a course category in the system.
"""

from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, Field
from pydantic.config import ConfigDict


def utcnow() -> datetime:
    """Get current UTC time."""
    return datetime.now(UTC)


class CourseCategory(BaseModel):
    """Course category aggregate root."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str = Field(...)
    name: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1, max_length=1000)
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    @classmethod
    def create(
        cls,
        id: str,
        name: str,
        description: str,
    ) -> CourseCategory:
        """Create a new course category."""
        now = utcnow()
        return cls(
            id=id,
            name=name,
            description=description,
            created_at=now,
            updated_at=now,
        )
