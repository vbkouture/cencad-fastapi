"""Job role DTOs for API requests/responses."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class JobRoleCreateRequest(BaseModel):
    """Request DTO for creating a job role."""

    name: str = Field(min_length=1, max_length=200, description="Job role name")
    description: str = Field(
        min_length=1, max_length=1000, description="Job role description"
    )


class JobRoleUpdateRequest(BaseModel):
    """Request DTO for updating a job role."""

    name: str | None = Field(
        None, min_length=1, max_length=200, description="Job role name"
    )
    description: str | None = Field(
        None, min_length=1, max_length=1000, description="Job role description"
    )


class JobRoleResponse(BaseModel):
    """Response DTO for job role."""

    id: str = Field(description="Job role ID (MongoDB ObjectId as string)")
    name: str = Field(description="Job role name")
    description: str = Field(description="Job role description")
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")
