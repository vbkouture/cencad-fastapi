"""Script to add course categories to the database.

Usage:
    python scripts/add_categories.py
    python scripts/add_categories.py --name "Web Development" --description "Learn web development"
"""

import asyncio
import sys
from argparse import ArgumentParser
from datetime import datetime, timezone
from uuid import uuid4

from motor.motor_asyncio import AsyncIOMotorClient

from app.core.config import settings


def utcnow() -> datetime:
    """Get current UTC time."""
    return datetime.now(timezone.utc)


# Default categories to seed
DEFAULT_CATEGORIES = [
    {
        "name": "Web Development",
        "description": "Learn modern web development with HTML, CSS, JavaScript, and frameworks",
    },
    {
        "name": "Mobile Development",
        "description": "Build iOS and Android applications with React Native and Flutter",
    },
    {
        "name": "Data Science",
        "description": "Master data analysis, machine learning, and artificial intelligence",
    },
    {
        "name": "Cloud & DevOps",
        "description": "Deploy and manage applications on AWS, Azure, and Google Cloud",
    },
    {
        "name": "Backend Development",
        "description": "Build scalable backend systems with Python, Node.js, and Java",
    },
    {
        "name": "UI/UX Design",
        "description": "Design beautiful and user-friendly interfaces",
    },
]


async def add_category(
    name: str, description: str, mongodb_url: str, db_name: str
) -> str:
    """Add a course category to the database."""
    client = AsyncIOMotorClient(mongodb_url)
    db = client[db_name]

    try:
        # Check if category already exists
        existing_category = await db.course_categories.find_one(
            {"name": {"$regex": f"^{name}$", "$options": "i"}}
        )
        if existing_category:
            return f"⏭️  Category '{name}' already exists (ID: {existing_category['_id']})"

        # Create category document
        category_id = str(uuid4())
        now = utcnow()
        category = {
            "_id": category_id,
            "id": category_id,
            "name": name,
            "description": description,
            "created_at": now,
            "updated_at": now,
        }

        # Insert category
        await db.course_categories.insert_one(category)
        return f"✅ Category '{name}' created (ID: {category_id})"

    finally:
        client.close()


async def add_multiple_categories(
    categories: list[dict[str, str]], mongodb_url: str, db_name: str
) -> None:
    """Add multiple categories to the database."""
    print(f"📚 Adding {len(categories)} course categories...")
    print(f"   MongoDB URL: {mongodb_url}")
    print(f"   Database: {db_name}\n")

    for category in categories:
        message = await add_category(
            name=category["name"],
            description=category["description"],
            mongodb_url=mongodb_url,
            db_name=db_name,
        )
        print(f"   {message}")

    print("\n✨ Done!")


def main() -> None:
    """Main entry point."""
    parser = ArgumentParser(description="Add course categories to the database")
    parser.add_argument(
        "--name",
        type=str,
        help="Category name (if not provided, will add default categories)",
    )
    parser.add_argument(
        "--description",
        type=str,
        help="Category description (required if --name is provided)",
    )

    args = parser.parse_args()

    try:
        if args.name:
            if not args.description:
                print("❌ Error: --description is required when using --name")
                sys.exit(1)

            # Add single category
            asyncio.run(
                add_category(
                    name=args.name,
                    description=args.description,
                    mongodb_url=settings.mongodb_url,
                    db_name=settings.mongodb_db,
                )
            )
        else:
            # Add default categories
            asyncio.run(
                add_multiple_categories(
                    categories=DEFAULT_CATEGORIES,
                    mongodb_url=settings.mongodb_url,
                    db_name=settings.mongodb_db,
                )
            )
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
