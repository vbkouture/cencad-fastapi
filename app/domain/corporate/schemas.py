from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from app.domain.corporate.models import AccountStatus, CompanySize, LicenseStatus


class CorporateAccountResponse(BaseModel):
    id: str
    company_name: str
    company_website: str | None
    industry: str | None
    company_size: CompanySize
    address: str | None
    phone: str | None
    status: AccountStatus
    created_at: datetime


class RegisterCorporateRequest(BaseModel):
    company_name: str
    company_website: str | None = None
    industry: str | None = None
    company_size: CompanySize
    address: str | None = None
    phone: str | None = None

    # Admin User Details
    admin_name: str
    admin_email: EmailStr
    admin_password: str


class UpdateCorporateAccountRequest(BaseModel):
    company_name: str | None = None
    company_website: str | None = None
    industry: str | None = None
    company_size: CompanySize | None = None
    address: str | None = None
    phone: str | None = None


class CorporateDashboardStats(BaseModel):
    total_licenses: int
    available_licenses: int
    total_trainees: int
    active_trainees: int
    courses_purchased: int
    total_spend: float
    currency: str


class CreateBulkCheckoutSessionRequest(BaseModel):
    course_id: str
    schedule_id: str
    quantity: int = Field(gt=0, description="Number of seats")


class CheckoutSessionResponse(BaseModel):
    url: str
    session_id: str


class CorporateLicenseResponse(BaseModel):
    id: str
    course_id: str
    schedule_id: str
    total_seats: int
    assigned_seats: int
    amount_total: float
    currency: str
    status: LicenseStatus
    purchased_at: datetime
    expires_at: datetime | None


class InviteTraineeRequest(BaseModel):
    email: EmailStr
    name: str
    license_id: str | None = None  # Optional: assign immediately


class CorporateTraineeResponse(BaseModel):
    id: str
    user_id: str
    # Enriched fields from User model could go here if needed,
    # but for now we stick to the CorporateTrainee model fields + user details
    email: str
    name: str
    is_active: bool
    joined_at: datetime | None


class AssignTraineeRequest(BaseModel):
    trainee_id: str
    license_id: str


class UnassignTraineeRequest(BaseModel):
    trainee_id: str
    license_id: str


class PaginatedLicenseResponse(BaseModel):
    total: int
    items: list[CorporateLicenseResponse]


class PaginatedTraineeResponse(BaseModel):
    total: int
    items: list[CorporateTraineeResponse]
