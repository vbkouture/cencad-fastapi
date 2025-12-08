"""Course category DTOs for API requests/responses."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class CourseCategoryCreateRequest(BaseModel):
    """Request DTO for creating a course category."""

    name: str = Field(min_length=1, max_length=200, description="Category name")
    description: str = Field(min_length=1, max_length=1000, description="Category description")


class CourseCategoryUpdateRequest(BaseModel):
    """Request DTO for updating a course category."""

    name: str | None = Field(None, min_length=1, max_length=200, description="Category name")
    description: str | None = Field(
        None, min_length=1, max_length=1000, description="Category description"
    )


class CourseCategoryResponse(BaseModel):
    """Response DTO for course category."""

    id: str = Field(description="Category ID (MongoDB ObjectId as string)")
    name: str = Field(description="Category name")
    description: str = Field(description="Category description")
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")
