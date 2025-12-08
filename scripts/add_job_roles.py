"""Script to add job roles to the database.

Usage:
    python scripts/add_job_roles.py
    python scripts/add_job_roles.py --name "Frontend Developer" --description "Build user interfaces"
"""

import asyncio
import sys
from argparse import ArgumentParser
from datetime import UTC, datetime
from uuid import uuid4

from motor.motor_asyncio import AsyncIOMotorClient

from app.core.config import settings


def utcnow() -> datetime:
    """Get current UTC time."""
    return datetime.now(UTC)


# Default job roles to seed
DEFAULT_JOB_ROLES = [
    {
        "name": "Frontend Developer",
        "description": "Build responsive and interactive user interfaces using modern web technologies",
    },
    {
        "name": "Backend Developer",
        "description": "Develop server-side logic, APIs, and database systems",
    },
    {
        "name": "Full Stack Developer",
        "description": "Work on both frontend and backend of web applications",
    },
    {
        "name": "Mobile Developer",
        "description": "Create native and cross-platform mobile applications",
    },
    {
        "name": "Data Scientist",
        "description": "Analyze data and build machine learning models",
    },
    {
        "name": "DevOps Engineer",
        "description": "Manage infrastructure, deployment, and CI/CD pipelines",
    },
    {
        "name": "Cloud Architect",
        "description": "Design and implement cloud solutions on major platforms",
    },
    {
        "name": "UI/UX Designer",
        "description": "Create user-friendly and visually appealing designs",
    },
    {
        "name": "QA Engineer",
        "description": "Test applications and ensure code quality",
    },
    {
        "name": "Security Engineer",
        "description": "Ensure application security and data protection",
    },
]


async def add_job_role(name: str, description: str, mongodb_url: str, db_name: str) -> str:
    """Add a job role to the database."""
    client = AsyncIOMotorClient(mongodb_url)  # type: ignore[var-annotated]
    db = client[db_name]

    try:
        # Check if job role already exists
        existing_role = await db.job_roles.find_one(
            {"name": {"$regex": f"^{name}$", "$options": "i"}}
        )
        if existing_role:
            return f"⏭️  Job role '{name}' already exists (ID: {existing_role['_id']})"

        # Create job role document
        role_id = str(uuid4())
        now = utcnow()
        job_role = {
            "_id": role_id,
            "id": role_id,
            "name": name,
            "description": description,
            "created_at": now,
            "updated_at": now,
        }

        # Insert job role
        await db.job_roles.insert_one(job_role)
        return f"✅ Job role '{name}' created (ID: {role_id})"

    finally:
        client.close()


async def add_multiple_job_roles(
    job_roles: list[dict[str, str]], mongodb_url: str, db_name: str
) -> None:
    """Add multiple job roles to the database."""
    print(f"💼 Adding {len(job_roles)} job roles...")
    print(f"   MongoDB URL: {mongodb_url}")
    print(f"   Database: {db_name}\n")

    for role in job_roles:
        message = await add_job_role(
            name=role["name"],
            description=role["description"],
            mongodb_url=mongodb_url,
            db_name=db_name,
        )
        print(f"   {message}")

    print("\n✨ Done!")


def main() -> None:
    """Main entry point."""
    parser = ArgumentParser(description="Add job roles to the database")
    parser.add_argument(
        "--name",
        type=str,
        help="Job role name (if not provided, will add default roles)",
    )
    parser.add_argument(
        "--description",
        type=str,
        help="Job role description (required if --name is provided)",
    )

    args = parser.parse_args()

    try:
        if args.name:
            if not args.description:
                print("❌ Error: --description is required when using --name")
                sys.exit(1)

            # Add single job role
            asyncio.run(
                add_job_role(
                    name=args.name,
                    description=args.description,
                    mongodb_url=settings.mongodb_url,
                    db_name=settings.mongodb_db,
                )
            )
        else:
            # Add default job roles
            asyncio.run(
                add_multiple_job_roles(
                    job_roles=DEFAULT_JOB_ROLES,
                    mongodb_url=settings.mongodb_url,
                    db_name=settings.mongodb_db,
                )
            )
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
