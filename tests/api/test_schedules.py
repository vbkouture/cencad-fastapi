"""Tests for schedules endpoints."""

from collections.abc import AsyncGenerator
from datetime import datetime, timedelta
from typing import Any

import pytest
from fastapi import status
from httpx import AsyncClient

from app.core.security import create_access_token
from app.db import get_database
from app.db.schedule_repository import ScheduleRepository
from app.domain.users.value_objects import UserRole


@pytest.fixture
async def schedule_repo(
    setup_db: AsyncGenerator[None, None]
) -> AsyncGenerator[ScheduleRepository, None]:
    """Get schedule repository with setup."""
    db = get_database()
    repo = ScheduleRepository(db)
    await repo.create_indexes()
    yield repo


@pytest.fixture
async def admin_token() -> str:
    """Create admin JWT token for testing."""
    token = create_access_token(data={"sub": "test_admin_id", "role": UserRole.ADMIN})
    return token


@pytest.fixture
async def tutor_token() -> str:
    """Create tutor JWT token for testing."""
    token = create_access_token(data={"sub": "test_tutor_id", "role": UserRole.TUTOR})
    return token


@pytest.fixture
async def cleanup_schedules(schedule_repo: ScheduleRepository) -> AsyncGenerator[None, None]:
    """Clean up test schedules after each test."""
    yield
    await schedule_repo.collection.delete_many({})  # type: ignore


def _create_valid_schedule_payload() -> dict[str, Any]:
    """Create a valid schedule creation payload."""
    from bson import ObjectId

    session_date = datetime.utcnow() + timedelta(days=1)
    return {
        "course_id": str(ObjectId()),
        "tutor_id": str(ObjectId()),
        "sessions": [
            {"date": session_date.isoformat(), "start_time": "18:00", "end_time": "20:00"},
            {
                "date": (session_date + timedelta(days=2)).isoformat(),
                "start_time": "18:00",
                "end_time": "20:00",
            },
        ],
        "capacity": 20,
        "meeting_url": "https://zoom.us/test",
        "timezone": "UTC",
    }


class TestCreateSchedule:
    """Tests for POST /schedules endpoint."""

    @pytest.mark.anyio
    async def test_create_schedule_success(
        self, client: AsyncClient, admin_token: str, cleanup_schedules: AsyncGenerator[None, None]
    ) -> None:
        """Test creating schedule with valid data."""
        payload = _create_valid_schedule_payload()
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = await client.post("/api/v1/schedules/", json=payload, headers=headers)
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["course_id"] == payload["course_id"]
        assert len(data["sessions"]) == 2
        assert data["status"] == "UPCOMING"


class TestGetSchedules:
    """Tests for GET /schedules endpoints."""

    @pytest.mark.anyio
    async def test_get_schedule_by_id(
        self,
        client: AsyncClient,
        schedule_repo: ScheduleRepository,
        cleanup_schedules: AsyncGenerator[None, None],
    ) -> None:
        """Test getting a schedule by ID."""
        from bson import ObjectId

        schedule = await schedule_repo.create_schedule(
            course_id=str(ObjectId()),
            tutor_id=str(ObjectId()),
            sessions=[{"date": datetime.utcnow(), "start_time": "10:00", "end_time": "12:00"}],
            capacity=10,
        )
        response = await client.get(f"/api/v1/schedules/{str(schedule['_id'])}")
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["id"] == str(schedule["_id"])

    @pytest.mark.anyio
    async def test_get_schedules_by_course(
        self,
        client: AsyncClient,
        schedule_repo: ScheduleRepository,
        cleanup_schedules: AsyncGenerator[None, None],
    ) -> None:
        """Test getting schedules filtered by course."""
        from bson import ObjectId

        course_id = str(ObjectId())
        await schedule_repo.create_schedule(
            course_id=course_id, tutor_id=str(ObjectId()), sessions=[], capacity=10
        )
        await schedule_repo.create_schedule(
            course_id=str(ObjectId()), tutor_id=str(ObjectId()), sessions=[], capacity=10
        )

        response = await client.get(f"/api/v1/schedules/?course_id={course_id}")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]["course_id"] == course_id


class TestUpdateSchedule:
    """Tests for PUT /schedules/{id} endpoint."""

    @pytest.mark.anyio
    async def test_update_schedule_success(
        self,
        client: AsyncClient,
        schedule_repo: ScheduleRepository,
        admin_token: str,
        cleanup_schedules: AsyncGenerator[None, None],
    ) -> None:
        """Test updating a schedule."""
        from bson import ObjectId

        schedule = await schedule_repo.create_schedule(
            course_id=str(ObjectId()), tutor_id=str(ObjectId()), sessions=[], capacity=10
        )
        payload = {"capacity": 50, "status": "ACTIVE"}
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = await client.put(
            f"/api/v1/schedules/{str(schedule['_id'])}", json=payload, headers=headers
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["capacity"] == 50
        assert data["status"] == "ACTIVE"


class TestDeleteSchedule:
    """Tests for DELETE /schedules/{id} endpoint."""

    @pytest.mark.anyio
    async def test_delete_schedule_success(
        self,
        client: AsyncClient,
        schedule_repo: ScheduleRepository,
        admin_token: str,
        cleanup_schedules: AsyncGenerator[None, None],
    ) -> None:
        """Test deleting a schedule."""
        from bson import ObjectId

        schedule = await schedule_repo.create_schedule(
            course_id=str(ObjectId()), tutor_id=str(ObjectId()), sessions=[], capacity=10
        )
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = await client.delete(f"/api/v1/schedules/{str(schedule['_id'])}", headers=headers)
        assert response.status_code == status.HTTP_204_NO_CONTENT

        deleted = await schedule_repo.find_by_id(str(schedule["_id"]))
        assert deleted is None
