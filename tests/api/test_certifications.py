"""Tests for certifications endpoints."""

from typing import Any

import pytest
from httpx import AsyncClient

from app.core.security import create_access_token


@pytest.fixture
async def admin_token() -> str:
    """Create a test admin user and return a valid access token."""
    from app.domain.users.value_objects import UserRole

    return create_access_token(data={"sub": "admin@test.com", "role": UserRole.ADMIN})


@pytest.fixture
async def user_token() -> str:
    """Create a normal user and return token."""
    from app.domain.users.value_objects import UserRole

    return create_access_token(data={"sub": "user@test.com", "role": UserRole.STUDENT})


@pytest.fixture
async def vendor(setup_db: Any) -> dict[str, Any]:
    """Create a test vendor."""
    from app.db import get_database

    db = get_database()
    vendor_doc = {
        "name": "Test Vendor Cert",
        "description": "Test Desc",
        "created_at": "2023-01-01",
        "updated_at": "2023-01-01",
    }
    res = await db["vendors"].insert_one(vendor_doc)
    vendor_doc["_id"] = str(res.inserted_id)
    return vendor_doc


@pytest.mark.anyio
async def test_create_certification(
    client: AsyncClient, admin_token: str, vendor: dict[str, Any]
) -> None:
    """Test creating a certification as admin."""
    response = await client.post(
        "/api/v1/certifications",
        json={
            "vendor_id": vendor["_id"],
            "name": "Certified Tester",
            "description": "Certified Tester Description",
            "url": "http://test.com",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Certified Tester"
    assert data["description"] == "Certified Tester Description"
    assert data["vendor_id"] == vendor["_id"]


@pytest.mark.anyio
async def test_create_certification_invalid_vendor(client: AsyncClient, admin_token: str) -> None:
    """Test creating a certification with non-existent vendor."""
    response = await client.post(
        "/api/v1/certifications",
        json={
            "vendor_id": "000000000000000000000000",
            "name": "Invalid Vendor Cert",
            "description": "Invalid Vendor",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 409
    assert "not exist" in response.json()["detail"]


@pytest.mark.anyio
async def test_create_certification_unauthorized(
    client: AsyncClient, user_token: str, vendor: dict[str, Any]
) -> None:
    """Test creating a certification as non-admin."""
    response = await client.post(
        "/api/v1/certifications",
        json={
            "vendor_id": vendor["_id"],
            "name": "Hacker Cert",
            "description": "Hacker Cert Desc",
        },
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 403  # or 401 depending on impl, usually 403 for role
    # Assuming require_admin raises 403 if role doesn't match or 401 if invalid.
    # Let's check require_admin source if needed, but 403 is standard.


@pytest.mark.anyio
async def test_get_certifications(
    client: AsyncClient, admin_token: str, vendor: dict[str, Any]
) -> None:
    """Test getting all certifications."""
    # Create one first
    await client.post(
        "/api/v1/certifications",
        json={"vendor_id": vendor["_id"], "name": "Cert 1", "description": "Cert 1 Desc"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    response = await client.get("/api/v1/certifications")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert any(d["name"] == "Cert 1" for d in data)


@pytest.mark.anyio
async def test_update_certification(
    client: AsyncClient, admin_token: str, vendor: dict[str, Any]
) -> None:
    """Test updating a certification."""
    # Create
    create_res = await client.post(
        "/api/v1/certifications",
        json={"vendor_id": vendor["_id"], "name": "Old Name", "description": "Old Desc"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    cert_id = create_res.json()["id"]

    # Update
    response = await client.put(
        f"/api/v1/certifications/{cert_id}",
        json={"name": "New Name", "description": "New Desc", "url": "http://new.com"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "New Name"
    assert data["description"] == "New Desc"
    assert data["url"] == "http://new.com"
    assert data["vendor_id"] == vendor["_id"]


@pytest.mark.anyio
async def test_delete_certification(
    client: AsyncClient, admin_token: str, vendor: dict[str, Any]
) -> None:
    """Test deleting a certification."""
    # Create
    create_res = await client.post(
        "/api/v1/certifications",
        json={"vendor_id": vendor["_id"], "name": "To Delete", "description": "To Delete Desc"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    cert_id = create_res.json()["id"]

    # Delete
    response = await client.delete(
        f"/api/v1/certifications/{cert_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200

    # Verify gone
    get_res = await client.get(f"/api/v1/certifications/{cert_id}")
    assert get_res.status_code == 404
