"""Tests for enrollments endpoints."""

from collections.abc import AsyncGenerator

import pytest
from fastapi import status
from httpx import AsyncClient

from app.core.security import create_access_token
from app.db import get_database
from app.db.enrollment_repository import EnrollmentRepository
from app.domain.users.value_objects import UserRole


@pytest.fixture
async def enrollment_repo(
    setup_db: AsyncGenerator[None, None]
) -> AsyncGenerator[EnrollmentRepository, None]:
    """Get enrollment repository with setup."""
    db = get_database()
    repo = EnrollmentRepository(db)
    await repo.create_indexes()
    yield repo


@pytest.fixture
async def student_token() -> str:
    """Create student JWT token for testing."""
    # Use a valid ObjectId for the student ID

    student_id = "5f8d0d55b54764421b7156c3"  # Use the one from seed or a valid one
    token = create_access_token(data={"sub": student_id, "role": UserRole.STUDENT})
    return token


@pytest.fixture
async def cleanup_enrollments(enrollment_repo: EnrollmentRepository) -> AsyncGenerator[None, None]:
    """Clean up test enrollments after each test."""
    yield
    await enrollment_repo.collection.delete_many({})  # type: ignore


class TestCreateEnrollment:
    """Tests for POST /enrollments endpoint."""

    @pytest.mark.anyio
    async def test_create_enrollment_success(
        self,
        client: AsyncClient,
        student_token: str,
        cleanup_enrollments: AsyncGenerator[None, None],
    ) -> None:
        """Test creating enrollment."""
        from bson import ObjectId

        payload = {
            "user_id": str(ObjectId()),
            "schedule_id": str(ObjectId()),
            "course_id": str(ObjectId()),
            "payment_transaction_id": "tx_test",
        }
        headers = {"Authorization": f"Bearer {student_token}"}
        response = await client.post("/api/v1/enrollments/", json=payload, headers=headers)
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["user_id"] == payload["user_id"]
        assert data["status"] == "ENROLLED"


class TestGetMyEnrollments:
    """Tests for GET /enrollments/my-enrollments endpoint."""

    @pytest.mark.anyio
    async def test_get_my_enrollments(
        self,
        client: AsyncClient,
        student_token: str,
        enrollment_repo: EnrollmentRepository,
        cleanup_enrollments: AsyncGenerator[None, None],
    ) -> None:
        """Test getting current user's enrollments."""
        from bson import ObjectId

        student_id = "5f8d0d55b54764421b7156c3"  # Must match token

        # Create enrollment for this student
        await enrollment_repo.create_enrollment(
            user_id=student_id, schedule_id=str(ObjectId()), course_id=str(ObjectId())
        )
        # Create enrollment for another student
        await enrollment_repo.create_enrollment(
            user_id=str(ObjectId()), schedule_id=str(ObjectId()), course_id=str(ObjectId())
        )

        headers = {"Authorization": f"Bearer {student_token}"}
        response = await client.get("/api/v1/enrollments/my-enrollments", headers=headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]["user_id"] == student_id


class TestUpdateEnrollment:
    """Tests for PUT /enrollments/{id} endpoint."""

    @pytest.mark.anyio
    async def test_update_enrollment_status(
        self,
        client: AsyncClient,
        enrollment_repo: EnrollmentRepository,
        cleanup_enrollments: AsyncGenerator[None, None],
    ) -> None:
        """Test updating enrollment status."""
        from bson import ObjectId

        enrollment = await enrollment_repo.create_enrollment(
            user_id=str(ObjectId()), schedule_id=str(ObjectId()), course_id=str(ObjectId())
        )

        payload = {"status": "COMPLETED", "grade": 95.5}
        response = await client.put(f"/api/v1/enrollments/{str(enrollment['_id'])}", json=payload)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "COMPLETED"
        assert data["grade"] == 95.5
