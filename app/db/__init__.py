"""Database module initialization."""

from app.db.mongo import connect_to_mongodb, close_mongodb_connection, get_database
from app.db.repository import UserRepository
from app.db.course_category_repository import CourseCategoryRepository
from app.db.job_role_repository import JobRoleRepository

__all__ = [
    "connect_to_mongodb",
    "close_mongodb_connection",
    "get_database",
    "UserRepository",
    "CourseCategoryRepository",
    "JobRoleRepository",
]
