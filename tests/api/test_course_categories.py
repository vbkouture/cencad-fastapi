"""Tests for course categories endpoints."""

from collections.abc import AsyncGenerator

import pytest
from fastapi import status
from httpx import AsyncClient

from app.db import CourseCategoryRepository, get_database


@pytest.fixture
async def course_category_repo(
    setup_db: AsyncGenerator[None, None]
) -> AsyncGenerator[CourseCategoryRepository, None]:
    """Get course category repository with setup."""
    db = get_database()
    repo = CourseCategoryRepository(db)
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
async def cleanup_categories(
    course_category_repo: CourseCategoryRepository,
) -> AsyncGenerator[None, None]:
    """Clean up test categories after each test."""
    yield
    await course_category_repo.collection.delete_many({})  # type: ignore


# ============================================================================
# READ ENDPOINTS - No Authentication Required
# ============================================================================


class TestGetAllCategories:
    """Tests for GET /course-categories endpoint."""

    @pytest.mark.anyio
    async def test_get_empty_list(
        self, client: AsyncClient, cleanup_categories: AsyncGenerator[None, None]
    ) -> None:
        """Test getting categories when none exist."""
        response = await client.get("/api/v1/course-categories")
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == []

    @pytest.mark.anyio
    async def test_get_all_categories_success(
        self,
        client: AsyncClient,
        course_category_repo: CourseCategoryRepository,
        cleanup_categories: AsyncGenerator[None, None],
    ) -> None:
        """Test getting all categories successfully."""
        await course_category_repo.create_category(
            name="Web Development", description="Learn web development"
        )
        await course_category_repo.create_category(
            name="Data Science", description="Learn data science"
        )
        response = await client.get("/api/v1/course-categories")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 2

    @pytest.mark.anyio
    async def test_get_all_categories_multiple_pages(
        self,
        client: AsyncClient,
        course_category_repo: CourseCategoryRepository,
        cleanup_categories: AsyncGenerator[None, None],
    ) -> None:
        """Test getting many categories."""
        for i in range(10):
            await course_category_repo.create_category(
                name=f"Category {i}", description=f"Description {i}"
            )
        response = await client.get("/api/v1/course-categories")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()) == 10


class TestGetSingleCategory:
    """Tests for GET /course-categories/{id} endpoint."""

    @pytest.mark.anyio
    async def test_get_category_by_id_success(
        self,
        client: AsyncClient,
        course_category_repo: CourseCategoryRepository,
        cleanup_categories: AsyncGenerator[None, None],
    ) -> None:
        """Test getting a category by valid ID."""
        category = await course_category_repo.create_category(
            name="Python Basics", description="Learn Python fundamentals"
        )
        response = await client.get(f"/api/v1/course-categories/{str(category['_id'])}")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "Python Basics"

    @pytest.mark.anyio
    async def test_get_category_by_id_invalid_id(
        self, client: AsyncClient, cleanup_categories: AsyncGenerator[None, None]
    ) -> None:
        """Test getting category with invalid ID."""
        from bson import ObjectId

        invalid_id = str(ObjectId())
        response = await client.get(f"/api/v1/course-categories/{invalid_id}")
        assert response.status_code == status.HTTP_404_NOT_FOUND


# ============================================================================
# CREATE ENDPOINT - Admin Only
# ============================================================================


