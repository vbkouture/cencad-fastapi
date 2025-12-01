"""Script to add admin users to the database.

Usage:
    python scripts/add_admin.py
    python scripts/add_admin.py --email admin@example.com --name "Admin User" --password "securepass123"
"""

import asyncio
import sys
from argparse import ArgumentParser
from uuid import uuid4

from motor.motor_asyncio import AsyncIOMotorClient

from app.core.config import settings
from app.core.security import hash_password
from app.domain.users.value_objects import UserRole


async def add_admin(email: str, name: str, password: str, mongodb_url: str, db_name: str) -> None:
    """Add an admin user to the database."""
    client = AsyncIOMotorClient(mongodb_url)
    db = client[db_name]

    try:
        # Check if user already exists
        existing_user = await db.users.find_one({"email": email.lower()})
        if existing_user:
            print(f"❌ User with email '{email}' already exists")
            return

        # Create admin user document
        user_id = str(uuid4())
        admin_user = {
            "_id": user_id,
            "id": user_id,
            "email": email.lower(),
            "name": name,
            "hashed_password": hash_password(password),
            "role": UserRole.ADMIN,
            "is_active": True,
            "created_at": {"$date": "2025-11-10T00:00:00Z"},
            "updated_at": {"$date": "2025-11-10T00:00:00Z"},
        }

        # Insert user
        await db.users.insert_one(admin_user)
        print(f"✅ Admin user created successfully!")
        print(f"   ID: {user_id}")
        print(f"   Email: {email}")
        print(f"   Name: {name}")
        print(f"   Role: {UserRole.ADMIN}")

    finally:
        client.close()


def main() -> None:
    """Main entry point."""
    parser = ArgumentParser(description="Add admin user to the database")
    parser.add_argument(
        "--email",
        type=str,
        default="admin@example.com",
        help="Admin email address (default: admin@example.com)",
    )
    parser.add_argument(
        "--name",
        type=str,
        default="Admin User",
        help="Admin full name (default: Admin User)",
    )
    parser.add_argument(
        "--password",
        type=str,
        default="admin123",
        help="Admin password (default: admin123)",
    )

    args = parser.parse_args()

    print("🔧 Adding admin user...")
    print(f"   MongoDB URL: {settings.mongodb_url}")
    print(f"   Database: {settings.mongodb_db}")

    try:
        asyncio.run(
            add_admin(
                email=args.email,
                name=args.name,
                password=args.password,
                mongodb_url=settings.mongodb_url,
                db_name=settings.mongodb_db,
            )
        )
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
