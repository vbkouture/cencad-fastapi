"""Enrollment DTOs for API requests/responses."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class EnrollmentCreateRequest(BaseModel):
    """Request DTO for creating an enrollment."""

    user_id: str = Field(description="User ID")
    schedule_id: str = Field(description="Schedule ID")
    course_id: str = Field(description="Course ID")
    payment_transaction_id: str | None = Field(None, description="Payment transaction ID")


class EnrollmentUpdateRequest(BaseModel):
    """Request DTO for updating an enrollment."""

    status: str | None = Field(
        None, description="Enrollment status (ENROLLED, IN_PROGRESS, COMPLETED, DROPPED)"
    )
    payment_status: str | None = Field(None, description="Payment status (PENDING, PAID, REFUNDED)")
    completed_at: datetime | None = Field(None, description="Completion date")
    grade: float | None = Field(None, ge=0, le=100, description="Grade")
    certificate_url: str | None = Field(None, description="Certificate URL")
    instructor_notes: list[dict[str, Any]] | None = Field(None, description="Instructor notes")


class EnrollmentResponse(BaseModel):
    """Response DTO for enrollment."""

    id: str = Field(description="Enrollment ID")
    user_id: str = Field(description="User ID")
    schedule_id: str = Field(description="Schedule ID")
    course_id: str = Field(description="Course ID")
    status: str = Field(description="Enrollment status")
    payment_status: str = Field(description="Payment status")
    payment_transaction_id: str | None = Field(description="Payment transaction ID")
    enrolled_at: datetime = Field(description="Enrollment date")
    completed_at: datetime | None = Field(description="Completion date")
    grade: float | None = Field(description="Grade")
    certificate_url: str | None = Field(description="Certificate URL")
    instructor_notes: list[dict[str, Any]] = Field(description="Instructor notes")