class TestCreateCategory:
    """Tests for POST /course-categories endpoint."""

    @pytest.mark.anyio
    async def test_create_category_success(
        self, client: AsyncClient, admin_token: str, cleanup_categories: AsyncGenerator[None, None]
    ) -> None:
        """Test creating category with valid data and admin token."""
        payload = {
            "name": "Machine Learning",
            "description": "Learn machine learning algorithms",
        }
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = await client.post("/api/v1/course-categories", json=payload, headers=headers)
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == "Machine Learning"

    @pytest.mark.anyio
    async def test_create_category_missing_auth(
        self, client: AsyncClient, cleanup_categories: AsyncGenerator[None, None]
    ) -> None:
        """Test creating category without authentication."""
        payload = {"name": "Category", "description": "Description"}
        response = await client.post("/api/v1/course-categories", json=payload)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.anyio
    async def test_create_category_student_token(
        self,
        client: AsyncClient,
        student_token: str,
        cleanup_categories: AsyncGenerator[None, None],
    ) -> None:
        """Test creating category with student token (non-admin)."""
        payload = {"name": "Category", "description": "Description"}
        headers = {"Authorization": f"Bearer {student_token}"}
        response = await client.post("/api/v1/course-categories", json=payload, headers=headers)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.anyio
    async def test_create_category_duplicate_name(
        self,
        client: AsyncClient,
        admin_token: str,
        course_category_repo: CourseCategoryRepository,
        cleanup_categories: AsyncGenerator[None, None],
    ) -> None:
        """Test creating category with duplicate name."""
        await course_category_repo.create_category(
            name="Duplicate Name", description="First description"
        )
        payload = {"name": "Duplicate Name", "description": "Second description"}
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = await client.post("/api/v1/course-categories", json=payload, headers=headers)
        assert response.status_code == status.HTTP_409_CONFLICT

    @pytest.mark.anyio
    async def test_create_category_name_too_short(
        self, client: AsyncClient, admin_token: str, cleanup_categories: AsyncGenerator[None, None]
    ) -> None:
        """Test creating category with empty name."""
        payload = {"name": "", "description": "Description"}
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = await client.post("/api/v1/course-categories", json=payload, headers=headers)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.anyio
    async def test_create_category_name_too_long(
        self, client: AsyncClient, admin_token: str, cleanup_categories: AsyncGenerator[None, None]
    ) -> None:
        """Test creating category with name exceeding max length."""
        payload = {"name": "a" * 201, "description": "Description"}
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = await client.post("/api/v1/course-categories", json=payload, headers=headers)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.anyio
    async def test_create_category_description_too_short(
        self, client: AsyncClient, admin_token: str, cleanup_categories: AsyncGenerator[None, None]
    ) -> None:
        """Test creating category with empty description."""
        payload = {"name": "Category", "description": ""}
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = await client.post("/api/v1/course-categories", json=payload, headers=headers)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.anyio
    async def test_create_category_missing_name(
        self, client: AsyncClient, admin_token: str, cleanup_categories: AsyncGenerator[None, None]
    ) -> None:
        """Test creating category without name field."""
        payload = {"description": "Description"}
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = await client.post("/api/v1/course-categories", json=payload, headers=headers)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.anyio
    async def test_create_category_missing_description(
        self, client: AsyncClient, admin_token: str, cleanup_categories: AsyncGenerator[None, None]
    ) -> None:
        """Test creating category without description field."""
        payload = {"name": "Category"}
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = await client.post("/api/v1/course-categories", json=payload, headers=headers)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.anyio
    async def test_create_category_max_length_name(
        self, client: AsyncClient, admin_token: str, cleanup_categories: AsyncGenerator[None, None]
    ) -> None:
        """Test creating category with maximum valid name length."""
        payload = {"name": "a" * 200, "description": "Description"}
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = await client.post("/api/v1/course-categories", json=payload, headers=headers)
        assert response.status_code == status.HTTP_201_CREATED

    @pytest.mark.anyio
    async def test_create_category_max_length_description(
        self, client: AsyncClient, admin_token: str, cleanup_categories: AsyncGenerator[None, None]
    ) -> None:
        """Test creating category with maximum valid description length."""
        payload = {"name": "Category", "description": "a" * 1000}
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = await client.post("/api/v1/course-categories", json=payload, headers=headers)
        assert response.status_code == status.HTTP_201_CREATED

    @pytest.mark.anyio
    async def test_create_category_unicode_characters(
        self, client: AsyncClient, admin_token: str, cleanup_categories: AsyncGenerator[None, None]
    ) -> None:
        """Test creating category with unicode characters."""
        payload = {
            "name": "数据科学 (Data Science)",
            "description": "Learn 机器学习 and AI 🚀",
        }
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = await client.post("/api/v1/course-categories", json=payload, headers=headers)
        assert response.status_code == status.HTTP_201_CREATED


