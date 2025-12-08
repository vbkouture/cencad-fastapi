"""Tests for job roles endpoints."""

from collections.abc import AsyncGenerator

import pytest
from fastapi import status
from httpx import AsyncClient

from app.db import get_database
from app.db.job_role_repository import JobRoleRepository


@pytest.fixture
async def job_role_repo(
    setup_db: AsyncGenerator[None, None]
) -> AsyncGenerator[JobRoleRepository, None]:
    """Get job role repository with setup."""
    db = get_database()
    repo = JobRoleRepository(db)
    await repo.create_indexes()
    yield repo


@pytest.fixture
async def admin_token() -> str:
    """Create admin JWT token for testing."""
    from app.core.security import create_access_token
    from app.domain.users.value_objects import UserRole

    token = create_access_token(data={"sub": "test_admin_id", "role": UserRole.ADMIN})
    return token


@pytest.fixture
async def student_token() -> str:
    """Create student JWT token for testing."""
    from app.core.security import create_access_token
    from app.domain.users.value_objects import UserRole

    token = create_access_token(data={"sub": "test_student_id", "role": UserRole.STUDENT})
    return token


@pytest.fixture
async def cleanup_job_roles(job_role_repo: JobRoleRepository) -> AsyncGenerator[None, None]:
    """Clean up test job roles after each test."""
    yield
    await job_role_repo.collection.delete_many({})  # type: ignore


# ============================================================================
# READ ENDPOINTS - No Authentication Required
# ============================================================================


class TestGetAllJobRoles:
    """Tests for GET /job-roles endpoint."""

    @pytest.mark.anyio
    async def test_get_empty_list(
        self, client: AsyncClient, cleanup_job_roles: AsyncGenerator[None, None]
    ) -> None:
        """Test getting job roles when none exist."""
        response = await client.get("/api/v1/job-roles")
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == []

    @pytest.mark.anyio
    async def test_get_all_job_roles_success(
        self,
        client: AsyncClient,
        job_role_repo: JobRoleRepository,
        cleanup_job_roles: AsyncGenerator[None, None],
    ) -> None:
        """Test getting all job roles successfully."""
        await job_role_repo.create_job_role(
            name="Software Engineer", description="Develop software"
        )
        await job_role_repo.create_job_role(name="Data Scientist", description="Analyze data")
        response = await client.get("/api/v1/job-roles")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 2

    @pytest.mark.anyio
    async def test_get_all_job_roles_multiple(
        self,
        client: AsyncClient,
        job_role_repo: JobRoleRepository,
        cleanup_job_roles: AsyncGenerator[None, None],
    ) -> None:
        """Test getting many job roles."""
        for i in range(10):
            await job_role_repo.create_job_role(name=f"Role {i}", description=f"Description {i}")
        response = await client.get("/api/v1/job-roles")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()) == 10


class TestGetSingleJobRole:
    """Tests for GET /job-roles/{id} endpoint."""

    @pytest.mark.anyio
    async def test_get_job_role_by_id_success(
        self,
        client: AsyncClient,
        job_role_repo: JobRoleRepository,
        cleanup_job_roles: AsyncGenerator[None, None],
    ) -> None:
        """Test getting a job role by valid ID."""
        job_role = await job_role_repo.create_job_role(
            name="Product Manager", description="Manage product roadmap"
        )
        response = await client.get(f"/api/v1/job-roles/{str(job_role['_id'])}")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "Product Manager"

    @pytest.mark.anyio
    async def test_get_job_role_by_id_invalid_id(
        self, client: AsyncClient, cleanup_job_roles: AsyncGenerator[None, None]
    ) -> None:
        """Test getting job role with invalid ID."""
        from bson import ObjectId

        invalid_id = str(ObjectId())
        response = await client.get(f"/api/v1/job-roles/{invalid_id}")
        assert response.status_code == status.HTTP_404_NOT_FOUND


# ============================================================================
# CREATE ENDPOINT - Admin Only
# ============================================================================


