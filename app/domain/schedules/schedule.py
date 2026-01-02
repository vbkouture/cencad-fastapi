"""Schedule domain model."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ScheduleStatus(str, Enum):
    """Schedule status."""

    UPCOMING = "UPCOMING"
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class ResourceType(str, Enum):
    """Resource type."""

    COURSE_MATERIAL = "course_material"
    LAB_LINK = "lab_link"
    CLASS_LINK = "class_link"


class Resource(BaseModel):
    """Resource for a schedule."""

    title: str | None = None
    type: ResourceType
    details: str | None = None
    url: str | None = None


class Session(BaseModel):
    """Individual course session."""

    date: datetime
    start_time: str
    end_time: str


class Schedule(BaseModel):
    """Schedule domain model."""

    id: str = Field(alias="_id")
    course_id: str
    tutor_id: str
    sessions: list[Session]
    capacity: int
    enrollment_count: int = 0
    status: ScheduleStatus = ScheduleStatus.UPCOMING
    meeting_url: str | None = None
    timezone: str = "UTC"
    resources: list[Resource] | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic config."""

        populate_by_name = True
        json_encoders = {datetime: lambda v: v.isoformat()}

    @classmethod
    def from_mongo(cls, data: dict[str, Any]) -> Schedule:
        """Convert MongoDB document to Schedule model."""
        if not data:
            raise ValueError("Data is empty")

        id_val = str(data["_id"])

        # Handle sessions
        sessions_data = data.get("sessions", [])
        sessions = [Session(**s) for s in sessions_data]

        return cls(
            id=id_val,
            course_id=str(data["course_id"]),
            tutor_id=str(data["tutor_id"]),
            sessions=sessions,
            capacity=data["capacity"],
            enrollment_count=data.get("enrollment_count", 0),
            status=ScheduleStatus(data.get("status", "UPCOMING")),
            meeting_url=data.get("meeting_url"),
            timezone=data.get("timezone", "UTC"),
            resources=(
                [Resource(**r) for r in data.get("resources", [])]
                if data.get("resources")
                else None
            ),
            created_at=data["created_at"],
            updated_at=data["updated_at"],
        )