# ============================================================================
# UPDATE ENDPOINT - Admin Only
# ============================================================================


class TestUpdateCategory:
    """Tests for PUT /course-categories/{id} endpoint."""

    @pytest.mark.anyio
    async def test_update_category_both_fields(
        self,
        client: AsyncClient,
        admin_token: str,
        course_category_repo: CourseCategoryRepository,
        cleanup_categories: AsyncGenerator[None, None],
    ) -> None:
        """Test updating category with both name and description."""
        category = await course_category_repo.create_category(
            name="Old Name", description="Old description"
        )
        payload = {"name": "New Name", "description": "New description"}
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = await client.put(
            f"/api/v1/course-categories/{str(category['_id'])}",
            json=payload,
            headers=headers,
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "New Name"
        assert data["description"] == "New description"

    @pytest.mark.anyio
    async def test_update_category_name_only(
        self,
        client: AsyncClient,
        admin_token: str,
        course_category_repo: CourseCategoryRepository,
        cleanup_categories: AsyncGenerator[None, None],
    ) -> None:
        """Test updating only the category name."""
        category = await course_category_repo.create_category(
            name="Old Name", description="Original description"
        )
        payload = {"name": "New Name"}
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = await client.put(
            f"/api/v1/course-categories/{str(category['_id'])}",
            json=payload,
            headers=headers,
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "New Name"
        assert data["description"] == "Original description"

    @pytest.mark.anyio
    async def test_update_category_not_found(
        self, client: AsyncClient, admin_token: str, cleanup_categories: AsyncGenerator[None, None]
    ) -> None:
        """Test updating non-existent category."""
        from bson import ObjectId

        invalid_id = str(ObjectId())
        payload = {"name": "New Name"}
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = await client.put(
            f"/api/v1/course-categories/{invalid_id}",
            json=payload,
            headers=headers,
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.anyio
    async def test_update_category_duplicate_name(
        self,
        client: AsyncClient,
        admin_token: str,
        course_category_repo: CourseCategoryRepository,
        cleanup_categories: AsyncGenerator[None, None],
    ) -> None:
        """Test updating category to a name that already exists."""
        await course_category_repo.create_category(name="Category 1", description="Description 1")
        cat2 = await course_category_repo.create_category(
            name="Category 2", description="Description 2"
        )
        payload = {"name": "Category 1"}
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = await client.put(
            f"/api/v1/course-categories/{str(cat2['_id'])}",
            json=payload,
            headers=headers,
        )
        assert response.status_code == status.HTTP_409_CONFLICT

    @pytest.mark.anyio
    async def test_update_category_missing_auth(
        self,
        client: AsyncClient,
        course_category_repo: CourseCategoryRepository,
        cleanup_categories: AsyncGenerator[None, None],
    ) -> None:
        """Test updating category without authentication."""
        category = await course_category_repo.create_category(
            name="Name", description="Description"
        )
        payload = {"name": "New Name"}
        response = await client.put(
            f"/api/v1/course-categories/{str(category['_id'])}", json=payload
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.anyio
    async def test_update_category_student_token(
        self,
        client: AsyncClient,
        student_token: str,
        course_category_repo: CourseCategoryRepository,
        cleanup_categories: AsyncGenerator[None, None],
    ) -> None:
        """Test updating category with student token."""
        category = await course_category_repo.create_category(
            name="Name", description="Description"
        )
        payload = {"name": "New Name"}
        headers = {"Authorization": f"Bearer {student_token}"}
        response = await client.put(
            f"/api/v1/course-categories/{str(category['_id'])}",
            json=payload,
            headers=headers,
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN


# ============================================================================
# DELETE ENDPOINT - Admin Only
# ============================================================================


class TestDeleteCategory:
    """Tests for DELETE /course-categories/{id} endpoint."""

    @pytest.mark.anyio
    async def test_delete_category_success(
        self,
        client: AsyncClient,
        admin_token: str,
        course_category_repo: CourseCategoryRepository,
        cleanup_categories: AsyncGenerator[None, None],
    ) -> None:
        """Test successfully deleting a category."""
        category = await course_category_repo.create_category(
            name="Category to Delete", description="This will be deleted"
        )
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = await client.delete(
            f"/api/v1/course-categories/{str(category['_id'])}", headers=headers
        )
        assert response.status_code == status.HTTP_200_OK
        deleted_category = await course_category_repo.find_by_id(str(category["_id"]))
        assert deleted_category is None

    @pytest.mark.anyio
    async def test_delete_category_not_found(
        self, client: AsyncClient, admin_token: str, cleanup_categories: AsyncGenerator[None, None]
    ) -> None:
        """Test deleting non-existent category."""
        from bson import ObjectId

        invalid_id = str(ObjectId())
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = await client.delete(f"/api/v1/course-categories/{invalid_id}", headers=headers)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.anyio
    async def test_delete_category_missing_auth(
        self,
        client: AsyncClient,
        course_category_repo: CourseCategoryRepository,
        cleanup_categories: AsyncGenerator[None, None],
    ) -> None:
        """Test deleting category without authentication."""
        category = await course_category_repo.create_category(
            name="Category", description="Description"
        )
        response = await client.delete(f"/api/v1/course-categories/{str(category['_id'])}")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.anyio
    async def test_delete_category_student_token(
        self,
        client: AsyncClient,
        student_token: str,
        course_category_repo: CourseCategoryRepository,
        cleanup_categories: AsyncGenerator[None, None],
    ) -> None:
        """Test deleting category with student token."""
        category = await course_category_repo.create_category(
            name="Category", description="Description"
        )
        headers = {"Authorization": f"Bearer {student_token}"}
        response = await client.delete(
            f"/api/v1/course-categories/{str(category['_id'])}", headers=headers
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN


# ============================================================================
# Integration Tests
# ============================================================================


class TestCourseCategoryIntegration:
    """Integration tests combining multiple operations."""

    @pytest.mark.anyio
    async def test_full_crud_workflow(
        self, client: AsyncClient, admin_token: str, cleanup_categories: AsyncGenerator[None, None]
    ) -> None:
        """Test complete CRUD workflow."""
        headers = {"Authorization": f"Bearer {admin_token}"}

        # CREATE
        create_payload = {
            "name": "Web Development",
            "description": "Learn web development",
        }
        create_response = await client.post(
            "/api/v1/course-categories", json=create_payload, headers=headers
        )
        assert create_response.status_code == status.HTTP_201_CREATED
        category_id = create_response.json()["id"]

        # READ
        read_response = await client.get(f"/api/v1/course-categories/{category_id}")
        assert read_response.status_code == status.HTTP_200_OK
        assert read_response.json()["name"] == "Web Development"

        # UPDATE
        update_payload = {"description": "Updated description"}
        update_response = await client.put(
            f"/api/v1/course-categories/{category_id}",
            json=update_payload,
            headers=headers,
        )
        assert update_response.status_code == status.HTTP_200_OK

        # DELETE
        delete_response = await client.delete(
            f"/api/v1/course-categories/{category_id}", headers=headers
        )
        assert delete_response.status_code == status.HTTP_200_OK

        # Verify deleted
        final_read = await client.get(f"/api/v1/course-categories/{category_id}")
        assert final_read.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.anyio
    async def test_public_read_after_admin_operations(
        self, client: AsyncClient, admin_token: str, cleanup_categories: AsyncGenerator[None, None]
    ) -> None:
        """Test that public read works after admin creates."""
        headers = {"Authorization": f"Bearer {admin_token}"}
        payload = {"name": "Public Test", "description": "Test"}
        response = await client.post("/api/v1/course-categories", json=payload, headers=headers)
        category_id = response.json()["id"]

        # Public read without auth
        public_read = await client.get(f"/api/v1/course-categories/{category_id}")
        assert public_read.status_code == status.HTTP_200_OK
        assert public_read.json()["name"] == "Public Test"
