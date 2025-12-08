"""Tests for courses endpoints."""

from collections.abc import AsyncGenerator
from typing import Any

import pytest
from fastapi import status
from httpx import AsyncClient

from app.db import get_database
from app.db.course_repository import CourseRepository


@pytest.fixture
async def course_repo(
    setup_db: AsyncGenerator[None, None]
) -> AsyncGenerator[CourseRepository, None]:
    """Get course repository with setup."""
    db = get_database()
    repo = CourseRepository(db)
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
async def cleanup_courses(course_repo: CourseRepository) -> AsyncGenerator[None, None]:
    """Clean up test courses after each test."""
    yield
    await course_repo.collection.delete_many({})  # type: ignore


def _create_valid_course_payload() -> dict[str, Any]:
    """Create a valid course creation payload."""
    return {
        "title": "Python Basics",
        "description": "Learn Python programming from scratch",
        "duration": "8 Weeks",
        "level": "BEGINNER",
        "course_details": {
            "overview": "This course teaches Python basics including data types, control flow, and functions.",
            "objectives": [
                "Understand Python basics",
                "Write simple programs",
                "Use functions effectively",
            ],
            "prerequisites": ["Basic computer knowledge"],
            "syllabus": [
                {
                    "week": "Week 1",
                    "title": "Introduction to Python",
                    "topics": ["Installation", "Basic syntax", "Variables"],
                },
                {
                    "week": "Week 2",
                    "title": "Data Types",
                    "topics": ["Strings", "Numbers", "Lists"],
                },
            ],
        },
        "language": "English",
        "certifications": [],
        "resources": [{"title": "Book", "url": "http://example.com"}],
        "notice": "Important notice",
        "tags": ["python", "basics"],
        "status": "DRAFT",
    }


# ============================================================================
# READ ENDPOINTS - No Authentication Required
# ============================================================================


class TestGetAllCourses:
    """Tests for GET /courses endpoint."""

    @pytest.mark.anyio
    async def test_get_empty_list(
        self, client: AsyncClient, cleanup_courses: AsyncGenerator[None, None]
    ) -> None:
        """Test getting courses when none exist."""
        response = await client.get("/api/v1/courses")
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["data"] == []

    @pytest.mark.anyio
    async def test_get_all_courses_success(
        self,
        client: AsyncClient,
        course_repo: CourseRepository,
        cleanup_courses: AsyncGenerator[None, None],
    ) -> None:
        """Test getting all courses successfully."""
        await course_repo.create_course(
            title="Python 101",
            description="Learn Python",
            duration="8 Weeks",
            level="BEGINNER",
            course_details={
                "overview": "Introduction to Python programming basics",
                "objectives": ["Learn"],
                "prerequisites": [],
                "syllabus": [{"week": "1", "title": "Intro", "topics": ["Python"]}],
            },
        )
        response = await client.get("/api/v1/courses")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()["data"]) == 1

    @pytest.mark.anyio
    async def test_get_all_courses_multiple(
        self,
        client: AsyncClient,
        course_repo: CourseRepository,
        cleanup_courses: AsyncGenerator[None, None],
    ) -> None:
        """Test getting multiple courses."""
        for i in range(5):
            await course_repo.create_course(
                title=f"Course {i}",
                description="Description",
                duration="4 Weeks",
                level="BEGINNER",
                course_details={
                    "overview": "Comprehensive course overview for learning",
                    "objectives": ["Learn"],
                    "prerequisites": [],
                    "syllabus": [{"week": "1", "title": "Week 1", "topics": ["Topic1"]}],
                },
            )
        response = await client.get("/api/v1/courses")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()["data"]) == 5


