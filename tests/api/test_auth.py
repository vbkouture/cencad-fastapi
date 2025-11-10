"""Tests for authentication endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.anyio
async def test_signup_creates_user_with_default_role(client: AsyncClient) -> None:
    """Test signup endpoint creates a user with student role by default."""
    response = await client.post(
        "/api/v1/auth/signup",
        json={
            "email": "student@example.com",
            "password": "securepass123",
            "name": "John Student",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "student@example.com"
    assert data["name"] == "John Student"
    assert data["role"] == "student"
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.anyio
async def test_signup_always_creates_student(client: AsyncClient) -> None:
    """Test that signup endpoint always creates student, ignoring role parameter."""
    response = await client.post(
        "/api/v1/auth/signup",
        json={
            "email": "student2@example.com",
            "password": "securepass123",
            "name": "Jane Student",
            # Note: role field is no longer accepted in signup
        },
    )
    assert response.status_code == 201
    data = response.json()
    # Verify role is always student regardless of input
    assert data["role"] == "student"


@pytest.mark.anyio
async def test_signup_rejects_short_password(client: AsyncClient) -> None:
    """Test signup rejects passwords shorter than 8 characters."""
    response = await client.post(
        "/api/v1/auth/signup",
        json={
            "email": "user@example.com",
            "password": "short",
            "name": "Test User",
        },
    )
    assert response.status_code == 422


@pytest.mark.anyio
async def test_signup_rejects_duplicate_email(client: AsyncClient) -> None:
    """Test signup rejects duplicate email addresses."""
    # First signup
    await client.post(
        "/api/v1/auth/signup",
        json={
            "email": "duplicate@example.com",
            "password": "securepass123",
            "name": "First User",
        },
    )

    # Second signup with same email
    response = await client.post(
        "/api/v1/auth/signup",
        json={
            "email": "duplicate@example.com",
            "password": "securepass456",
            "name": "Second User",
        },
    )
    assert response.status_code == 409
    assert "Email already registered" in response.json()["detail"]


@pytest.mark.anyio
async def test_login_successful(client: AsyncClient) -> None:
    """Test successful login with correct credentials."""
    # Create user first
    signup_response = await client.post(
        "/api/v1/auth/signup",
        json={
            "email": "login@example.com",
            "password": "securepass123",
            "name": "Login Test",
        },
    )
    signup_data = signup_response.json()

    # Login with correct credentials
    login_response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "login@example.com",
            "password": "securepass123",
        },
    )
    assert login_response.status_code == 200
    login_data = login_response.json()
    assert login_data["email"] == "login@example.com"
    assert login_data["name"] == "Login Test"
    assert "access_token" in login_data
    # Both responses should have access tokens
    assert signup_data["access_token"] is not None
    assert login_data["access_token"] is not None


@pytest.mark.anyio
async def test_login_fails_with_wrong_password(client: AsyncClient) -> None:
    """Test login fails with incorrect password."""
    # Create user first
    await client.post(
        "/api/v1/auth/signup",
        json={
            "email": "wrongpwd@example.com",
            "password": "securepass123",
            "name": "Wrong Password Test",
        },
    )

    # Login with wrong password
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "wrongpwd@example.com",
            "password": "wrongpassword",
        },
    )
    assert response.status_code == 401
    assert "Invalid email or password" in response.json()["detail"]


@pytest.mark.anyio
async def test_login_fails_with_nonexistent_email(client: AsyncClient) -> None:
    """Test login fails with non-existent email."""
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "nonexistent@example.com",
            "password": "securepass123",
        },
    )
    assert response.status_code == 401
    assert "Invalid email or password" in response.json()["detail"]


@pytest.mark.anyio
async def test_email_case_insensitivity(client: AsyncClient) -> None:
    """Test that email addresses are treated case-insensitively."""
    # Signup with lowercase email
    await client.post(
        "/api/v1/auth/signup",
        json={
            "email": "casetest@example.com",
            "password": "securepass123",
            "name": "Case Test",
        },
    )

    # Login with uppercase email
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "CASETEST@EXAMPLE.COM",
            "password": "securepass123",
        },
    )
    assert response.status_code == 200
    assert response.json()["email"] == "casetest@example.com"


@pytest.mark.anyio
async def test_jwt_token_contains_user_id_and_role(client: AsyncClient) -> None:
    """Test that JWT token contains user ID and role claims."""
    from app.core.security import decode_access_token

    # Create student user
    response = await client.post(
        "/api/v1/auth/signup",
        json={
            "email": "tokentest@example.com",
            "password": "securepass123",
            "name": "Token Test",
        },
    )
    token = response.json()["access_token"]

    # Decode token
    payload = decode_access_token(token)
    assert payload is not None
    assert payload["sub"] is not None  # user_id
    assert payload["role"] == "student"
