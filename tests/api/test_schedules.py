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
        admin_token: str,
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

        headers = {"Authorization": f"Bearer {admin_token}"}
        response = await client.get(f"/api/v1/schedules/?course_id={course_id}", headers=headers)
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


# Resource CRUD Tests

# Use valid ObjectId strings for testing
ASSIGNED_TUTOR_ID = "507f1f77bcf86cd799439011"
OTHER_TUTOR_ID = "507f1f77bcf86cd799439012"
STUDENT_ID = "507f1f77bcf86cd799439013"


@pytest.fixture
async def assigned_tutor_token() -> str:
    """Create JWT token for the assigned tutor."""
    token = create_access_token(data={"sub": ASSIGNED_TUTOR_ID, "role": UserRole.TUTOR})
    return token


@pytest.fixture
async def other_tutor_token() -> str:
    """Create JWT token for a non-assigned tutor."""
    token = create_access_token(data={"sub": OTHER_TUTOR_ID, "role": UserRole.TUTOR})
    return token


@pytest.fixture
async def student_token() -> str:
    """Create JWT token for a student."""
    token = create_access_token(data={"sub": STUDENT_ID, "role": UserRole.STUDENT})
    return token


async def _create_schedule_with_tutor(
    repo: ScheduleRepository, tutor_id: str = ASSIGNED_TUTOR_ID
) -> dict[str, Any]:
    """Helper to create a schedule with a specific tutor."""
    from bson import ObjectId

    return await repo.create_schedule(
        course_id=str(ObjectId()),
        tutor_id=tutor_id,
        sessions=[{"date": datetime.utcnow(), "start_time": "10:00", "end_time": "12:00"}],
        capacity=10,
    )