class TestGetSingleCourse:
    """Tests for GET /courses/{id} endpoint."""

    @pytest.mark.anyio
    async def test_get_course_by_id_success(
        self,
        client: AsyncClient,
        course_repo: CourseRepository,
        cleanup_courses: AsyncGenerator[None, None],
    ) -> None:
        """Test getting a course by valid ID."""
        course = await course_repo.create_course(
            title="Advanced Python",
            description="Master Python",
            duration="12 Weeks",
            level="ADVANCED",
            course_details={
                "overview": "Advanced Python concepts",
                "objectives": ["Master", "Expert"],
                "prerequisites": ["Basics"],
                "syllabus": [{"week": "1", "title": "Advanced", "topics": ["Decorators"]}],
            },
        )
        response = await client.get(f"/api/v1/courses/{str(course['_id'])}")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["title"] == "Advanced Python"

    @pytest.mark.anyio
    async def test_get_course_by_id_invalid_id(
        self, client: AsyncClient, cleanup_courses: AsyncGenerator[None, None]
    ) -> None:
        """Test getting course with invalid ID."""
        from bson import ObjectId

        invalid_id = str(ObjectId())
        response = await client.get(f"/api/v1/courses/{invalid_id}")
        assert response.status_code == status.HTTP_404_NOT_FOUND


# ============================================================================
# CREATE ENDPOINT - Admin Only
# ============================================================================


class TestCreateCourse:
    """Tests for POST /courses endpoint."""

    @pytest.mark.anyio
    async def test_create_course_success(
        self, client: AsyncClient, admin_token: str, cleanup_courses: AsyncGenerator[None, None]
    ) -> None:
        """Test creating course with valid data and admin token."""
        payload = _create_valid_course_payload()
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = await client.post("/api/v1/courses", json=payload, headers=headers)
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["title"] == "Python Basics"
        assert data["level"] == "BEGINNER"
        assert data["status"] == "DRAFT"
        assert len(data["resources"]) == 1
        assert data["resources"][0]["title"] == "Book"
        assert data["notice"] == "Important notice"
        assert "python" in data["tags"]

    @pytest.mark.anyio
    async def test_create_course_missing_auth(
        self, client: AsyncClient, cleanup_courses: AsyncGenerator[None, None]
    ) -> None:
        """Test creating course without authentication."""
        payload = _create_valid_course_payload()
        response = await client.post("/api/v1/courses", json=payload)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.anyio
    async def test_create_course_student_token(
        self, client: AsyncClient, student_token: str, cleanup_courses: AsyncGenerator[None, None]
    ) -> None:
        """Test creating course with student token (non-admin)."""
        payload = _create_valid_course_payload()
        headers = {"Authorization": f"Bearer {student_token}"}
        response = await client.post("/api/v1/courses", json=payload, headers=headers)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.anyio
    async def test_create_course_duplicate_title(
        self,
        client: AsyncClient,
        admin_token: str,
        course_repo: CourseRepository,
        cleanup_courses: AsyncGenerator[None, None],
    ) -> None:
        """Test creating course with duplicate title."""
        await course_repo.create_course(
            title="Duplicate",
            description="First",
            duration="4 Weeks",
            level="BEGINNER",
            course_details={
                "overview": "Test",
                "objectives": ["Learn"],
                "prerequisites": [],
                "syllabus": [{"week": "1", "title": "W1", "topics": ["T1"]}],
            },
        )
        payload = _create_valid_course_payload()
        payload["title"] = "Duplicate"
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = await client.post("/api/v1/courses", json=payload, headers=headers)
        assert response.status_code == status.HTTP_409_CONFLICT

    @pytest.mark.anyio
    async def test_create_course_invalid_level(
        self, client: AsyncClient, admin_token: str, cleanup_courses: AsyncGenerator[None, None]
    ) -> None:
        """Test creating course with invalid level."""
        payload = _create_valid_course_payload()
        payload["level"] = "INVALID"
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = await client.post("/api/v1/courses", json=payload, headers=headers)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.anyio
    async def test_create_course_missing_title(
        self, client: AsyncClient, admin_token: str, cleanup_courses: AsyncGenerator[None, None]
    ) -> None:
        """Test creating course without title."""
        payload = _create_valid_course_payload()
        del payload["title"]
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = await client.post("/api/v1/courses", json=payload, headers=headers)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.anyio
    async def test_create_course_short_description(
        self, client: AsyncClient, admin_token: str, cleanup_courses: AsyncGenerator[None, None]
    ) -> None:
        """Test creating course with description too short."""
        payload = _create_valid_course_payload()
        payload["description"] = "Too short"
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = await client.post("/api/v1/courses", json=payload, headers=headers)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.anyio
    async def test_create_course_with_vendor_and_category(
        self, client: AsyncClient, admin_token: str, cleanup_courses: AsyncGenerator[None, None]
    ) -> None:
        """Test creating course with vendor and category IDs."""
        from bson import ObjectId

        payload = _create_valid_course_payload()
        payload["vendor_id"] = str(ObjectId())
        payload["category_id"] = str(ObjectId())
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = await client.post("/api/v1/courses", json=payload, headers=headers)
        assert response.status_code == status.HTTP_201_CREATED

    @pytest.mark.anyio
    async def test_create_course_with_certifications(
        self, client: AsyncClient, admin_token: str, cleanup_courses: AsyncGenerator[None, None]
    ) -> None:
        """Test creating course with multiple certifications."""
        payload = _create_valid_course_payload()
        payload["certifications"] = ["AZ-900", "Azure Fundamentals"]
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = await client.post("/api/v1/courses", json=payload, headers=headers)
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert len(data["certifications"]) == 2

    @pytest.mark.anyio
    async def test_create_course_all_levels(
        self, client: AsyncClient, admin_token: str, cleanup_courses: AsyncGenerator[None, None]
    ) -> None:
        """Test creating courses with all valid levels."""
        headers = {"Authorization": f"Bearer {admin_token}"}
        levels = ["BEGINNER", "INTERMEDIATE", "ADVANCED", "EXPERT"]

        for level in levels:
            payload = _create_valid_course_payload()
            payload["title"] = f"Course {level}"
            payload["level"] = level
            response = await client.post("/api/v1/courses", json=payload, headers=headers)
            assert response.status_code == status.HTTP_201_CREATED
            data = response.json()
            assert data["level"] == level


