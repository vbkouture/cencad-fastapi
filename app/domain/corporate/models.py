from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from app.domain.users.value_objects import utcnow


class CompanySize(str, Enum):
    SIZE_1_10 = "1-10"
    SIZE_11_50 = "11-50"
    SIZE_51_200 = "51-200"
    SIZE_201_500 = "201-500"
    SIZE_501_1000 = "501-1000"
    SIZE_1000_PLUS = "1000+"


class AccountStatus(str, Enum):
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    CANCELLED = "CANCELLED"


class LicenseStatus(str, Enum):
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"


class AssignmentStatus(str, Enum):
    PENDING = "PENDING"  # Invited but not joined/accepted
    ACTIVE = "ACTIVE"  # User active on license
    COMPLETED = "COMPLETED"
    REMOVED = "REMOVED"


class CorporateAccount(BaseModel):
    """Represents a company using the platform."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str = Field(...)
    company_name: str = Field(...)
    company_website: str | None = None
    industry: str | None = None
    company_size: CompanySize
    address: str | None = None
    phone: str | None = None
    status: AccountStatus = Field(default=AccountStatus.PENDING)

    # Store IDs of admin users for this account
    admin_user_ids: list[str] = Field(default_factory=list)

    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    @classmethod
    def create(
        cls,
        account_id: str,
        company_name: str,
        company_size: CompanySize,
        admin_user_id: str,
        company_website: str | None = None,
        industry: str | None = None,
        address: str | None = None,
        phone: str | None = None,
    ) -> CorporateAccount:
        now = utcnow()
        return cls(
            id=account_id,
            company_name=company_name,
            company_size=company_size,
            company_website=company_website,
            industry=industry,
            address=address,
            phone=phone,
            status=AccountStatus.ACTIVE,  # Use ACTIVE by default for new registrations?
            admin_user_ids=[admin_user_id],
            created_at=now,
            updated_at=now,
        )


class CorporateLicense(BaseModel):
    """Represents a bulk purchase of seats for a specific course schedule."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str = Field(...)
    corporate_account_id: str = Field(...)
    schedule_id: str = Field(...)
    course_id: str = Field(...)

    total_seats: int = Field(ge=1)
    assigned_seats: int = Field(default=0, ge=0)

    amount_total: float = Field(...)
    currency: str = Field(default="usd")

    status: LicenseStatus = Field(default=LicenseStatus.ACTIVE)
    stripe_payment_intent_id: str | None = None

    purchased_at: datetime = Field(default_factory=utcnow)
    expires_at: datetime | None = None


class CorporateTrainee(BaseModel):
    """Represents an employee invited by a corporate account."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str = Field(...)
    corporate_account_id: str = Field(...)
    user_id: str = Field(...)  # Link to the actual User record

    # Optional metadata specific to the company context
    employee_id: str | None = None
    department: str | None = None

    is_active: bool = Field(default=True)
    invited_at: datetime = Field(default_factory=utcnow)
    joined_at: datetime | None = None


class TraineeAssignment(BaseModel):
    """Links a specific trainee to a specific license (seat usage)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str = Field(...)
    license_id: str = Field(...)
    trainee_id: str = Field(...)  # Refers to CorporateTrainee.id

    status: AssignmentStatus = Field(default=AssignmentStatus.PENDING)

    assigned_at: datetime = Field(default_factory=utcnow)
    completed_at: datetime | None = None
