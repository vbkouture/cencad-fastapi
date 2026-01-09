"""Tests for contact form endpoints."""

from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from app.core.security import hash_password
from app.db import UserRepository, get_database
from app.domain.contact_forms.value_objects import ContactFormStatus
from app.domain.users.value_objects import UserRole


@pytest.fixture
async def admin_token(client: AsyncClient) -> str:
    """Create an admin user and return their access token."""
    db = get_database()
    user_repo = UserRepository(db)

    hashed_pwd = hash_password("adminpass123")
    await user_repo.create_user(
        email="admin@example.com",
        name="Admin User",
        hashed_password=hashed_pwd,
        role=UserRole.ADMIN,
    )

    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "admin@example.com",
            "password": "adminpass123",
        },
    )
    return response.json()["access_token"]


@pytest.mark.anyio
async def test_submit_contact_form(client: AsyncClient) -> None:
    """Test submitting a contact form."""
    with patch(
        "app.api.v1.routers.contact_forms.send_contact_form_email", new_callable=AsyncMock
    ) as mock_email:
        mock_email.return_value = True

        response = await client.post(
            "/api/v1/contact-forms",
            json={
                "name": "Test User",
                "email": "test@example.com",
                "subject": "Test Subject",
                "message": "Test Message",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["status"] == ContactFormStatus.PENDING
        assert data["history"] == []
        assert mock_email.called


@pytest.mark.anyio
async def test_update_contact_form_status(client: AsyncClient, admin_token: str) -> None:
    """Test updating the status of a contact form."""
    # 1. Submit a form
    with patch("app.api.v1.routers.contact_forms.send_contact_form_email", new_callable=AsyncMock):
        create_res = await client.post(
            "/api/v1/contact-forms",
            json={
                "name": "Status Test",
                "email": "status@example.com",
                "subject": "Status Subject",
                "message": "Status Message",
            },
        )
        form_id = create_res.json()["id"]

    # 2. Update status to READ
    response = await client.patch(
        f"/api/v1/contact-forms/{form_id}/status",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "status": ContactFormStatus.READ,
            "note": "Read by admin",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == ContactFormStatus.READ
    assert len(data["history"]) == 1
    assert data["history"][0]["status"] == ContactFormStatus.READ
    assert data["history"][0]["note"] == "Read by admin"


@pytest.mark.anyio
async def test_admin_list_contact_forms(client: AsyncClient, admin_token: str) -> None:
    """Test admin listing contact forms shows status."""
    # Submit one form
    with patch("app.api.v1.routers.contact_forms.send_contact_form_email", new_callable=AsyncMock):
        await client.post(
            "/api/v1/contact-forms",
            json={
                "name": "List Test",
                "email": "list@example.com",
                "subject": "List Subject",
                "message": "List Message",
            },
        )

    response = await client.get(
        "/api/v1/contact-forms",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert "status" in data[0]
