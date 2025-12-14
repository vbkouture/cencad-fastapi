"""Enrollment domain model."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class EnrollmentStatus(str, Enum):
    """Enrollment status."""

    ENROLLED = "ENROLLED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    DROPPED = "DROPPED"


class PaymentStatus(str, Enum):
    """Payment status."""

    PENDING = "PENDING"
    PAID = "PAID"
    REFUNDED = "REFUNDED"
    DISPUTED = "DISPUTED"
    FAILED = "FAILED"


class Enrollment(BaseModel):
    """Enrollment domain model."""

    id: str = Field(alias="_id")
    user_id: str
    schedule_id: str
    course_id: str
    status: EnrollmentStatus = EnrollmentStatus.ENROLLED

    # Checkouts / Payment details
    amount_total: int | None = None  # in cents
    currency: str = "cad"
    payment_status: PaymentStatus = PaymentStatus.PENDING
    payment_method_type: str | None = None
    receipt_email: str | None = None

    # Stripe Identifiers
    stripe_checkout_session_id: str | None = None
    stripe_payment_intent_id: str | None = None
    stripe_customer_id: str | None = None
    stripe_charge_id: str | None = None

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    paid_at: datetime | None = None
    enrolled_at: datetime  # When they officially became a student (often same as paid_at)
    completed_at: datetime | None = None

    # Metadata / Extras
    grade: float | None = None
    certificate_url: str | None = None
    instructor_notes: list[dict[str, Any]] = Field(default_factory=list)
    failure_message: str | None = None
    amount_refunded: int | None = None

    class Config:
        """Pydantic config."""

        populate_by_name = True
        json_encoders = {datetime: lambda v: v.isoformat()}

    @classmethod
    def from_mongo(cls, data: dict[str, Any]) -> Enrollment:
        """Convert MongoDB document to Enrollment model."""
        if not data:
            raise ValueError("Data is empty")

        id_val = str(data["_id"])
        return cls(
            id=id_val,
            user_id=str(data["user_id"]),
            schedule_id=str(data["schedule_id"]),
            course_id=str(data["course_id"]),
            status=EnrollmentStatus(data.get("status", "ENROLLED")),
            amount_total=data.get("amount_total"),
            currency=data.get("currency", "cad"),
            payment_status=PaymentStatus(data.get("payment_status", "PENDING")),
            payment_method_type=data.get("payment_method_type"),
            receipt_email=data.get("receipt_email"),
            stripe_checkout_session_id=data.get("stripe_checkout_session_id"),
            stripe_payment_intent_id=data.get("stripe_payment_intent_id"),
            stripe_customer_id=data.get("stripe_customer_id"),
            stripe_charge_id=data.get("stripe_charge_id"),
            created_at=data.get("created_at", datetime.utcnow()),
            paid_at=data.get("paid_at"),
            enrolled_at=data["enrolled_at"],
            completed_at=data.get("completed_at"),
            grade=data.get("grade"),
            certificate_url=data.get("certificate_url"),
            instructor_notes=data.get("instructor_notes", []),
            failure_message=data.get("failure_message"),
            amount_refunded=data.get("amount_refunded"),
        )
