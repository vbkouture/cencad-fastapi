"""Tests for user profile management endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.anyio
async def test_change_password_success(client: AsyncClient) -> None:
    """Test successful password change."""
    # Create user
    signup_response = await client.post(
        "/api/v1/auth/signup",
        json={
            "email": "changepass@example.com",
            "password": "oldpassword123",
            "name": "Change Password Test",
        },
    )
    token = signup_response.json()["access_token"]

    # Change password
    response = await client.post(
        "/api/v1/auth/change-password",
        json={
            "current_password": "oldpassword123",
            "new_password": "newpassword456",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Password changed successfully"

    # Verify old password no longer works
    old_login = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "changepass@example.com",
            "password": "oldpassword123",
        },
    )
    assert old_login.status_code == 401

    # Verify new password works
    new_login = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "changepass@example.com",
            "password": "newpassword456",
        },
    )
    assert new_login.status_code == 200


@pytest.mark.anyio
async def test_change_password_wrong_current_password(client: AsyncClient) -> None:
    """Test password change fails with incorrect current password."""
    # Create user
    signup_response = await client.post(
        "/api/v1/auth/signup",
        json={
            "email": "wrongcurrent@example.com",
            "password": "correctpass123",
            "name": "Wrong Current Test",
        },
    )
    token = signup_response.json()["access_token"]

    # Try to change with wrong current password
    response = await client.post(
        "/api/v1/auth/change-password",
        json={
            "current_password": "wrongpassword",
            "new_password": "newpassword456",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 401
    assert "Current password is incorrect" in response.json()["detail"]


@pytest.mark.anyio
async def test_change_password_requires_auth(client: AsyncClient) -> None:
    """Test password change requires authentication."""
    response = await client.post(
        "/api/v1/auth/change-password",
        json={
            "current_password": "oldpassword123",
            "new_password": "newpassword456",
        },
    )
    assert response.status_code == 403  # Forbidden without auth token


@pytest.mark.anyio
async def test_update_profile_name(client: AsyncClient) -> None:
    """Test updating user profile name."""
    # Create user
    signup_response = await client.post(
        "/api/v1/auth/signup",
        json={
            "email": "updatename@example.com",
            "password": "password123",
            "name": "Original Name",
        },
    )
    token = signup_response.json()["access_token"]

    # Update name
    response = await client.patch(
        "/api/v1/auth/profile",
        json={"name": "Updated Name"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Profile updated successfully"

    # Verify name updated in login response
    login_response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "updatename@example.com",
            "password": "password123",
        },
    )
    assert login_response.json()["name"] == "Updated Name"


@pytest.mark.anyio
async def test_update_profile_requires_auth(client: AsyncClient) -> None:
    """Test profile update requires authentication."""
    response = await client.patch(
        "/api/v1/auth/profile",
        json={"name": "New Name"},
    )
    assert response.status_code == 403  # Forbidden without auth token
