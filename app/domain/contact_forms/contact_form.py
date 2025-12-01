"""ContactForm aggregate root.

Represents a contact form submission in the system.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field
from pydantic.config import ConfigDict

from app.domain.users.value_objects import utcnow


class ContactForm(BaseModel):
    """ContactForm aggregate root."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str = Field(...)
    name: str = Field(min_length=1, max_length=200)
    email: EmailStr = Field(...)
    subject: str = Field(min_length=1, max_length=500)
    message: str = Field(min_length=1, max_length=5000)
    created_at: datetime = Field(default_factory=utcnow)

    @classmethod
    def create(
        cls,
        id: str,
        name: str,
        email: str,
        subject: str,
        message: str,
    ) -> ContactForm:
        """Create a new contact form submission."""
        return cls(
            id=id,
            name=name,
            email=email,
            subject=subject,
            message=message,
            created_at=utcnow(),
        )
