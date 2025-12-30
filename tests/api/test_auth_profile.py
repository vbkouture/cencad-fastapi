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


# ==================== CHANGE PASSWORD - VALIDATION EDGE CASES ====================


@pytest.mark.anyio
async def test_change_password_new_password_too_short(client: AsyncClient) -> None:
    """Test password change fails when new password is too short (< 8 chars)."""
    signup_response = await client.post(
        "/api/v1/auth/signup",
        json={
            "email": "shortpass@example.com",
            "password": "validpassword123",
            "name": "Short Pass Test",
        },
    )
    token = signup_response.json()["access_token"]

    response = await client.post(
        "/api/v1/auth/change-password",
        json={
            "current_password": "validpassword123",
            "new_password": "short",  # Only 5 chars, min is 8
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 422  # Validation error


@pytest.mark.anyio
async def test_change_password_new_password_too_long(client: AsyncClient) -> None:
    """Test password change fails when new password exceeds max length (> 100 chars)."""
    signup_response = await client.post(
        "/api/v1/auth/signup",
        json={
            "email": "longpass@example.com",
            "password": "validpassword123",
            "name": "Long Pass Test",
        },
    )
    token = signup_response.json()["access_token"]

    response = await client.post(
        "/api/v1/auth/change-password",
        json={
            "current_password": "validpassword123",
            "new_password": "a" * 101,  # 101 chars, max is 100
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 422  # Validation error


@pytest.mark.anyio
async def test_change_password_same_as_current(client: AsyncClient) -> None:
    """Test password change when new password is same as current (should succeed or fail based on policy)."""
    signup_response = await client.post(
        "/api/v1/auth/signup",
        json={
            "email": "samepass@example.com",
            "password": "samepassword123",
            "name": "Same Pass Test",
        },
    )
    token = signup_response.json()["access_token"]

    response = await client.post(
        "/api/v1/auth/change-password",
        json={
            "current_password": "samepassword123",
            "new_password": "samepassword123",  # Same as current
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    # Current implementation allows same password - adjust if policy changes
    assert response.status_code == 200


@pytest.mark.anyio
async def test_change_password_empty_current_password(client: AsyncClient) -> None:
    """Test password change fails with empty current password."""
    signup_response = await client.post(
        "/api/v1/auth/signup",
        json={
            "email": "emptypass@example.com",
            "password": "validpassword123",
            "name": "Empty Pass Test",
        },
    )
    token = signup_response.json()["access_token"]

    response = await client.post(
        "/api/v1/auth/change-password",
        json={
            "current_password": "",
            "new_password": "newpassword456",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    # Empty password won't match hash - returns 401
    assert response.status_code == 401


@pytest.mark.anyio
async def test_change_password_invalid_token(client: AsyncClient) -> None:
    """Test password change fails with invalid/malformed JWT token."""
    response = await client.post(
        "/api/v1/auth/change-password",
        json={
            "current_password": "oldpassword123",
            "new_password": "newpassword456",
        },
        headers={"Authorization": "Bearer invalid.jwt.token"},
    )
    assert response.status_code in [401, 403]  # Unauthorized or Forbidden


# ==================== UPDATE PROFILE - VALIDATION EDGE CASES ====================


@pytest.mark.anyio
async def test_update_profile_empty_name(client: AsyncClient) -> None:
    """Test profile update fails with empty name."""
    signup_response = await client.post(
        "/api/v1/auth/signup",
        json={
            "email": "emptyname@example.com",
            "password": "password123",
            "name": "Original Name",
        },
    )
    token = signup_response.json()["access_token"]

    response = await client.patch(
        "/api/v1/auth/profile",
        json={"name": ""},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 422  # Validation error - min_length=1


@pytest.mark.anyio
async def test_update_profile_name_too_long(client: AsyncClient) -> None:
    """Test profile update fails when name exceeds max length (> 200 chars)."""
    signup_response = await client.post(
        "/api/v1/auth/signup",
        json={
            "email": "longname@example.com",
            "password": "password123",
            "name": "Original Name",
        },
    )
    token = signup_response.json()["access_token"]

    response = await client.patch(
        "/api/v1/auth/profile",
        json={"name": "a" * 201},  # 201 chars, max is 200
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 422  # Validation error


@pytest.mark.anyio
async def test_update_profile_whitespace_only_name(client: AsyncClient) -> None:
    """Test profile update with whitespace-only name."""
    signup_response = await client.post(
        "/api/v1/auth/signup",
        json={
            "email": "whitespace@example.com",
            "password": "password123",
            "name": "Original Name",
        },
    )
    token = signup_response.json()["access_token"]

    response = await client.patch(
        "/api/v1/auth/profile",
        json={"name": "   "},  # Whitespace only
        headers={"Authorization": f"Bearer {token}"},
    )
    # Current implementation allows whitespace - may want to add validation
    assert response.status_code in [200, 422]


@pytest.mark.anyio
async def test_update_profile_special_characters(client: AsyncClient) -> None:
    """Test profile update with special characters, unicode, and emojis."""
    signup_response = await client.post(
        "/api/v1/auth/signup",
        json={
            "email": "specialchars@example.com",
            "password": "password123",
            "name": "Original Name",
        },
    )
    token = signup_response.json()["access_token"]

    # Test unicode and special characters
    response = await client.patch(
        "/api/v1/auth/profile",
        json={"name": "José María 日本語 🚀"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200

    # Verify name was updated correctly
    login_response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "specialchars@example.com",
            "password": "password123",
        },
    )
    assert login_response.json()["name"] == "José María 日本語 🚀"


@pytest.mark.anyio
async def test_update_profile_invalid_token(client: AsyncClient) -> None:
    """Test profile update fails with invalid/malformed JWT token."""
    response = await client.patch(
        "/api/v1/auth/profile",
        json={"name": "New Name"},
        headers={"Authorization": "Bearer invalid.jwt.token"},
    )
    assert response.status_code in [401, 403]  # Unauthorized or Forbidden


# ==================== CROSS-USER SECURITY TESTS ====================


@pytest.mark.anyio
async def test_cannot_change_another_users_password(client: AsyncClient) -> None:
    """Test that user A cannot change user B's password using their own token."""
    # Create user A
    signup_a = await client.post(
        "/api/v1/auth/signup",
        json={
            "email": "usera_pass@example.com",
            "password": "userApassword123",
            "name": "User A",
        },
    )
    token_a = signup_a.json()["access_token"]

    # Create user B
    await client.post(
        "/api/v1/auth/signup",
        json={
            "email": "userb_pass@example.com",
            "password": "userBpassword123",
            "name": "User B",
        },
    )

    # User A tries to change password using User B's current password
    # (attempting to guess or knowing B's password shouldn't work with A's token)
    response = await client.post(
        "/api/v1/auth/change-password",
        json={
            "current_password": "userBpassword123",  # User B's password
            "new_password": "hackedpassword123",
        },
        headers={"Authorization": f"Bearer {token_a}"},  # User A's token
    )
    # Should fail because token belongs to User A, not User B
    assert response.status_code == 401
    assert "Current password is incorrect" in response.json()["detail"]

    # Verify User B can still login with original password
    login_b = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "userb_pass@example.com",
            "password": "userBpassword123",
        },
    )
    assert login_b.status_code == 200


@pytest.mark.anyio
async def test_cannot_update_another_users_profile(client: AsyncClient) -> None:
    """Test that user A cannot update user B's profile using their own token."""
    # Create user A
    signup_a = await client.post(
        "/api/v1/auth/signup",
        json={
            "email": "usera_profile@example.com",
            "password": "password123",
            "name": "User A Original",
        },
    )
    token_a = signup_a.json()["access_token"]

    # Create user B
    await client.post(
        "/api/v1/auth/signup",
        json={
            "email": "userb_profile@example.com",
            "password": "password123",
            "name": "User B Original",
        },
    )

    # User A updates profile (should only affect User A)
    response = await client.patch(
        "/api/v1/auth/profile",
        json={"name": "Hacked Name"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert response.status_code == 200

    # Verify User B's name is unchanged
    login_b = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "userb_profile@example.com",
            "password": "password123",
        },
    )
    assert login_b.status_code == 200
    assert login_b.json()["name"] == "User B Original"  # Unchanged

    # Verify User A's name was changed (to confirm the endpoint works)
    login_a = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "usera_profile@example.com",
            "password": "password123",
        },
    )
    assert login_a.json()["name"] == "Hacked Name"