class TestGetScheduleResources:
    """Tests for GET /schedules/{schedule_id}/resources endpoint."""

    @pytest.mark.anyio
    async def test_get_resources_empty(
        self,
        client: AsyncClient,
        schedule_repo: ScheduleRepository,
        cleanup_schedules: AsyncGenerator[None, None],
    ) -> None:
        """Test getting resources from schedule with no resources."""
        schedule = await _create_schedule_with_tutor(schedule_repo)
        response = await client.get(f"/api/v1/schedules/{schedule['_id']}/resources")
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == []

    @pytest.mark.anyio
    async def test_get_resources_with_data(
        self,
        client: AsyncClient,
        schedule_repo: ScheduleRepository,
        admin_token: str,
        cleanup_schedules: AsyncGenerator[None, None],
    ) -> None:
        """Test getting resources after adding some."""
        schedule = await _create_schedule_with_tutor(schedule_repo)
        headers = {"Authorization": f"Bearer {admin_token}"}

        # Add a resource
        resource = {"type": "course_material", "title": "Test Resource"}
        await client.post(
            f"/api/v1/schedules/{schedule['_id']}/resources", json=resource, headers=headers
        )

        response = await client.get(f"/api/v1/schedules/{schedule['_id']}/resources")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]["title"] == "Test Resource"

    @pytest.mark.anyio
    async def test_get_resources_schedule_not_found(
        self,
        client: AsyncClient,
        schedule_repo: ScheduleRepository,
        cleanup_schedules: AsyncGenerator[None, None],
    ) -> None:
        """Test getting resources from non-existent schedule."""
        from bson import ObjectId

        fake_id = str(ObjectId())
        response = await client.get(f"/api/v1/schedules/{fake_id}/resources")
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestAddScheduleResource:
    """Tests for POST /schedules/{schedule_id}/resources endpoint."""

    @pytest.mark.anyio
    async def test_admin_can_add_resource(
        self,
        client: AsyncClient,
        schedule_repo: ScheduleRepository,
        admin_token: str,
        cleanup_schedules: AsyncGenerator[None, None],
    ) -> None:
        """Test that admin can add resource to any schedule."""
        schedule = await _create_schedule_with_tutor(schedule_repo)
        headers = {"Authorization": f"Bearer {admin_token}"}
        resource = {
            "type": "course_material",
            "title": "Course Slides",
            "details": "Introduction slides",
            "url": "https://example.com/slides.pdf",
        }

        response = await client.post(
            f"/api/v1/schedules/{schedule['_id']}/resources", json=resource, headers=headers
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["type"] == "course_material"
        assert data["title"] == "Course Slides"
        assert data["url"] == "https://example.com/slides.pdf"

    @pytest.mark.anyio
    async def test_assigned_tutor_can_add_resource(
        self,
        client: AsyncClient,
        schedule_repo: ScheduleRepository,
        assigned_tutor_token: str,
        cleanup_schedules: AsyncGenerator[None, None],
    ) -> None:
        """Test that assigned tutor can add resource to their schedule."""
        schedule = await _create_schedule_with_tutor(schedule_repo, ASSIGNED_TUTOR_ID)
        headers = {"Authorization": f"Bearer {assigned_tutor_token}"}
        resource = {"type": "lab_link", "title": "Lab Environment"}

        response = await client.post(
            f"/api/v1/schedules/{schedule['_id']}/resources", json=resource, headers=headers
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["type"] == "lab_link"

    @pytest.mark.anyio
    async def test_non_assigned_tutor_forbidden(
        self,
        client: AsyncClient,
        schedule_repo: ScheduleRepository,
        other_tutor_token: str,
        cleanup_schedules: AsyncGenerator[None, None],
    ) -> None:
        """Test that non-assigned tutor cannot add resource."""
        schedule = await _create_schedule_with_tutor(schedule_repo, ASSIGNED_TUTOR_ID)
        headers = {"Authorization": f"Bearer {other_tutor_token}"}
        resource = {"type": "course_material", "title": "Unauthorized Resource"}

        response = await client.post(
            f"/api/v1/schedules/{schedule['_id']}/resources", json=resource, headers=headers
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.anyio
    async def test_student_forbidden(
        self,
        client: AsyncClient,
        schedule_repo: ScheduleRepository,
        student_token: str,
        cleanup_schedules: AsyncGenerator[None, None],
    ) -> None:
        """Test that student cannot add resource."""
        schedule = await _create_schedule_with_tutor(schedule_repo)
        headers = {"Authorization": f"Bearer {student_token}"}
        resource = {"type": "course_material", "title": "Student Resource"}

        response = await client.post(
            f"/api/v1/schedules/{schedule['_id']}/resources", json=resource, headers=headers
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.anyio
    async def test_add_resource_invalid_type(
        self,
        client: AsyncClient,
        schedule_repo: ScheduleRepository,
        admin_token: str,
        cleanup_schedules: AsyncGenerator[None, None],
    ) -> None:
        """Test adding resource with invalid type."""
        schedule = await _create_schedule_with_tutor(schedule_repo)
        headers = {"Authorization": f"Bearer {admin_token}"}
        resource = {"type": "invalid_type", "title": "Bad Resource"}

        response = await client.post(
            f"/api/v1/schedules/{schedule['_id']}/resources", json=resource, headers=headers
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.anyio
    async def test_add_resource_schedule_not_found(
        self,
        client: AsyncClient,
        admin_token: str,
        cleanup_schedules: AsyncGenerator[None, None],
    ) -> None:
        """Test adding resource to non-existent schedule."""
        from bson import ObjectId

        fake_id = str(ObjectId())
        headers = {"Authorization": f"Bearer {admin_token}"}
        resource = {"type": "course_material", "title": "Resource"}

        response = await client.post(
            f"/api/v1/schedules/{fake_id}/resources", json=resource, headers=headers
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestUpdateScheduleResource:
    """Tests for PUT /schedules/{schedule_id}/resources/{resource_index} endpoint."""

    @pytest.mark.anyio
    async def test_update_resource_success(
        self,
        client: AsyncClient,
        schedule_repo: ScheduleRepository,
        admin_token: str,
        cleanup_schedules: AsyncGenerator[None, None],
    ) -> None:
        """Test updating a resource."""
        schedule = await _create_schedule_with_tutor(schedule_repo)
        headers = {"Authorization": f"Bearer {admin_token}"}

        # First add a resource
        resource = {"type": "course_material", "title": "Original Title"}
        await client.post(
            f"/api/v1/schedules/{schedule['_id']}/resources", json=resource, headers=headers
        )

        # Update the resource
        update = {"title": "Updated Title", "details": "New details"}
        response = await client.put(
            f"/api/v1/schedules/{schedule['_id']}/resources/0", json=update, headers=headers
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["title"] == "Updated Title"
        assert data["details"] == "New details"
        assert data["type"] == "course_material"  # Unchanged

    @pytest.mark.anyio
    async def test_assigned_tutor_can_update_resource(
        self,
        client: AsyncClient,
        schedule_repo: ScheduleRepository,
        assigned_tutor_token: str,
        cleanup_schedules: AsyncGenerator[None, None],
    ) -> None:
        """Test that assigned tutor can update resource."""
        schedule = await _create_schedule_with_tutor(schedule_repo, ASSIGNED_TUTOR_ID)
        headers = {"Authorization": f"Bearer {assigned_tutor_token}"}

        # Add resource
        await client.post(
            f"/api/v1/schedules/{schedule['_id']}/resources",
            json={"type": "lab_link", "title": "Lab"},
            headers=headers,
        )

        # Update resource
        response = await client.put(
            f"/api/v1/schedules/{schedule['_id']}/resources/0",
            json={"url": "https://lab.example.com"},
            headers=headers,
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["url"] == "https://lab.example.com"

    @pytest.mark.anyio
    async def test_update_resource_invalid_index(
        self,
        client: AsyncClient,
        schedule_repo: ScheduleRepository,
        admin_token: str,
        cleanup_schedules: AsyncGenerator[None, None],
    ) -> None:
        """Test updating resource with invalid index."""
        schedule = await _create_schedule_with_tutor(schedule_repo)
        headers = {"Authorization": f"Bearer {admin_token}"}

        response = await client.put(
            f"/api/v1/schedules/{schedule['_id']}/resources/99",
            json={"title": "Update"},
            headers=headers,
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.anyio
    async def test_update_resource_negative_index(
        self,
        client: AsyncClient,
        schedule_repo: ScheduleRepository,
        admin_token: str,
        cleanup_schedules: AsyncGenerator[None, None],
    ) -> None:
        """Test updating resource with negative index."""
        schedule = await _create_schedule_with_tutor(schedule_repo)
        headers = {"Authorization": f"Bearer {admin_token}"}

        # Add a resource first
        await client.post(
            f"/api/v1/schedules/{schedule['_id']}/resources",
            json={"type": "course_material", "title": "Test"},
            headers=headers,
        )

        response = await client.put(
            f"/api/v1/schedules/{schedule['_id']}/resources/-1",
            json={"title": "Update"},
            headers=headers,
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestDeleteScheduleResource:
    """Tests for DELETE /schedules/{schedule_id}/resources/{resource_index} endpoint."""

    @pytest.mark.anyio
    async def test_delete_resource_success(
        self,
        client: AsyncClient,
        schedule_repo: ScheduleRepository,
        admin_token: str,
        cleanup_schedules: AsyncGenerator[None, None],
    ) -> None:
        """Test deleting a resource."""
        schedule = await _create_schedule_with_tutor(schedule_repo)
        headers = {"Authorization": f"Bearer {admin_token}"}

        # Add two resources
        await client.post(
            f"/api/v1/schedules/{schedule['_id']}/resources",
            json={"type": "course_material", "title": "First"},
            headers=headers,
        )
        await client.post(
            f"/api/v1/schedules/{schedule['_id']}/resources",
            json={"type": "lab_link", "title": "Second"},
            headers=headers,
        )

        # Delete first resource
        response = await client.delete(
            f"/api/v1/schedules/{schedule['_id']}/resources/0", headers=headers
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Verify only one resource remains
        get_response = await client.get(f"/api/v1/schedules/{schedule['_id']}/resources")
        data = get_response.json()
        assert len(data) == 1
        assert data[0]["title"] == "Second"

    @pytest.mark.anyio
    async def test_assigned_tutor_can_delete_resource(
        self,
        client: AsyncClient,
        schedule_repo: ScheduleRepository,
        assigned_tutor_token: str,
        cleanup_schedules: AsyncGenerator[None, None],
    ) -> None:
        """Test that assigned tutor can delete resource."""
        schedule = await _create_schedule_with_tutor(schedule_repo, ASSIGNED_TUTOR_ID)
        headers = {"Authorization": f"Bearer {assigned_tutor_token}"}

        # Add resource
        await client.post(
            f"/api/v1/schedules/{schedule['_id']}/resources",
            json={"type": "class_link", "title": "Zoom Link"},
            headers=headers,
        )

        # Delete resource
        response = await client.delete(
            f"/api/v1/schedules/{schedule['_id']}/resources/0", headers=headers
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT

    @pytest.mark.anyio
    async def test_non_assigned_tutor_cannot_delete(
        self,
        client: AsyncClient,
        schedule_repo: ScheduleRepository,
        admin_token: str,
        other_tutor_token: str,
        cleanup_schedules: AsyncGenerator[None, None],
    ) -> None:
        """Test that non-assigned tutor cannot delete resource."""
        schedule = await _create_schedule_with_tutor(schedule_repo, ASSIGNED_TUTOR_ID)
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        tutor_headers = {"Authorization": f"Bearer {other_tutor_token}"}

        # Add resource as admin
        await client.post(
            f"/api/v1/schedules/{schedule['_id']}/resources",
            json={"type": "course_material", "title": "Test"},
            headers=admin_headers,
        )

        # Try to delete as non-assigned tutor
        response = await client.delete(
            f"/api/v1/schedules/{schedule['_id']}/resources/0", headers=tutor_headers
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.anyio
    async def test_delete_resource_invalid_index(
        self,
        client: AsyncClient,
        schedule_repo: ScheduleRepository,
        admin_token: str,
        cleanup_schedules: AsyncGenerator[None, None],
    ) -> None:
        """Test deleting resource with invalid index."""
        schedule = await _create_schedule_with_tutor(schedule_repo)
        headers = {"Authorization": f"Bearer {admin_token}"}

        response = await client.delete(
            f"/api/v1/schedules/{schedule['_id']}/resources/0", headers=headers
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.anyio
    async def test_delete_resource_schedule_not_found(
        self,
        client: AsyncClient,
        admin_token: str,
        cleanup_schedules: AsyncGenerator[None, None],
    ) -> None:
        """Test deleting resource from non-existent schedule."""
        from bson import ObjectId

        fake_id = str(ObjectId())
        headers = {"Authorization": f"Bearer {admin_token}"}

        response = await client.delete(f"/api/v1/schedules/{fake_id}/resources/0", headers=headers)
        assert response.status_code == status.HTTP_404_NOT_FOUND
