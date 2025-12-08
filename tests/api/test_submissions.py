"""Tests for submissions endpoints."""

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
        email="tutor_sub@example.com",
        name="Tutor User",
        hashed_password=hash_password("tutorpass123"),
        role=UserRole.TUTOR,
    )

    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "tutor_sub@example.com",
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
            "email": "student_sub@example.com",
            "password": "studentpass123",
            "name": "Student User",
        },
    )
    return str(response.json()["access_token"])


class TestGetSubmissions:
    """Tests for GET /assignments/{id}/submissions endpoint."""

    @pytest.mark.anyio
    async def test_get_submissions_tutor_success(
        self, client: AsyncClient, tutor_token: str
    ) -> None:
        """Test that a tutor can view submissions."""
        response = await client.get(
            "/api/v1/assignments/123/submissions",
            headers={"Authorization": f"Bearer {tutor_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["assignment_id"] == "123"
        assert isinstance(data["submissions"], list)

    @pytest.mark.anyio
    async def test_get_submissions_student_forbidden(
        self, client: AsyncClient, student_token: str
    ) -> None:
        """Test that a student cannot view all submissions."""
        response = await client.get(
            "/api/v1/assignments/123/submissions",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == 403


class TestGradeSubmission:
    """Tests for PUT /assignments/{id}/submissions/{sub_id}/grade endpoint."""

    @pytest.mark.anyio
    async def test_grade_submission_tutor_success(
        self, client: AsyncClient, tutor_token: str
    ) -> None:
        """Test that a tutor can grade a submission."""
        response = await client.put(
            "/api/v1/assignments/123/submissions/456/grade",
            headers={"Authorization": f"Bearer {tutor_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Submission graded"
        assert data["graded_by"] is not None

    @pytest.mark.anyio
    async def test_grade_submission_student_forbidden(
        self, client: AsyncClient, student_token: str
    ) -> None:
        """Test that a student cannot grade a submission."""
        response = await client.put(
            "/api/v1/assignments/123/submissions/456/grade",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == 403
