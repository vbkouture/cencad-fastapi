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

    # Optional payment info if available at creation time
    amount_total: int | None = Field(None, description="Total amount in cents")
    currency: str = Field("cad", description="Currency code")
    stripe_payment_intent_id: str | None = Field(None, description="Stripe Payment Intent ID")
    stripe_checkout_session_id: str | None = Field(None, description="Stripe Checkout Session ID")


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

    # Checkouts / Payment details
    amount_total: int | None = Field(description="Total amount in cents")
    currency: str = Field(description="Currency code")
    payment_status: str = Field(description="Payment status")
    payment_method_type: str | None = Field(description="Payment method type")
    receipt_email: str | None = Field(description="Receipt email")

    # Stripe Identifiers
    stripe_checkout_session_id: str | None = Field(description="Stripe Checkout Session ID")
    stripe_payment_intent_id: str | None = Field(description="Stripe Payment Intent ID")
    stripe_customer_id: str | None = Field(description="Stripe Customer ID")
    stripe_charge_id: str | None = Field(description="Stripe Charge ID")

    # Timestamps
    created_at: datetime = Field(description="Creation date")
    paid_at: datetime | None = Field(description="Payment date")
    enrolled_at: datetime = Field(description="Enrollment date")
    completed_at: datetime | None = Field(description="Completion date")

    # Metadata
    grade: float | None = Field(description="Grade")
    certificate_url: str | None = Field(description="Certificate URL")
    instructor_notes: list[dict[str, Any]] = Field(description="Instructor notes")
    failure_message: str | None = Field(description="Payment failure message")
    amount_refunded: int | None = Field(description="Amount refunded in cents")
