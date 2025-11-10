"""Tests for vendors endpoints."""

import pytest
from fastapi import status
from httpx import AsyncClient
from typing import AsyncGenerator

from app.db import get_database
from app.db.vendor_repository import VendorRepository


@pytest.fixture
async def vendor_repo(setup_db: AsyncGenerator[None, None]) -> AsyncGenerator[VendorRepository, None]:
    """Get vendor repository with setup."""
    db = get_database()
    repo = VendorRepository(db)
    await repo.create_indexes()
    yield repo


@pytest.fixture
async def admin_token() -> str:
    """Create admin JWT token for testing."""
    from app.core.security import create_access_token
    from app.domain.users.value_objects import UserRole

    token = create_access_token(
        data={"sub": "test_admin_id", "role": UserRole.ADMIN}
    )
    return token


@pytest.fixture
async def student_token() -> str:
    """Create student JWT token for testing."""
    from app.core.security import create_access_token
    from app.domain.users.value_objects import UserRole

    token = create_access_token(
        data={"sub": "test_student_id", "role": UserRole.STUDENT}
    )
    return token


@pytest.fixture
async def cleanup_vendors(vendor_repo: VendorRepository) -> AsyncGenerator[None, None]:
    """Clean up test vendors after each test."""
    yield
    await vendor_repo.collection.delete_many({})  # type: ignore


# ============================================================================
# READ ENDPOINTS - No Authentication Required
# ============================================================================


class TestGetAllVendors:
    """Tests for GET /vendors endpoint."""

    @pytest.mark.anyio
    async def test_get_empty_list(self, client: AsyncClient, cleanup_vendors: AsyncGenerator[None, None]) -> None:
        """Test getting vendors when none exist."""
        response = await client.get("/api/v1/vendors")
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == []

    @pytest.mark.anyio
    async def test_get_all_vendors_success(
        self, client: AsyncClient, vendor_repo: VendorRepository, cleanup_vendors: AsyncGenerator[None, None]
    ) -> None:
        """Test getting all vendors successfully."""
        await vendor_repo.create_vendor(
            name="Vendor One", description="First vendor"
        )
        await vendor_repo.create_vendor(
            name="Vendor Two", description="Second vendor"
        )
        response = await client.get("/api/v1/vendors")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 2

    @pytest.mark.anyio
    async def test_get_all_vendors_multiple(
        self, client: AsyncClient, vendor_repo: VendorRepository, cleanup_vendors: AsyncGenerator[None, None]
    ) -> None:
        """Test getting many vendors."""
        for i in range(10):
            await vendor_repo.create_vendor(
                name=f"Vendor {i}", description=f"Description {i}"
            )
        response = await client.get("/api/v1/vendors")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()) == 10


