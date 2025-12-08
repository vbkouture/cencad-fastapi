"""Tests for assignments endpoints."""

import pytest
from httpx import AsyncClient

from app.db import get_database


@pytest.fixture
async def tutor_token(client: AsyncClient) -> str:
    """Create a tutor user and return their JWT token."""
    from app.core.security import hash_password
    from app.db import UserRepository
    from app.domain.users.value_objects import UserRole

    db = get_database()
    user_repo = UserRepository(db)

    await user_repo.create_user(
        email="tutor@example.com",
        name="Tutor User",
        hashed_password=hash_password("tutorpass123"),
        role=UserRole.TUTOR,
    )

    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "tutor@example.com",
            "password": "tutorpass123",
        },
    )
    return str(response.json()["access_token"])


@pytest.fixture
async def student_token(client: AsyncClient) -> str:
    """Create a student user and return their JWT token."""
    response = await client.post(
        "/api/v1/auth/signup",
        json={
            "email": "student@example.com",
            "password": "studentpass123",
            "name": "Student User",
        },
    )
    return str(response.json()["access_token"])


class TestCreateAssignment:
    """Tests for POST /assignments endpoint."""

    @pytest.mark.anyio
    async def test_create_assignment_tutor_success(
        self, client: AsyncClient, tutor_token: str
    ) -> None:
        """Test that a tutor can create an assignment."""
        response = await client.post(
            "/api/v1/assignments",
            headers={"Authorization": f"Bearer {tutor_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Assignment created"
        assert "created_by" in data

    @pytest.mark.anyio
    async def test_create_assignment_student_forbidden(
        self, client: AsyncClient, student_token: str
    ) -> None:
        """Test that a student cannot create an assignment."""
        response = await client.post(
            "/api/v1/assignments",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == 403


class TestGetAssignment:
    """Tests for GET /assignments/{id} endpoint."""

    @pytest.mark.anyio
    async def test_get_assignment_success(self, client: AsyncClient, student_token: str) -> None:
        """Test that a student can view an assignment."""
        response = await client.get(
            "/api/v1/assignments/123",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["assignment_id"] == "123"

    @pytest.mark.anyio
    async def test_get_assignment_unauthorized(self, client: AsyncClient) -> None:
        """Test that unauthenticated users cannot view assignments."""
        response = await client.get("/api/v1/assignments/123")
        assert response.status_code == 403


class TestUpdateAssignment:
    """Tests for PUT /assignments/{id} endpoint."""

    @pytest.mark.anyio
    async def test_update_assignment_tutor_success(
        self, client: AsyncClient, tutor_token: str
    ) -> None:
        """Test that a tutor can update an assignment."""
        response = await client.put(
            "/api/v1/assignments/123",
            headers={"Authorization": f"Bearer {tutor_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Assignment updated"

    @pytest.mark.anyio
    async def test_update_assignment_student_forbidden(
        self, client: AsyncClient, student_token: str
    ) -> None:
        """Test that a student cannot update an assignment."""
        response = await client.put(
            "/api/v1/assignments/123",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == 403


class TestDeleteAssignment:
    """Tests for DELETE /assignments/{id} endpoint."""

    @pytest.mark.anyio
    async def test_delete_assignment_tutor_success(
        self, client: AsyncClient, tutor_token: str
    ) -> None:
        """Test that a tutor can delete an assignment."""
        response = await client.delete(
            "/api/v1/assignments/123",
            headers={"Authorization": f"Bearer {tutor_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Assignment deleted"

    @pytest.mark.anyio
    async def test_delete_assignment_student_forbidden(
        self, client: AsyncClient, student_token: str
    ) -> None:
        """Test that a student cannot delete an assignment."""
        response = await client.delete(
            "/api/v1/assignments/123",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == 403
