"""ContactForm request and response DTOs."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, EmailStr, Field
from pydantic.config import ConfigDict

from app.domain.contact_forms.value_objects import ContactFormStatus


class ContactFormHistoryEntry(BaseModel):
    """History entry for contact form status changes."""

    status: ContactFormStatus
    changed_by: str
    changed_at: datetime
    note: str | None = None


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
    status: ContactFormStatus = Field(description="Current status of the form")
    history: list[ContactFormHistoryEntry] = Field(
        default_factory=list, description="History of status changes"
    )
    created_at: datetime = Field(description="Submission timestamp")
    updated_at: datetime | None = Field(default=None, description="Last update timestamp")

    @classmethod
    def from_document(cls, doc: dict[str, Any]) -> ContactFormResponse:
        """Convert MongoDB document to response model."""
        return cls(
            id=str(doc["_id"]),
            name=doc["name"],
            email=doc["email"],
            subject=doc["subject"],
            message=doc["message"],
            status=doc["status"],
            history=doc.get("history", []),
            created_at=doc["created_at"],
            updated_at=doc.get("updated_at"),
        )


class ContactFormStatusUpdateRequest(BaseModel):
    """Request model for updating contact form status."""

    model_config = ConfigDict(extra="forbid")

    status: ContactFormStatus = Field(description="New status")
    note: str | None = Field(default=None, max_length=1000, description="Optional note")
