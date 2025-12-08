"""Tests for user management endpoints."""

import pytest
from httpx import AsyncClient


@pytest.fixture
async def admin_token(client: AsyncClient) -> str:
    """Create an admin user and return their JWT token."""
    from app.core.security import hash_password
    from app.db import UserRepository, get_database
    from app.domain.users.value_objects import UserRole

    # Create admin directly in database
    db = get_database()
    user_repo = UserRepository(db)

    await user_repo.create_user(
        email="admin@example.com",
        name="Admin User",
        hashed_password=hash_password("adminpass123"),
        role=UserRole.ADMIN,
    )

    # Login as admin to get token
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "admin@example.com",
            "password": "adminpass123",
        },
    )
    return str(response.json()["access_token"])


@pytest.fixture
async def student_token(client: AsyncClient) -> str:
    """Create a student user and return their JWT token."""
    # Sign up as student
    response = await client.post(
        "/api/v1/auth/signup",
        json={
            "email": "student@example.com",
            "password": "studentpass123",
            "name": "Student User",
        },
    )
    return str(response.json()["access_token"])


@pytest.mark.anyio
async def test_create_tutor_as_admin(client: AsyncClient, admin_token: str) -> None:
    """Test that admins can create tutor accounts."""
    response = await client.post(
        "/api/v1/users/tutors",
        json={
            "email": "tutor@example.com",
            "password": "tutorpass123",
            "name": "Jane Tutor",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "tutor@example.com"
    assert data["name"] == "Jane Tutor"
    assert data["role"] == "tutor"
    assert "user_id" in data


@pytest.mark.anyio
async def test_create_tutor_requires_admin(client: AsyncClient, student_token: str) -> None:
    """Test that students cannot create tutor accounts."""
    response = await client.post(
        "/api/v1/users/tutors",
        json={
            "email": "tutor2@example.com",
            "password": "tutorpass123",
            "name": "Another Tutor",
        },
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert response.status_code == 403
    assert "Admin access required" in response.json()["detail"]


@pytest.mark.anyio
async def test_create_tutor_requires_auth(client: AsyncClient) -> None:
    """Test that creating tutor requires authentication."""
    response = await client.post(
        "/api/v1/users/tutors",
        json={
            "email": "tutor3@example.com",
            "password": "tutorpass123",
            "name": "Unauthorized Tutor",
        },
    )
    assert response.status_code == 403


@pytest.mark.anyio
async def test_create_tutor_rejects_duplicate_email(client: AsyncClient, admin_token: str) -> None:
    """Test that creating tutor rejects duplicate emails."""
    # Create first tutor
    await client.post(
        "/api/v1/users/tutors",
        json={
            "email": "duplicate@example.com",
            "password": "tutorpass123",
            "name": "First Tutor",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    # Try to create second tutor with same email
    response = await client.post(
        "/api/v1/users/tutors",
        json={
            "email": "duplicate@example.com",
            "password": "tutorpass456",
            "name": "Second Tutor",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 409
    assert "Email already registered" in response.json()["detail"]


@pytest.mark.anyio
async def test_create_tutor_rejects_short_password(client: AsyncClient, admin_token: str) -> None:
    """Test that creating tutor rejects short passwords."""
    response = await client.post(
        "/api/v1/users/tutors",
        json={
            "email": "tutor4@example.com",
            "password": "short",
            "name": "Bad Password Tutor",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 422


@pytest.mark.anyio
async def test_created_tutor_can_login(client: AsyncClient, admin_token: str) -> None:
    """Test that created tutor can login with their credentials."""
    # Create tutor
    create_response = await client.post(
        "/api/v1/users/tutors",
        json={
            "email": "logintutor@example.com",
            "password": "tutorpass123",
            "name": "Login Tutor",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert create_response.status_code == 201

    # Login as tutor
    login_response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "logintutor@example.com",
            "password": "tutorpass123",
        },
    )
    assert login_response.status_code == 200
    data = login_response.json()
    assert data["email"] == "logintutor@example.com"
    assert data["role"] == "tutor"
    assert "access_token" in data