class TestCreateJobRole:
    """Tests for POST /job-roles endpoint."""

    @pytest.mark.anyio
    async def test_create_job_role_success(
        self, client: AsyncClient, admin_token: str, cleanup_job_roles: AsyncGenerator[None, None]
    ) -> None:
        """Test creating job role with valid data and admin token."""
        payload = {
            "name": "DevOps Engineer",
            "description": "Manage infrastructure and deployments",
        }
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = await client.post("/api/v1/job-roles", json=payload, headers=headers)
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == "DevOps Engineer"

    @pytest.mark.anyio
    async def test_create_job_role_missing_auth(
        self, client: AsyncClient, cleanup_job_roles: AsyncGenerator[None, None]
    ) -> None:
        """Test creating job role without authentication."""
        payload = {"name": "Role", "description": "Description"}
        response = await client.post("/api/v1/job-roles", json=payload)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.anyio
    async def test_create_job_role_student_token(
        self, client: AsyncClient, student_token: str, cleanup_job_roles: AsyncGenerator[None, None]
    ) -> None:
        """Test creating job role with student token (non-admin)."""
        payload = {"name": "Role", "description": "Description"}
        headers = {"Authorization": f"Bearer {student_token}"}
        response = await client.post("/api/v1/job-roles", json=payload, headers=headers)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.anyio
    async def test_create_job_role_duplicate_name(
        self,
        client: AsyncClient,
        admin_token: str,
        job_role_repo: JobRoleRepository,
        cleanup_job_roles: AsyncGenerator[None, None],
    ) -> None:
        """Test creating job role with duplicate name."""
        await job_role_repo.create_job_role(name="Duplicate Name", description="First description")
        payload = {"name": "Duplicate Name", "description": "Second description"}
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = await client.post("/api/v1/job-roles", json=payload, headers=headers)
        assert response.status_code == status.HTTP_409_CONFLICT

    @pytest.mark.anyio
    async def test_create_job_role_name_empty(
        self, client: AsyncClient, admin_token: str, cleanup_job_roles: AsyncGenerator[None, None]
    ) -> None:
        """Test creating job role with empty name."""
        payload = {"name": "", "description": "Description"}
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = await client.post("/api/v1/job-roles", json=payload, headers=headers)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.anyio
    async def test_create_job_role_name_too_long(
        self, client: AsyncClient, admin_token: str, cleanup_job_roles: AsyncGenerator[None, None]
    ) -> None:
        """Test creating job role with name exceeding max length."""
        payload = {"name": "a" * 201, "description": "Description"}
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = await client.post("/api/v1/job-roles", json=payload, headers=headers)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.anyio
    async def test_create_job_role_description_empty(
        self, client: AsyncClient, admin_token: str, cleanup_job_roles: AsyncGenerator[None, None]
    ) -> None:
        """Test creating job role with empty description."""
        payload = {"name": "Role", "description": ""}
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = await client.post("/api/v1/job-roles", json=payload, headers=headers)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.anyio
    async def test_create_job_role_missing_name(
        self, client: AsyncClient, admin_token: str, cleanup_job_roles: AsyncGenerator[None, None]
    ) -> None:
        """Test creating job role without name field."""
        payload = {"description": "Description"}
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = await client.post("/api/v1/job-roles", json=payload, headers=headers)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.anyio
    async def test_create_job_role_missing_description(
        self, client: AsyncClient, admin_token: str, cleanup_job_roles: AsyncGenerator[None, None]
    ) -> None:
        """Test creating job role without description field."""
        payload = {"name": "Role"}
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = await client.post("/api/v1/job-roles", json=payload, headers=headers)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.anyio
    async def test_create_job_role_max_length_name(
        self, client: AsyncClient, admin_token: str, cleanup_job_roles: AsyncGenerator[None, None]
    ) -> None:
        """Test creating job role with maximum valid name length."""
        payload = {"name": "a" * 200, "description": "Description"}
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = await client.post("/api/v1/job-roles", json=payload, headers=headers)
        assert response.status_code == status.HTTP_201_CREATED

    @pytest.mark.anyio
    async def test_create_job_role_max_length_description(
        self, client: AsyncClient, admin_token: str, cleanup_job_roles: AsyncGenerator[None, None]
    ) -> None:
        """Test creating job role with maximum valid description length."""
        payload = {"name": "Role", "description": "a" * 1000}
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = await client.post("/api/v1/job-roles", json=payload, headers=headers)
        assert response.status_code == status.HTTP_201_CREATED

    @pytest.mark.anyio
    async def test_create_job_role_unicode_characters(
        self, client: AsyncClient, admin_token: str, cleanup_job_roles: AsyncGenerator[None, None]
    ) -> None:
        """Test creating job role with unicode characters."""
        payload = {
            "name": "工程师 (Engineer)",
            "description": "Build amazing 产品 and 技术 🚀",
        }
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = await client.post("/api/v1/job-roles", json=payload, headers=headers)
        assert response.status_code == status.HTTP_201_CREATED


# ============================================================================
# UPDATE ENDPOINT - Admin Only
# ============================================================================


