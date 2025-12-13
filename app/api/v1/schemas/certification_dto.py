"""Certification Data Transfer Objects."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CertificationBase(BaseModel):
    """Base Certification schema."""

    vendor_id: str = Field(..., description="ID of the vendor providing this certification")
    name: str = Field(..., description="Name of the certification")
    description: str | None = Field(None, description="Optional description of the certification")
    url: str | None = Field(None, description="Optional URL for more info")


class CertificationCreateRequest(CertificationBase):
    """Request schema for creating a certification."""

    pass


class CertificationUpdateRequest(BaseModel):
    """Request schema for updating a certification."""

    vendor_id: str | None = Field(None, description="ID of the vendor providing this certification")
    name: str | None = Field(None, description="Name of the certification")
    description: str | None = Field(None, description="Optional description of the certification")
    url: str | None = Field(None, description="Optional URL for more info")


class CertificationResponse(CertificationBase):
    """Response schema for certification."""

    id: str = Field(..., description="Unique identifier")
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
