"""Vendor DTOs for API requests/responses."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class VendorCreateRequest(BaseModel):
    """Request DTO for creating a vendor."""

    name: str = Field(min_length=1, max_length=200, description="Vendor name")
    description: str = Field(
        min_length=1, max_length=1000, description="Vendor description"
    )
    logo: str | None = Field(None, description="Optional vendor logo URL")


class VendorUpdateRequest(BaseModel):
    """Request DTO for updating a vendor."""

    name: str | None = Field(
        None, min_length=1, max_length=200, description="Vendor name"
    )
    description: str | None = Field(
        None, min_length=1, max_length=1000, description="Vendor description"
    )
    logo: str | None = Field(None, description="Optional vendor logo URL")


class VendorResponse(BaseModel):
    """Response DTO for vendor."""

    id: str = Field(description="Vendor ID (MongoDB ObjectId as string)")
    name: str = Field(description="Vendor name")
    description: str = Field(description="Vendor description")
    logo: str | None = Field(description="Optional vendor logo URL")
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")