class TestUpdateJobRole:
    """Tests for PUT /job-roles/{id} endpoint."""

    @pytest.mark.anyio
    async def test_update_job_role_both_fields(
        self,
        client: AsyncClient,
        admin_token: str,
        job_role_repo: JobRoleRepository,
        cleanup_job_roles: AsyncGenerator[None, None],
    ) -> None:
        """Test updating job role with both name and description."""
        job_role = await job_role_repo.create_job_role(
            name="Old Name", description="Old description"
        )
        payload = {"name": "New Name", "description": "New description"}
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = await client.put(
            f"/api/v1/job-roles/{str(job_role['_id'])}",
            json=payload,
            headers=headers,
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "New Name"
        assert data["description"] == "New description"

    @pytest.mark.anyio
    async def test_update_job_role_name_only(
        self,
        client: AsyncClient,
        admin_token: str,
        job_role_repo: JobRoleRepository,
        cleanup_job_roles: AsyncGenerator[None, None],
    ) -> None:
        """Test updating only the job role name."""
        job_role = await job_role_repo.create_job_role(
            name="Old Name", description="Original description"
        )
        payload = {"name": "New Name"}
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = await client.put(
            f"/api/v1/job-roles/{str(job_role['_id'])}",
            json=payload,
            headers=headers,
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "New Name"
        assert data["description"] == "Original description"

    @pytest.mark.anyio
    async def test_update_job_role_not_found(
        self, client: AsyncClient, admin_token: str, cleanup_job_roles: AsyncGenerator[None, None]
    ) -> None:
        """Test updating non-existent job role."""
        from bson import ObjectId

        invalid_id = str(ObjectId())
        payload = {"name": "New Name"}
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = await client.put(
            f"/api/v1/job-roles/{invalid_id}",
            json=payload,
            headers=headers,
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.anyio
    async def test_update_job_role_duplicate_name(
        self,
        client: AsyncClient,
        admin_token: str,
        job_role_repo: JobRoleRepository,
        cleanup_job_roles: AsyncGenerator[None, None],
    ) -> None:
        """Test updating job role to a name that already exists."""
        await job_role_repo.create_job_role(name="Role 1", description="Description 1")
        role2 = await job_role_repo.create_job_role(name="Role 2", description="Description 2")
        payload = {"name": "Role 1"}
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = await client.put(
            f"/api/v1/job-roles/{str(role2['_id'])}",
            json=payload,
            headers=headers,
        )
        assert response.status_code == status.HTTP_409_CONFLICT

    @pytest.mark.anyio
    async def test_update_job_role_missing_auth(
        self,
        client: AsyncClient,
        job_role_repo: JobRoleRepository,
        cleanup_job_roles: AsyncGenerator[None, None],
    ) -> None:
        """Test updating job role without authentication."""
        job_role = await job_role_repo.create_job_role(name="Name", description="Description")
        payload = {"name": "New Name"}
        response = await client.put(f"/api/v1/job-roles/{str(job_role['_id'])}", json=payload)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.anyio
    async def test_update_job_role_student_token(
        self,
        client: AsyncClient,
        student_token: str,
        job_role_repo: JobRoleRepository,
        cleanup_job_roles: AsyncGenerator[None, None],
    ) -> None:
        """Test updating job role with student token."""
        job_role = await job_role_repo.create_job_role(name="Name", description="Description")
        payload = {"name": "New Name"}
        headers = {"Authorization": f"Bearer {student_token}"}
        response = await client.put(
            f"/api/v1/job-roles/{str(job_role['_id'])}",
            json=payload,
            headers=headers,
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN


# ============================================================================
# DELETE ENDPOINT - Admin Only
# ============================================================================


class TestDeleteJobRole:
    """Tests for DELETE /job-roles/{id} endpoint."""

    @pytest.mark.anyio
    async def test_delete_job_role_success(
        self,
        client: AsyncClient,
        admin_token: str,
        job_role_repo: JobRoleRepository,
        cleanup_job_roles: AsyncGenerator[None, None],
    ) -> None:
        """Test successfully deleting a job role."""
        job_role = await job_role_repo.create_job_role(
            name="Role to Delete", description="This will be deleted"
        )
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = await client.delete(f"/api/v1/job-roles/{str(job_role['_id'])}", headers=headers)
        assert response.status_code == status.HTTP_200_OK
        deleted_role = await job_role_repo.find_by_id(str(job_role["_id"]))
        assert deleted_role is None

    @pytest.mark.anyio
    async def test_delete_job_role_not_found(
        self, client: AsyncClient, admin_token: str, cleanup_job_roles: AsyncGenerator[None, None]
    ) -> None:
        """Test deleting non-existent job role."""
        from bson import ObjectId

        invalid_id = str(ObjectId())
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = await client.delete(f"/api/v1/job-roles/{invalid_id}", headers=headers)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.anyio
    async def test_delete_job_role_missing_auth(
        self,
        client: AsyncClient,
        job_role_repo: JobRoleRepository,
        cleanup_job_roles: AsyncGenerator[None, None],
    ) -> None:
        """Test deleting job role without authentication."""
        job_role = await job_role_repo.create_job_role(name="Role", description="Description")
        response = await client.delete(f"/api/v1/job-roles/{str(job_role['_id'])}")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.anyio
    async def test_delete_job_role_student_token(
        self,
        client: AsyncClient,
        student_token: str,
        job_role_repo: JobRoleRepository,
        cleanup_job_roles: AsyncGenerator[None, None],
    ) -> None:
        """Test deleting job role with student token."""
        job_role = await job_role_repo.create_job_role(name="Role", description="Description")
        headers = {"Authorization": f"Bearer {student_token}"}
        response = await client.delete(f"/api/v1/job-roles/{str(job_role['_id'])}", headers=headers)
        assert response.status_code == status.HTTP_403_FORBIDDEN


# ============================================================================
# Integration Tests
# ============================================================================


class TestJobRoleIntegration:
    """Integration tests combining multiple operations."""

    @pytest.mark.anyio
    async def test_full_crud_workflow(
        self, client: AsyncClient, admin_token: str, cleanup_job_roles: AsyncGenerator[None, None]
    ) -> None:
        """Test complete CRUD workflow."""
        headers = {"Authorization": f"Bearer {admin_token}"}

        # CREATE
        create_payload = {
            "name": "Full Stack Developer",
            "description": "Develop full stack applications",
        }
        create_response = await client.post(
            "/api/v1/job-roles", json=create_payload, headers=headers
        )
        assert create_response.status_code == status.HTTP_201_CREATED
        role_id = create_response.json()["id"]

        # READ
        read_response = await client.get(f"/api/v1/job-roles/{role_id}")
        assert read_response.status_code == status.HTTP_200_OK
        assert read_response.json()["name"] == "Full Stack Developer"

        # UPDATE
        update_payload = {"description": "Updated description"}
        update_response = await client.put(
            f"/api/v1/job-roles/{role_id}",
            json=update_payload,
            headers=headers,
        )
        assert update_response.status_code == status.HTTP_200_OK

        # DELETE
        delete_response = await client.delete(f"/api/v1/job-roles/{role_id}", headers=headers)
        assert delete_response.status_code == status.HTTP_200_OK

        # Verify deleted
        final_read = await client.get(f"/api/v1/job-roles/{role_id}")
        assert final_read.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.anyio
    async def test_public_read_after_admin_operations(
        self, client: AsyncClient, admin_token: str, cleanup_job_roles: AsyncGenerator[None, None]
    ) -> None:
        """Test that public read works after admin creates."""
        headers = {"Authorization": f"Bearer {admin_token}"}
        payload = {"name": "Public Test", "description": "Test"}
        response = await client.post("/api/v1/job-roles", json=payload, headers=headers)
        role_id = response.json()["id"]

        # Public read without auth
        public_read = await client.get(f"/api/v1/job-roles/{role_id}")
        assert public_read.status_code == status.HTTP_200_OK
        assert public_read.json()["name"] == "Public Test"

    @pytest.mark.anyio
    async def test_student_cannot_create_but_can_read(
        self,
        client: AsyncClient,
        admin_token: str,
        student_token: str,
        cleanup_job_roles: AsyncGenerator[None, None],
    ) -> None:
        """Test that students can read but cannot create."""
        headers_admin = {"Authorization": f"Bearer {admin_token}"}
        headers_student = {"Authorization": f"Bearer {student_token}"}

        # Admin creates
        payload = {"name": "Test Role", "description": "Test"}
        response = await client.post("/api/v1/job-roles", json=payload, headers=headers_admin)
        assert response.status_code == status.HTTP_201_CREATED
        role_id = response.json()["id"]

        # Student reads successfully
        read_response = await client.get(f"/api/v1/job-roles/{role_id}")
        assert read_response.status_code == status.HTTP_200_OK

        # Student cannot create
        create_payload = {"name": "Illegal Role", "description": "Test"}
        create_response = await client.post(
            "/api/v1/job-roles", json=create_payload, headers=headers_student
        )
        assert create_response.status_code == status.HTTP_403_FORBIDDEN
