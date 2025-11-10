# FastAPI + MongoDB Starter Wiki

## Quick Start

### Run Tests

```bash
# All tests (asyncio only - ~20 seconds)
pytest tests/ -p no:trio -v

# Specific test
pytest tests/api/test_auth.py::test_signup_creates_user_with_default_role -v

# With output/debugging
pytest tests/ -p no:trio -v -s
```

### Development Commands

```bash
make install    # Install dependencies
make run       # Run app on localhost:8000
make test      # Run tests
make format    # Code formatting (black)
make lint      # Linting (ruff)
make type      # Type checking (mypy strict)
make sec       # Security audit (bandit)
```

### API Documentation

-   **Swagger UI:** http://localhost:8000/docs
-   **ReDoc:** http://localhost:8000/redoc

---

## Project Structure

```
app/
├── api/v1/routers/          # Feature-based endpoints
│   ├── auth.py              # Authentication (signup, login)
│   ├── course_categories.py # Course category management (CRUD)
│   ├── job_roles.py         # Job role management (CRUD)
│   ├── courses.py           # Course management
│   ├── assignments.py       # Assignment management
│   ├── submissions.py       # Student submissions
│   ├── users.py             # Admin user management
│   └── analytics.py         # Analytics & reports
├── core/
│   ├── config.py            # Environment settings
│   ├── security.py          # JWT, password hashing
│   └── dependencies.py      # RBAC dependency injection
├── domain/
│   ├── users/
│   │   ├── user.py          # User aggregate
│   │   └── value_objects.py # UserRole enum
│   ├── course_categories/
│   │   └── category.py      # CourseCategory aggregate
│   └── job_roles/
│       └── job_role.py      # JobRole aggregate
├── db/
│   ├── mongo.py             # MongoDB connection (Motor)
│   ├── repository.py        # User repository
│   ├── course_category_repository.py # Course category repository
│   └── job_role_repository.py        # Job role repository
└── main.py                  # App factory
```

---

## User Roles

-   **Admin** - Full system access
-   **Tutor** - Manage courses, grade assignments
-   **Student** - View courses, submit assignments

---

## Authentication

### Signup Endpoint

```
POST /api/v1/auth/signup   → Create student account (returns JWT)
```

**Request:**

```json
{
    "email": "user@example.com",
    "password": "securepass123",
    "name": "John Student"
}
```

**Response:** Returns JWT token and user info (role always `student`)

**Security:** All new users are created as **students** by default. Admins must explicitly promote users to tutor/admin roles.

### Login Endpoint

```
POST /api/v1/auth/login    → Authenticate (returns JWT)
```

**Request:**

```json
{
    "email": "user@example.com",
    "password": "securepass123"
}
```

**Response:** Returns JWT token and user info with their current role

### Create Tutor Account (Admin Only)

```
POST /api/v1/users/tutors   → Create tutor account (admin only)
```

**Request:**

```json
{
    "email": "tutor@example.com",
    "password": "tutorpass123",
    "name": "Jane Tutor"
}
```

**Response:** Returns tutor account details (role is `tutor`)

**Security:** Requires admin authentication. Only admins can create tutor accounts.

### Protected Endpoints Example

```python
from app.core.dependencies import require_admin, get_current_user_id, require_tutor
from fastapi import Depends

@router.delete("/{id}")
async def delete(id: str, _=Depends(require_admin)):
    pass

@router.post("")
async def create(user_id=Depends(get_current_user_id), _=Depends(require_tutor)):
    pass
```

### Available Dependencies

-   `get_current_user_id` - Extract user ID
-   `get_current_user_role` - Extract user role
-   `require_admin` - Admin only
-   `require_tutor` - Tutor or admin
-   `require_student` - All authenticated

---

## Collections

### Course Categories

-   **Endpoints**: `GET /api/v1/course-categories`, `POST /api/v1/course-categories`, etc.
-   **Read**: Public (no auth required)
-   **Create/Update/Delete**: Admin only
-   **Fields**: `name` (string, required, unique), `description` (string, required)

### Job Roles

-   **Endpoints**: `GET /api/v1/job-roles`, `POST /api/v1/job-roles`, etc.
-   **Read**: Public (no auth required) - anyone can view all job roles
-   **Create/Update/Delete**: Admin only - only admins can manage job roles
-   **Fields**: `name` (string, required, unique, 1-200 chars), `description` (string, required, 1-1000 chars)
-   **Example**:
    ```json
    {
        "name": "Software Engineer",
        "description": "Design, develop, and maintain software applications"
    }
    ```

### Vendors

-   **Endpoints**: `GET /api/v1/vendors`, `POST /api/v1/vendors`, etc.
-   **Read**: Public (no auth required) - anyone can view all vendors
-   **Create/Update/Delete**: Admin only - only admins can manage vendors
-   **Fields**: `name` (string, required, unique, 1-200 chars), `description` (string, required, 1-1000 chars), `logo` (string, optional)
-   **Example**:
    ```json
    {
        "name": "Coursera",
        "description": "Online learning platform with courses from universities",
        "logo": "https://example.com/coursera-logo.png"
    }
    ```

### Courses

-   **Endpoints**: `GET /api/v1/courses`, `POST /api/v1/courses`, `PUT /api/v1/courses/{id}`, `DELETE /api/v1/courses/{id}`
-   **Read**: Public (no auth required) - anyone can view courses with optional filters
-   **Create/Update/Delete**: Admin only
-   **Filtering & Pagination**:

    ```
    GET /api/v1/courses?level=BEGINNER&language=English&certifications=AWS&skip=0&limit=20
    ```

    -   `level` - Course level (BEGINNER, INTERMEDIATE, ADVANCED, EXPERT)
    -   `language` - Course language
    -   `category_id` - Filter by category ID
    -   `certifications` - Filter by one or more certifications
    -   `job_role_ids` - Filter by one or more job role IDs
    -   `vendor_ids` - Filter by one or more vendor IDs
    -   `skip` - Pagination offset (default: 0)
    -   `limit` - Pagination limit (default: 20, max: 100)

