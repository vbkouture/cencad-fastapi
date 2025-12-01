# FastAPI + MongoDB Starter Wiki

## Quick Start

### Run App

**Windows (PowerShell)**
```powershell
# Install dependencies
make install

# Run app (localhost:8000)
make run
# OR manually
uvicorn app.main:app --reload
```

**Linux/Mac**
```bash
make install
make run
```

### Run Tests

You can run tests using `pytest` directly or via `make` commands.

**1. Run All Tests**  
```bash
# Run all tests (asyncio mode)
pytest tests/ -p no:trio -v

# OR using make
make test
```

**2. Run Specific Test File**
```bash
# Run only authentication tests
pytest tests/api/test_auth.py -p no:trio -v
```

**3. Run Specific Test Function**
```bash
# Run only the signup test
pytest tests/api/test_auth.py::test_signup_creates_user_with_default_role -p no:trio -v
```

**4. Debugging (Show Output)**
```bash
# Use -s to see print() statements and logs
pytest tests/ -p no:trio -v -s
```

### API Documentation

-   **Swagger UI:** http://localhost:8000/docs
-   **ReDoc:** http://localhost:8000/redoc

### API Schema Export

You can export the OpenAPI schema to a JSON file for generating frontend clients.

**1. Export Full Schema**
```powershell
python scripts/export_openapi.py
# Generates: openapi.json
```

**2. Export Specific Domain (Modular)**
To avoid large schema files, you can export only the endpoints for a specific feature.
```powershell
# Export only Authentication endpoints
python scripts/export_openapi.py --domain auth
# Generates: openapi_auth.json

# Export only Courses endpoints
python scripts/export_openapi.py --domain courses
# Generates: openapi_courses.json
```
**Available Domains**: `auth`, `courses`, `assignments`, `submissions`, `users`, `analytics`, `contact-forms`, `course-categories`, `job-roles`, `vendors`, `ping`.

---

## Project Structure

```
app/
├── api/v1/routers/          # Feature-based endpoints
│   ├── analytics.py         # Analytics & reports
│   ├── assignments.py       # Assignment management
│   ├── auth.py              # Authentication (signup, login)
│   ├── contact_forms.py     # Contact form submissions
│   ├── course_categories.py # Course category management
│   ├── courses.py           # Course management
│   ├── job_roles.py         # Job role management
│   ├── ping.py              # Health check
│   ├── protected.py         # Example protected routes
│   ├── submissions.py       # Student submissions
│   ├── users.py             # User management
│   └── vendors.py           # Vendor management
├── core/
│   ├── config.py            # Environment settings
│   ├── security.py          # JWT, password hashing
│   └── dependencies.py      # RBAC dependency injection
├── domain/                  # Domain models (Aggregates, Value Objects)
├── db/                      # Database connection and repositories
└── main.py                  # App factory
```

---

## Architecture & Data Flow

This project follows a layered architecture to separate concerns. Here is how a typical request flows through the system:

### 1. Router (`app/api/v1/routers/`)
**The Entry Point**.
-   Receives the HTTP request.
-   Uses **Schemas (DTOs)** to validate the request body/params.
-   Calls the **Repository** or **Service** to perform the action.
-   Returns a response using a **Schema (DTO)**.

### 2. Schema / DTO (`app/api/v1/schemas/`)
**The Contract**.
-   Defines what data is expected (Request) and what is returned (Response).
-   Handles validation (e.g., "Email must be valid", "Name is required").
-   Decouples the internal domain model from the external API.

### 3. Domain (`app/domain/`)
**The Business Logic**.
-   Represents the core entities (e.g., `User`, `Course`).
-   Enforces business rules (e.g., "A course must have a syllabus").
-   Independent of the database or API framework.

### 4. Repository (`app/db/`)
**The Data Access Layer**.
-   Handles all interactions with the database (MongoDB).
-   Converts Domain objects to Database documents and vice versa.
-   Abstracts the database details from the rest of the app.

### 5. Database (MongoDB)
**The Storage**.
-   Stores the data as JSON-like documents.

---

### Example Flow: Creating a User

1.  **Client** sends `POST /signup` with JSON data.
2.  **Router** (`auth.py`) receives data and validates it against `SignupRequest` **Schema**.
3.  **Router** calls `UserRepository.create_user()`.
4.  **Repository** (`repository.py`) checks for duplicates, creates a `User` document, and saves it to **MongoDB**.
5.  **Repository** returns the created user data.
6.  **Router** converts the data to `LoginResponse` **Schema** (hiding sensitive fields like password hash) and sends it back to **Client**.

---

## User Roles & Authentication

### Roles
-   **Student**: Default role. View courses, submit assignments.
-   **Tutor**: Manage courses, grade assignments. Created by Admins.
-   **Admin**: Full system access.

### Authentication Flow
-   **Signup**: `POST /api/v1/auth/signup` (Creates Student account)
-   **Login**: `POST /api/v1/auth/login` (Returns JWT)
-   **Tutor Creation**: `POST /api/v1/users/tutors` (Admin only)

**Security**:
-   JWT tokens (HS256) with role claims.
-   Password hashing using bcrypt.
-   RBAC enforced via dependencies (e.g., `require_admin`).

---

## Configuration (.env)

```ini
# JWT
JWT_SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# MongoDB
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB=appdb
MONGODB_USERNAME=
MONGODB_PASSWORD=

# Mailtrap (Email Service)
MAILTRAP_API_TOKEN=
MAILTRAP_SENDER_EMAIL=noreply@example.com
MAILTRAP_SENDER_NAME=Support
MAILTRAP_USE_SANDBOX=True

# App
DEBUG=false
```

---

## Key Features & Collections

### Core Collections
-   **Courses**: Rich content with syllabus, objectives, and prerequisites.
-   **Course Categories**: Categorization for courses.
-   **Job Roles**: Link courses to career paths.
-   **Vendors**: Course providers.
-   **Assignments & Submissions**: Education flow.
-   **Schedules**: Course sessions with tutors, dates, and times.
-   **Enrollments**: Student enrollments in specific schedules, tracking progress and payments.

### Deployment
-   **Docker**: Includes `Dockerfile` and `docker-compose.yml`.
-   **DigitalOcean**: Ready for App Platform (`app.yaml`).

### Error Handling
Standard HTTP status codes used: `200` (Success), `201` (Created), `400` (Bad Request), `401` (Unauthorized), `403` (Forbidden), `404` (Not Found), `422` (Validation Error).
