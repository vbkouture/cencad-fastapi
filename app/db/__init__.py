"""Database module initialization."""

from app.db.contact_form_repository import ContactFormRepository
from app.db.course_category_repository import CourseCategoryRepository
from app.db.job_role_repository import JobRoleRepository
from app.db.mongo import close_mongodb_connection, connect_to_mongodb, get_database
from app.db.repository import UserRepository

__all__ = [
    "connect_to_mongodb",
    "close_mongodb_connection",
    "get_database",
    "UserRepository",
    "CourseCategoryRepository",
    "JobRoleRepository",
    "ContactFormRepository",
]