-   **Core Fields**:

    -   `title` (string, required, unique, 1-500 chars)
    -   `description` (string, required, 10-5000 chars)
    -   `duration` (string, required) - e.g., "8 Weeks", "12 Hours"
    -   `level` (enum: BEGINNER, INTERMEDIATE, ADVANCED, EXPERT)
    -   `language` (string, optional) - e.g., "English", "Spanish"
    -   `url` (string, optional) - Course URL/link
    -   `rating` (number, optional, 0-5)
    -   `students` (integer, optional) - Number of enrolled students
    -   `cost` (number, optional) - Course cost
    -   `certifications` (array[string], optional) - Certification names provided
    -   `image` (string, optional) - Course thumbnail URL

-   **Nested Course Details** (required):

    ```json
    {
        "overview": "Comprehensive description (10-10000 chars)",
        "objectives": ["Learn X", "Master Y"],
        "prerequisites": ["Knowledge of Z"],
        "syllabus": [
            {
                "week": "1",
                "title": "Introduction",
                "topics": ["Topic1", "Topic2"]
            }
        ]
    }
    ```

    -   `overview` (string, 10-10000 chars) - Detailed course overview
    -   `objectives` (array[string], 1-20 items) - Learning objectives
    -   `prerequisites` (array[string], 0-20 items) - Prerequisites
    -   `syllabus` (array, 1-52 weeks) - Weekly breakdown

-   **Relationships** (all optional):

    -   `category_id` - Reference to course category
    -   `vendor_id` - Reference to vendor (course provider)
    -   `job_role_ids` (array) - References to job roles (many-to-many)

-   **Example Create Request**:
    ```json
    {
        "title": "Python Basics",
        "description": "Learn Python programming from scratch",
        "duration": "8 Weeks",
        "level": "BEGINNER",
        "language": "English",
        "certifications": ["Python Developer"],
        "course_details": {
            "overview": "This comprehensive Python course covers fundamentals and best practices",
            "objectives": [
                "Understand Python syntax",
                "Build real applications"
            ],
            "prerequisites": ["Basic programming knowledge"],
            "syllabus": [
                {
                    "week": "1",
                    "title": "Python Fundamentals",
                    "topics": ["Variables", "Data Types", "Operators"]
                }
            ]
        },
        "category_id": "123abc",
        "vendor_id": "456def",
        "job_role_ids": ["789ghi"]
    }
    ```

---

## User Roles & Role Management

### Role Hierarchy

1. **Student** - Basic user role (default for all new signups)
2. **Tutor** - Can manage courses and grade assignments
3. **Admin** - Full system access, can create tutors and other admins

### Role Promotion Rules

-   **New users** always signup as **students** (role cannot be specified in signup)
-   **Tutors** are created by admins using `POST /api/v1/users/tutors` endpoint
-   **Admins** can only be created by other admins (currently no UI endpoint; must be created directly in DB or via admin API)

### Security

-   Signup endpoint (`/auth/signup`) only creates student accounts
-   Role-based access control (RBAC) enforced via `Depends(require_admin)`, `Depends(require_tutor)`, etc.
-   All password hashes use bcrypt
-   JWT tokens include user role claim for quick authorization checks

---

## Configuration

### Environment Variables (.env)

```
JWT_SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24
MONGODB_URL=mongodb+srv://...
MONGODB_DB=proddb
DEBUG=false
```

## Testing Rules

### Pytest Fixtures & Markers

```python
# ✅ CORRECT: Use @pytest.mark.anyio for async tests
@pytest.mark.anyio
async def test_login_successful(client: AsyncClient) -> None:
    response = await client.post("/api/v1/auth/login", json={...})
    assert response.status_code == 200

# ❌ WRONG: Missing @pytest.mark.anyio
async def test_something(client: AsyncClient) -> None:  # Will hang!
    pass
```

### Type Annotations for Fixtures

```python
# ✅ CORRECT: Full type hints on fixture parameters
async def test_create_category(
    self,
    client: AsyncClient,
    admin_token: str,
    course_category_repo: CourseCategoryRepository,
    cleanup_categories: AsyncGenerator[None, None],
) -> None:
    pass

# ❌ WRONG: Missing types
async def test_create_category(self, client, admin_token, cleanup_categories) -> None:
    pass
```

### Pylance Configuration

-   All test files must be **Pylance error-free** (run `make type`)
-   Add `# type: ignore` only as **last resort** when working with untyped libraries
-   Fixture packages need `__init__.py` in `tests/api/`, `tests/db/`, etc.
-   Use `conftest.py` `pytest_runtest_logreport()` hook for test output formatting

### Environment & Settings

-   Access settings via `from app.core.config import settings`
-   Never hardcode env values in tests (use fixtures or `.env`)
-   Settings auto-load from `.env` with case-insensitive env vars

---

## Key Features

-   **Feature-Based Routing** - Each domain in separate router file
-   **JWT Authentication** - HS256 signed tokens with expiration
-   **RBAC** - Role-based access control with dependency injection
-   **MongoDB** - Motor async driver for persistence
-   **Type Safety** - Full type hints, mypy strict mode
-   **Production Ready** - Scalable to 100s of endpoints

---

## Error Responses

| Status | Scenario         |
| ------ | ---------------- |
| 200    | Success          |
| 201    | Created          |
| 400    | Bad Request      |
| 401    | Unauthorized     |
| 403    | Forbidden        |
| 409    | Conflict         |
| 422    | Validation Error |

---
