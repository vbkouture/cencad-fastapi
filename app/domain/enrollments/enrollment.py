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


class Enrollment(BaseModel):
    """Enrollment domain model."""

    id: str = Field(alias="_id")
    user_id: str
    schedule_id: str
    course_id: str
    status: EnrollmentStatus = EnrollmentStatus.ENROLLED
    payment_status: PaymentStatus = PaymentStatus.PENDING
    payment_transaction_id: str | None = None
    enrolled_at: datetime
    completed_at: datetime | None = None
    grade: float | None = None
    certificate_url: str | None = None
    instructor_notes: list[dict[str, Any]] = Field(default_factory=list)

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
            payment_status=PaymentStatus(data.get("payment_status", "PENDING")),
            payment_transaction_id=data.get("payment_transaction_id"),
            enrolled_at=data["enrolled_at"],
            completed_at=data.get("completed_at"),
            grade=data.get("grade"),
            certificate_url=data.get("certificate_url"),
            instructor_notes=data.get("instructor_notes", []),
        )