# ============================================================================
# UPDATE ENDPOINT - Admin Only
# ============================================================================


class TestUpdateCourse:
    """Tests for PUT /courses/{id} endpoint."""

    @pytest.mark.anyio
    async def test_update_course_title_only(
        self,
        client: AsyncClient,
        admin_token: str,
        course_repo: CourseRepository,
        cleanup_courses: AsyncGenerator[None, None],
    ) -> None:
        """Test updating only course title."""
        course = await course_repo.create_course(
            title="Old Title",
            description="A comprehensive course description",
            duration="8 Weeks",
            level="BEGINNER",
            course_details={
                "overview": "Test overview",
                "objectives": ["Learn"],
                "prerequisites": [],
                "syllabus": [{"week": "1", "title": "W1", "topics": ["T1"]}],
            },
        )
        payload = {"title": "New Title"}
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = await client.put(
            f"/api/v1/courses/{str(course['_id'])}",
            json=payload,
            headers=headers,
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["title"] == "New Title"

    @pytest.mark.anyio
    async def test_update_course_not_found(
        self, client: AsyncClient, admin_token: str, cleanup_courses: AsyncGenerator[None, None]
    ) -> None:
        """Test updating non-existent course."""
        from bson import ObjectId

        invalid_id = str(ObjectId())
        payload = {"title": "New Title"}
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = await client.put(
            f"/api/v1/courses/{invalid_id}",
            json=payload,
            headers=headers,
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.anyio
    async def test_update_course_missing_auth(
        self,
        client: AsyncClient,
        course_repo: CourseRepository,
        cleanup_courses: AsyncGenerator[None, None],
    ) -> None:
        """Test updating course without authentication."""
        course = await course_repo.create_course(
            title="Test",
            description="A test course description",
            duration="4 Weeks",
            level="BEGINNER",
            course_details={
                "overview": "Test",
                "objectives": ["Learn"],
                "prerequisites": [],
                "syllabus": [{"week": "1", "title": "W1", "topics": ["T1"]}],
            },
        )
        payload = {"title": "New Title"}
        response = await client.put(f"/api/v1/courses/{str(course['_id'])}", json=payload)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.anyio
    async def test_update_course_student_token(
        self,
        client: AsyncClient,
        student_token: str,
        course_repo: CourseRepository,
        cleanup_courses: AsyncGenerator[None, None],
    ) -> None:
        """Test updating course with student token."""
        course = await course_repo.create_course(
            title="Test",
            description="A test course description",
            duration="4 Weeks",
            level="BEGINNER",
            course_details={
                "overview": "Test",
                "objectives": ["Learn"],
                "prerequisites": [],
                "syllabus": [{"week": "1", "title": "W1", "topics": ["T1"]}],
            },
        )
        payload = {"title": "New Title"}
        headers = {"Authorization": f"Bearer {student_token}"}
        response = await client.put(
            f"/api/v1/courses/{str(course['_id'])}",
            json=payload,
            headers=headers,
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN


# ============================================================================
# DELETE ENDPOINT - Admin Only
# ============================================================================


class TestDeleteCourse:
    """Tests for DELETE /courses/{id} endpoint."""

    @pytest.mark.anyio
    async def test_delete_course_success(
        self,
        client: AsyncClient,
        admin_token: str,
        course_repo: CourseRepository,
        cleanup_courses: AsyncGenerator[None, None],
    ) -> None:
        """Test successfully deleting a course."""
        course = await course_repo.create_course(
            title="To Delete",
            description="This course will be deleted",
            duration="2 Weeks",
            level="BEGINNER",
            course_details={
                "overview": "Test",
                "objectives": ["Learn"],
                "prerequisites": [],
                "syllabus": [{"week": "1", "title": "W1", "topics": ["T1"]}],
            },
        )
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = await client.delete(f"/api/v1/courses/{str(course['_id'])}", headers=headers)
        assert response.status_code == status.HTTP_200_OK
        deleted = await course_repo.find_by_id(str(course["_id"]))
        assert deleted is None

    @pytest.mark.anyio
    async def test_delete_course_not_found(
        self, client: AsyncClient, admin_token: str, cleanup_courses: AsyncGenerator[None, None]
    ) -> None:
        """Test deleting non-existent course."""
        from bson import ObjectId

        invalid_id = str(ObjectId())
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = await client.delete(f"/api/v1/courses/{invalid_id}", headers=headers)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.anyio
    async def test_delete_course_missing_auth(
        self,
        client: AsyncClient,
        course_repo: CourseRepository,
        cleanup_courses: AsyncGenerator[None, None],
    ) -> None:
        """Test deleting course without authentication."""
        course = await course_repo.create_course(
            title="Test",
            description="A test course description",
            duration="4 Weeks",
            level="BEGINNER",
            course_details={
                "overview": "Test",
                "objectives": ["Learn"],
                "prerequisites": [],
                "syllabus": [{"week": "1", "title": "W1", "topics": ["T1"]}],
            },
        )
        response = await client.delete(f"/api/v1/courses/{str(course['_id'])}")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.anyio
    async def test_delete_course_student_token(
        self,
        client: AsyncClient,
        student_token: str,
        course_repo: CourseRepository,
        cleanup_courses: AsyncGenerator[None, None],
    ) -> None:
        """Test deleting course with student token."""
        course = await course_repo.create_course(
            title="Test",
            description="A test course description",
            duration="4 Weeks",
            level="BEGINNER",
            course_details={
                "overview": "Test",
                "objectives": ["Learn"],
                "prerequisites": [],
                "syllabus": [{"week": "1", "title": "W1", "topics": ["T1"]}],
            },
        )
        headers = {"Authorization": f"Bearer {student_token}"}
        response = await client.delete(f"/api/v1/courses/{str(course['_id'])}", headers=headers)
        assert response.status_code == status.HTTP_403_FORBIDDEN


# ============================================================================
# Integration Tests
# ============================================================================


class TestCourseIntegration:
    """Integration tests combining multiple operations."""

    @pytest.mark.anyio
    async def test_full_crud_workflow(
        self, client: AsyncClient, admin_token: str, cleanup_courses: AsyncGenerator[None, None]
    ) -> None:
        """Test complete CRUD workflow."""
        headers = {"Authorization": f"Bearer {admin_token}"}

        # CREATE
        create_payload = _create_valid_course_payload()
        create_response = await client.post("/api/v1/courses", json=create_payload, headers=headers)
        assert create_response.status_code == status.HTTP_201_CREATED
        course_id = create_response.json()["id"]

        # READ
        read_response = await client.get(f"/api/v1/courses/{course_id}")
        assert read_response.status_code == status.HTTP_200_OK
        assert read_response.json()["title"] == "Python Basics"

        # UPDATE
        update_payload = {"description": "Updated description for Python course"}
        update_response = await client.put(
            f"/api/v1/courses/{course_id}",
            json=update_payload,
            headers=headers,
        )
        assert update_response.status_code == status.HTTP_200_OK

        # DELETE
        delete_response = await client.delete(f"/api/v1/courses/{course_id}", headers=headers)
        assert delete_response.status_code == status.HTTP_200_OK

        # Verify deleted
        final_read = await client.get(f"/api/v1/courses/{course_id}")
        assert final_read.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.anyio
    async def test_public_read_after_admin_creates(
        self, client: AsyncClient, admin_token: str, cleanup_courses: AsyncGenerator[None, None]
    ) -> None:
        """Test that public can read after admin creates."""
        headers = {"Authorization": f"Bearer {admin_token}"}
        payload = _create_valid_course_payload()
        response = await client.post("/api/v1/courses", json=payload, headers=headers)
        assert response.status_code == status.HTTP_201_CREATED
        course_id = response.json()["id"]

        # Public read without auth
        public_read = await client.get(f"/api/v1/courses/{course_id}")
        assert public_read.status_code == status.HTTP_200_OK
        assert public_read.json()["title"] == "Python Basics"

    @pytest.mark.anyio
    async def test_student_cannot_create_but_can_read(
        self,
        client: AsyncClient,
        admin_token: str,
        student_token: str,
        cleanup_courses: AsyncGenerator[None, None],
    ) -> None:
        """Test that students can read but cannot create."""
        headers_admin = {"Authorization": f"Bearer {admin_token}"}
        headers_student = {"Authorization": f"Bearer {student_token}"}

        # Admin creates
        payload = _create_valid_course_payload()
        response = await client.post("/api/v1/courses", json=payload, headers=headers_admin)
        assert response.status_code == status.HTTP_201_CREATED
        course_id = response.json()["id"]

        # Student reads successfully
        read_response = await client.get(f"/api/v1/courses/{course_id}")
        assert read_response.status_code == status.HTTP_200_OK

        # Student cannot create
        create_payload = _create_valid_course_payload()
        create_response = await client.post(
            "/api/v1/courses", json=create_payload, headers=headers_student
        )
        assert create_response.status_code == status.HTTP_403_FORBIDDEN


class TestCourseFiltering:
    """Tests for GET /courses with filtering and pagination."""

    @pytest.mark.anyio
    async def test_filter_by_level(
        self,
        client: AsyncClient,
        course_repo: CourseRepository,
        cleanup_courses: AsyncGenerator[None, None],
    ) -> None:
        """Test filtering courses by level."""
        # Create courses with different levels
        for level in ["BEGINNER", "INTERMEDIATE", "ADVANCED"]:
            await course_repo.create_course(
                title=f"Course {level}",
                description="Description",
                duration="4 Weeks",
                level=level,
                course_details={
                    "overview": "This is a comprehensive course overview with sufficient length",
                    "objectives": ["Learn"],
                    "prerequisites": [],
                    "syllabus": [{"week": "1", "title": "Week 1", "topics": ["Topic1"]}],
                },
            )

        # Filter by BEGINNER level
        response = await client.get("/api/v1/courses?level=BEGINNER")
        assert response.status_code == status.HTTP_200_OK
        courses = response.json()["data"]
        assert len(courses) == 1
        assert courses[0]["level"] == "BEGINNER"

    @pytest.mark.anyio
    async def test_filter_by_language(
        self,
        client: AsyncClient,
        course_repo: CourseRepository,
        cleanup_courses: AsyncGenerator[None, None],
    ) -> None:
        """Test filtering courses by language."""
        # Create courses with different languages
        for lang in ["English", "Spanish"]:
            await course_repo.create_course(
                title=f"Course {lang}",
                description="Description",
                duration="4 Weeks",
                level="BEGINNER",
                language=lang,
                course_details={
                    "overview": "This is a comprehensive course overview with sufficient length",
                    "objectives": ["Learn"],
                    "prerequisites": [],
                    "syllabus": [{"week": "1", "title": "Week 1", "topics": ["Topic1"]}],
                },
            )

        # Filter by English
        response = await client.get("/api/v1/courses?language=English")
        assert response.status_code == status.HTTP_200_OK
        courses = response.json()["data"]
        assert len(courses) == 1
        assert courses[0]["language"] == "English"

    @pytest.mark.anyio
    async def test_filter_by_certifications(
        self,
        client: AsyncClient,
        course_repo: CourseRepository,
        cleanup_courses: AsyncGenerator[None, None],
    ) -> None:
        """Test filtering courses by certifications."""
        # Create courses with different certifications
        certs_data = [
            ["AWS", "Python"],
            ["Azure", "Java"],
            ["AWS"],
        ]

        for i, certs in enumerate(certs_data):
            await course_repo.create_course(
                title=f"Course {i}",
                description="Description",
                duration="4 Weeks",
                level="BEGINNER",
                certifications=certs,
                course_details={
                    "overview": "This is a comprehensive course overview with sufficient length",
                    "objectives": ["Learn"],
                    "prerequisites": [],
                    "syllabus": [{"week": "1", "title": "Week 1", "topics": ["Topic1"]}],
                },
            )

        # Filter by AWS certification
        response = await client.get("/api/v1/courses?certifications=AWS")
        assert response.status_code == status.HTTP_200_OK
        courses = response.json()["data"]
        assert len(courses) == 2  # Two courses have AWS

    @pytest.mark.anyio
    async def test_pagination(
        self,
        client: AsyncClient,
        course_repo: CourseRepository,
        cleanup_courses: AsyncGenerator[None, None],
    ) -> None:
        """Test pagination with skip and limit."""
        # Create 10 courses
        for i in range(10):
            await course_repo.create_course(
                title=f"Course {i:02d}",
                description="Description",
                duration="4 Weeks",
                level="BEGINNER",
                course_details={
                    "overview": "This is a comprehensive course overview with sufficient length",
                    "objectives": ["Learn"],
                    "prerequisites": [],
                    "syllabus": [{"week": "1", "title": "Week 1", "topics": ["Topic1"]}],
                },
            )

        # Get first 5
        response1 = await client.get("/api/v1/courses?limit=5")
        assert response1.status_code == status.HTTP_200_OK
        assert len(response1.json()["data"]) == 5

        # Get next 5 with skip
        response2 = await client.get("/api/v1/courses?skip=5&limit=5")
        assert response2.status_code == status.HTTP_200_OK
        assert len(response2.json()["data"]) == 5

        # Verify different courses
        courses1 = response1.json()["data"]
        courses2 = response2.json()["data"]
        assert courses1[0]["id"] != courses2[0]["id"]

    @pytest.mark.anyio
    async def test_invalid_level_filter(self, client: AsyncClient) -> None:
        """Test filtering with invalid level."""
        response = await client.get("/api/v1/courses?level=INVALID")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.anyio
    async def test_multiple_filters_combined(
        self,
        client: AsyncClient,
        course_repo: CourseRepository,
        cleanup_courses: AsyncGenerator[None, None],
    ) -> None:
        """Test combining multiple filters."""
        # Create test course
        await course_repo.create_course(
            title="Advanced AWS Course",
            description="Description",
            duration="8 Weeks",
            level="ADVANCED",
            language="English",
            certifications=["AWS"],
            course_details={
                "overview": "This is a comprehensive course overview with sufficient length",
                "objectives": ["Learn"],
                "prerequisites": [],
                "syllabus": [{"week": "1", "title": "Week 1", "topics": ["Topic1"]}],
            },
        )

        # Create non-matching course
        await course_repo.create_course(
            title="Beginner Python Course",
            description="Description",
            duration="4 Weeks",
            level="BEGINNER",
            language="English",
            course_details={
                "overview": "This is a comprehensive course overview with sufficient length",
                "objectives": ["Learn"],
                "prerequisites": [],
                "syllabus": [{"week": "1", "title": "Week 1", "topics": ["Topic1"]}],
            },
        )

        # Filter by level AND language
        response = await client.get("/api/v1/courses?level=ADVANCED&language=English")
        assert response.status_code == status.HTTP_200_OK
        courses = response.json()["data"]
        assert len(courses) == 1
        assert courses[0]["title"] == "Advanced AWS Course"
