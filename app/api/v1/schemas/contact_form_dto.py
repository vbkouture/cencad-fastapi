"""ContactForm request and response DTOs."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field
from pydantic.config import ConfigDict


class ContactFormRequest(BaseModel):
    """Request model for creating a contact form."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=200, description="Submitter's name")
    email: EmailStr = Field(description="Submitter's email")
    subject: str = Field(min_length=1, max_length=500, description="Contact form subject")
    message: str = Field(min_length=1, max_length=5000, description="Contact form message")


class ContactFormResponse(BaseModel):
    """Response model for contact form."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(description="Contact form ID")
    name: str = Field(description="Submitter's name")
    email: EmailStr = Field(description="Submitter's email")
    subject: str = Field(description="Contact form subject")
    message: str = Field(description="Contact form message")
    created_at: datetime = Field(description="Submission timestamp")

    @classmethod
    def from_document(cls, doc: dict[str, any]) -> ContactFormResponse:  # type: ignore[name-defined]
        """Convert MongoDB document to response model."""
        return cls(
            id=str(doc["_id"]),
            name=doc["name"],
            email=doc["email"],
            subject=doc["subject"],
            message=doc["message"],
            created_at=doc["created_at"],
        )
