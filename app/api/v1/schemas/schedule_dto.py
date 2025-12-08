"""Schedule DTOs for API requests/responses."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class SessionDTO(BaseModel):
    """DTO for a single session."""

    date: datetime = Field(description="Session date")
    start_time: str = Field(description="Start time (e.g., '18:00')")
    end_time: str = Field(description="End time (e.g., '20:00')")


class ScheduleCreateRequest(BaseModel):
    """Request DTO for creating a schedule."""

    course_id: str = Field(description="Course ID")
    tutor_id: str = Field(description="Tutor ID")
    sessions: list[SessionDTO] = Field(description="List of sessions")
    capacity: int = Field(ge=1, description="Maximum capacity")
    meeting_url: str | None = Field(None, description="Meeting URL for online sessions")
    timezone: str = Field("UTC", description="Timezone (e.g., 'America/New_York')")


class ScheduleUpdateRequest(BaseModel):
    """Request DTO for updating a schedule."""

    tutor_id: str | None = Field(None, description="Tutor ID")
    sessions: list[SessionDTO] | None = Field(None, description="List of sessions")
    capacity: int | None = Field(None, ge=1, description="Maximum capacity")
    status: str | None = Field(
        None, description="Schedule status (UPCOMING, ACTIVE, COMPLETED, CANCELLED)"
    )
    meeting_url: str | None = Field(None, description="Meeting URL")
    timezone: str | None = Field(None, description="Timezone")


class ScheduleResponse(BaseModel):
    """Response DTO for schedule."""

    id: str = Field(description="Schedule ID")
    course_id: str = Field(description="Course ID")
    tutor_id: str = Field(description="Tutor ID")
    sessions: list[SessionDTO] = Field(description="List of sessions")
    capacity: int = Field(description="Maximum capacity")
    enrollment_count: int = Field(description="Current enrollment count")
    status: str = Field(description="Schedule status")
    meeting_url: str | None = Field(description="Meeting URL")
    timezone: str = Field(description="Timezone")
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")