class TestGetSingleVendor:
    """Tests for GET /vendors/{id} endpoint."""

    @pytest.mark.anyio
    async def test_get_vendor_by_id_success(
        self, client: AsyncClient, vendor_repo: VendorRepository, cleanup_vendors: AsyncGenerator[None, None]
    ) -> None:
        """Test getting a vendor by valid ID."""
        vendor = await vendor_repo.create_vendor(
            name="Azure Vendor", description="Microsoft Azure services"
        )
        response = await client.get(
            f"/api/v1/vendors/{str(vendor['_id'])}"
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "Azure Vendor"

    @pytest.mark.anyio
    async def test_get_vendor_by_id_invalid_id(
        self, client: AsyncClient, cleanup_vendors: AsyncGenerator[None, None]
    ) -> None:
        """Test getting vendor with invalid ID."""
        from bson import ObjectId

        invalid_id = str(ObjectId())
        response = await client.get(f"/api/v1/vendors/{invalid_id}")
        assert response.status_code == status.HTTP_404_NOT_FOUND


# ============================================================================
# CREATE ENDPOINT - Admin Only
# ============================================================================


class TestCreateVendor:
    """Tests for POST /vendors endpoint."""

    @pytest.mark.anyio
    async def test_create_vendor_success(
        self, client: AsyncClient, admin_token: str, cleanup_vendors: AsyncGenerator[None, None]
    ) -> None:
        """Test creating vendor with valid data and admin token."""
        payload = {
            "name": "Coursera",
            "description": "Online learning platform",
            "logo": "https://example.com/coursera-logo.png",
        }
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = await client.post(
            "/api/v1/vendors", json=payload, headers=headers
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == "Coursera"
        assert data["logo"] == "https://example.com/coursera-logo.png"

    @pytest.mark.anyio
    async def test_create_vendor_without_logo(
        self, client: AsyncClient, admin_token: str, cleanup_vendors: AsyncGenerator[None, None]
    ) -> None:
        """Test creating vendor without optional logo field."""
        payload = {
            "name": "Udemy",
            "description": "Online course platform",
        }
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = await client.post(
            "/api/v1/vendors", json=payload, headers=headers
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == "Udemy"
        assert data["logo"] is None

    @pytest.mark.anyio
    async def test_create_vendor_missing_auth(
        self, client: AsyncClient, cleanup_vendors: AsyncGenerator[None, None]
    ) -> None:
        """Test creating vendor without authentication."""
        payload = {"name": "Vendor", "description": "Description"}
        response = await client.post("/api/v1/vendors", json=payload)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.anyio
    async def test_create_vendor_student_token(
        self, client: AsyncClient, student_token: str, cleanup_vendors: AsyncGenerator[None, None]
    ) -> None:
        """Test creating vendor with student token (non-admin)."""
        payload = {"name": "Vendor", "description": "Description"}
        headers = {"Authorization": f"Bearer {student_token}"}
        response = await client.post(
            "/api/v1/vendors", json=payload, headers=headers
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.anyio
    async def test_create_vendor_duplicate_name(
        self, client: AsyncClient, admin_token: str, vendor_repo: VendorRepository, cleanup_vendors: AsyncGenerator[None, None]
    ) -> None:
        """Test creating vendor with duplicate name."""
        await vendor_repo.create_vendor(
            name="Duplicate Name", description="First description"
        )
        payload = {"name": "Duplicate Name", "description": "Second description"}
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = await client.post(
            "/api/v1/vendors", json=payload, headers=headers
        )
        assert response.status_code == status.HTTP_409_CONFLICT

    @pytest.mark.anyio
    async def test_create_vendor_name_empty(
        self, client: AsyncClient, admin_token: str, cleanup_vendors: AsyncGenerator[None, None]
    ) -> None:
        """Test creating vendor with empty name."""
        payload = {"name": "", "description": "Description"}
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = await client.post(
            "/api/v1/vendors", json=payload, headers=headers
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.anyio
    async def test_create_vendor_name_too_long(
        self, client: AsyncClient, admin_token: str, cleanup_vendors: AsyncGenerator[None, None]
    ) -> None:
        """Test creating vendor with name exceeding max length."""
        payload = {"name": "a" * 201, "description": "Description"}
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = await client.post(
            "/api/v1/vendors", json=payload, headers=headers
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.anyio
    async def test_create_vendor_description_empty(
        self, client: AsyncClient, admin_token: str, cleanup_vendors: AsyncGenerator[None, None]
    ) -> None:
        """Test creating vendor with empty description."""
        payload = {"name": "Vendor", "description": ""}
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = await client.post(
            "/api/v1/vendors", json=payload, headers=headers
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.anyio
    async def test_create_vendor_missing_name(
        self, client: AsyncClient, admin_token: str, cleanup_vendors: AsyncGenerator[None, None]
    ) -> None:
        """Test creating vendor without name field."""
        payload = {"description": "Description"}
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = await client.post(
            "/api/v1/vendors", json=payload, headers=headers
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.anyio
    async def test_create_vendor_missing_description(
        self, client: AsyncClient, admin_token: str, cleanup_vendors: AsyncGenerator[None, None]
    ) -> None:
        """Test creating vendor without description field."""
        payload = {"name": "Vendor"}
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = await client.post(
            "/api/v1/vendors", json=payload, headers=headers
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.anyio
    async def test_create_vendor_max_length_name(
        self, client: AsyncClient, admin_token: str, cleanup_vendors: AsyncGenerator[None, None]
    ) -> None:
        """Test creating vendor with maximum valid name length."""
        payload = {"name": "a" * 200, "description": "Description"}
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = await client.post(
            "/api/v1/vendors", json=payload, headers=headers
        )
        assert response.status_code == status.HTTP_201_CREATED

    @pytest.mark.anyio
    async def test_create_vendor_max_length_description(
        self, client: AsyncClient, admin_token: str, cleanup_vendors: AsyncGenerator[None, None]
    ) -> None:
        """Test creating vendor with maximum valid description length."""
        payload = {"name": "Vendor", "description": "a" * 1000}
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = await client.post(
            "/api/v1/vendors", json=payload, headers=headers
        )
        assert response.status_code == status.HTTP_201_CREATED

    @pytest.mark.anyio
    async def test_create_vendor_unicode_characters(
        self, client: AsyncClient, admin_token: str, cleanup_vendors: AsyncGenerator[None, None]
    ) -> None:
        """Test creating vendor with unicode characters."""
        payload = {
            "name": "厂商 (Vendor)",
            "description": "Provide amazing 课程 and 平台 🚀",
        }
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = await client.post(
            "/api/v1/vendors", json=payload, headers=headers
        )
        assert response.status_code == status.HTTP_201_CREATED


# ============================================================================
# UPDATE ENDPOINT - Admin Only
# ============================================================================


class TestUpdateVendor:
    """Tests for PUT /vendors/{id} endpoint."""

    @pytest.mark.anyio
    async def test_update_vendor_all_fields(
        self, client: AsyncClient, admin_token: str, vendor_repo: VendorRepository, cleanup_vendors: AsyncGenerator[None, None]
    ) -> None:
        """Test updating vendor with all fields."""
        vendor = await vendor_repo.create_vendor(
            name="Old Name", description="Old description", logo="http://old.com/logo.png"
        )
        payload = {
            "name": "New Name",
            "description": "New description",
            "logo": "http://new.com/logo.png",
        }
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = await client.put(
            f"/api/v1/vendors/{str(vendor['_id'])}",
            json=payload,
            headers=headers,
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "New Name"
        assert data["description"] == "New description"
        assert data["logo"] == "http://new.com/logo.png"

    @pytest.mark.anyio
    async def test_update_vendor_name_only(
        self, client: AsyncClient, admin_token: str, vendor_repo: VendorRepository, cleanup_vendors: AsyncGenerator[None, None]
    ) -> None:
        """Test updating only the vendor name."""
        vendor = await vendor_repo.create_vendor(
            name="Old Name", description="Original description"
        )
        payload = {"name": "New Name"}
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = await client.put(
            f"/api/v1/vendors/{str(vendor['_id'])}",
            json=payload,
            headers=headers,
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "New Name"
        assert data["description"] == "Original description"

    @pytest.mark.anyio
    async def test_update_vendor_logo_only(
        self, client: AsyncClient, admin_token: str, vendor_repo: VendorRepository, cleanup_vendors: AsyncGenerator[None, None]
    ) -> None:
        """Test updating only the vendor logo."""
        vendor = await vendor_repo.create_vendor(
            name="Vendor", description="Description", logo="http://old.com/logo.png"
        )
        payload = {"logo": "http://new.com/logo.png"}
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = await client.put(
            f"/api/v1/vendors/{str(vendor['_id'])}",
            json=payload,
            headers=headers,
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["logo"] == "http://new.com/logo.png"
        assert data["name"] == "Vendor"

    @pytest.mark.anyio
    async def test_update_vendor_not_found(
        self, client: AsyncClient, admin_token: str, cleanup_vendors: AsyncGenerator[None, None]
    ) -> None:
        """Test updating non-existent vendor."""
        from bson import ObjectId

        invalid_id = str(ObjectId())
        payload = {"name": "New Name"}
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = await client.put(
            f"/api/v1/vendors/{invalid_id}",
            json=payload,
            headers=headers,
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.anyio
    async def test_update_vendor_duplicate_name(
        self, client: AsyncClient, admin_token: str, vendor_repo: VendorRepository, cleanup_vendors: AsyncGenerator[None, None]
    ) -> None:
        """Test updating vendor to a name that already exists."""
        await vendor_repo.create_vendor(
            name="Vendor 1", description="Description 1"
        )
        vendor2 = await vendor_repo.create_vendor(
            name="Vendor 2", description="Description 2"
        )
        payload = {"name": "Vendor 1"}
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = await client.put(
            f"/api/v1/vendors/{str(vendor2['_id'])}",
            json=payload,
            headers=headers,
        )
        assert response.status_code == status.HTTP_409_CONFLICT

    @pytest.mark.anyio
    async def test_update_vendor_missing_auth(
        self, client: AsyncClient, vendor_repo: VendorRepository, cleanup_vendors: AsyncGenerator[None, None]
    ) -> None:
        """Test updating vendor without authentication."""
        vendor = await vendor_repo.create_vendor(
            name="Name", description="Description"
        )
        payload = {"name": "New Name"}
        response = await client.put(
            f"/api/v1/vendors/{str(vendor['_id'])}", json=payload
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.anyio
    async def test_update_vendor_student_token(
        self, client: AsyncClient, student_token: str, vendor_repo: VendorRepository, cleanup_vendors: AsyncGenerator[None, None]
    ) -> None:
        """Test updating vendor with student token."""
        vendor = await vendor_repo.create_vendor(
            name="Name", description="Description"
        )
        payload = {"name": "New Name"}
        headers = {"Authorization": f"Bearer {student_token}"}
        response = await client.put(
            f"/api/v1/vendors/{str(vendor['_id'])}",
            json=payload,
            headers=headers,
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN


# ============================================================================
# DELETE ENDPOINT - Admin Only
# ============================================================================


class TestDeleteVendor:
    """Tests for DELETE /vendors/{id} endpoint."""

    @pytest.mark.anyio
    async def test_delete_vendor_success(
        self, client: AsyncClient, admin_token: str, vendor_repo: VendorRepository, cleanup_vendors: AsyncGenerator[None, None]
    ) -> None:
        """Test successfully deleting a vendor."""
        vendor = await vendor_repo.create_vendor(
            name="Vendor to Delete", description="This will be deleted"
        )
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = await client.delete(
            f"/api/v1/vendors/{str(vendor['_id'])}", headers=headers
        )
        assert response.status_code == status.HTTP_200_OK
        deleted_vendor = await vendor_repo.find_by_id(str(vendor["_id"]))
        assert deleted_vendor is None

    @pytest.mark.anyio
    async def test_delete_vendor_not_found(
        self, client: AsyncClient, admin_token: str, cleanup_vendors: AsyncGenerator[None, None]
    ) -> None:
        """Test deleting non-existent vendor."""
        from bson import ObjectId

        invalid_id = str(ObjectId())
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = await client.delete(
            f"/api/v1/vendors/{invalid_id}", headers=headers
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.anyio
    async def test_delete_vendor_missing_auth(
        self, client: AsyncClient, vendor_repo: VendorRepository, cleanup_vendors: AsyncGenerator[None, None]
    ) -> None:
        """Test deleting vendor without authentication."""
        vendor = await vendor_repo.create_vendor(
            name="Vendor", description="Description"
        )
        response = await client.delete(
            f"/api/v1/vendors/{str(vendor['_id'])}"
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.anyio
    async def test_delete_vendor_student_token(
        self, client: AsyncClient, student_token: str, vendor_repo: VendorRepository, cleanup_vendors: AsyncGenerator[None, None]
    ) -> None:
        """Test deleting vendor with student token."""
        vendor = await vendor_repo.create_vendor(
            name="Vendor", description="Description"
        )
        headers = {"Authorization": f"Bearer {student_token}"}
        response = await client.delete(
            f"/api/v1/vendors/{str(vendor['_id'])}", headers=headers
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN


# ============================================================================
# Integration Tests
# ============================================================================


class TestVendorIntegration:
    """Integration tests combining multiple operations."""

    @pytest.mark.anyio
    async def test_full_crud_workflow(
        self, client: AsyncClient, admin_token: str, cleanup_vendors: AsyncGenerator[None, None]
    ) -> None:
        """Test complete CRUD workflow."""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # CREATE
        create_payload = {
            "name": "Pluralsight",
            "description": "Technology skills platform",
            "logo": "https://example.com/pluralsight.png",
        }
        create_response = await client.post(
            "/api/v1/vendors", json=create_payload, headers=headers
        )
        assert create_response.status_code == status.HTTP_201_CREATED
        vendor_id = create_response.json()["id"]

        # READ
        read_response = await client.get(f"/api/v1/vendors/{vendor_id}")
        assert read_response.status_code == status.HTTP_200_OK
        assert read_response.json()["name"] == "Pluralsight"

        # UPDATE
        update_payload = {"description": "Updated description"}
        update_response = await client.put(
            f"/api/v1/vendors/{vendor_id}",
            json=update_payload,
            headers=headers,
        )
        assert update_response.status_code == status.HTTP_200_OK

        # DELETE
        delete_response = await client.delete(
            f"/api/v1/vendors/{vendor_id}", headers=headers
        )
        assert delete_response.status_code == status.HTTP_200_OK

        # Verify deleted
        final_read = await client.get(f"/api/v1/vendors/{vendor_id}")
        assert final_read.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.anyio
    async def test_public_read_after_admin_operations(
        self, client: AsyncClient, admin_token: str, cleanup_vendors: AsyncGenerator[None, None]
    ) -> None:
        """Test that public read works after admin creates."""
        headers = {"Authorization": f"Bearer {admin_token}"}
        payload = {"name": "Public Test", "description": "Test"}
        response = await client.post(
            "/api/v1/vendors", json=payload, headers=headers
        )
        vendor_id = response.json()["id"]

        # Public read without auth
        public_read = await client.get(f"/api/v1/vendors/{vendor_id}")
        assert public_read.status_code == status.HTTP_200_OK
        assert public_read.json()["name"] == "Public Test"

    @pytest.mark.anyio
    async def test_student_cannot_create_but_can_read(
        self, client: AsyncClient, admin_token: str, student_token: str, cleanup_vendors: AsyncGenerator[None, None]
    ) -> None:
        """Test that students can read but cannot create."""
        headers_admin = {"Authorization": f"Bearer {admin_token}"}
        headers_student = {"Authorization": f"Bearer {student_token}"}
        
        # Admin creates
        payload = {"name": "Test Vendor", "description": "Test"}
        response = await client.post(
            "/api/v1/vendors", json=payload, headers=headers_admin
        )
        assert response.status_code == status.HTTP_201_CREATED
        vendor_id = response.json()["id"]

        # Student reads successfully
        read_response = await client.get(f"/api/v1/vendors/{vendor_id}")
        assert read_response.status_code == status.HTTP_200_OK

        # Student cannot create
        create_payload = {"name": "Illegal Vendor", "description": "Test"}
        create_response = await client.post(
            "/api/v1/vendors", json=create_payload, headers=headers_student
        )
        assert create_response.status_code == status.HTTP_403_FORBIDDEN
