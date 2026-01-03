from fastapi import APIRouter

from .analytics import router as analytics_router
from .assignments import router as assignments_router
from .auth import router as auth_router
from .certifications import router as certifications_router
from .contact_forms import router as contact_forms_router
from .corporate import router as corporate_router
from .course_categories import router as course_categories_router
from .courses import router as courses_router
from .enrollments import router as enrollments_router
from .job_roles import router as job_roles_router
from .payments import router as payments_router
from .ping import router as ping_router
from .schedules import router as schedules_router
from .submissions import router as submissions_router
from .users import router as users_router
from .vendors import router as vendors_router

__all__ = [
    "analytics_router",
    "assignments_router",
    "auth_router",
    "certifications_router",
    "contact_forms_router",
    "corporate_router",
    "courses_router",
    "course_categories_router",
    "job_roles_router",
    "ping_router",
    "submissions_router",
    "schedules_router",
    "enrollments_router",
    "payments_router",
    "users_router",
    "vendors_router",
]


def get_v1_router() -> APIRouter:
    """
    Compose all v1 routers here so app/main.py stays simple.

    Feature-based routing organization:
    - auth: User authentication (signup, login)
    - contact-forms: Contact form submissions (public POST, admin GET/DELETE)
    - course-categories: Course category management (CRUD)
    - job-roles: Job role management (CRUD)
    - vendors: Vendor management (CRUD)
    - courses: Course management (CRUD, enrollment)
    - assignments: Assignment management
    - submissions: Student submissions and feedback
    - users: Admin user management
    - analytics: Reports and analytics
    - ping: Health check
    """
    router = APIRouter(prefix="/api/v1")

    # Meta endpoints
    router.include_router(ping_router)

    # Authentication
    router.include_router(auth_router)

    # Public forms
    router.include_router(contact_forms_router)

    # Corporate
    router.include_router(corporate_router)

    # Core features (mixed roles)
    router.include_router(course_categories_router)
    router.include_router(job_roles_router)
    router.include_router(certifications_router)
    router.include_router(vendors_router)
    router.include_router(courses_router)
    router.include_router(assignments_router)
    router.include_router(submissions_router)
    router.include_router(schedules_router)
    router.include_router(enrollments_router)
    router.include_router(payments_router)

    # Admin & Analytics
    router.include_router(users_router)
    router.include_router(analytics_router)

    return router
