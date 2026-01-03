"""
Unified script to seed and verify MongoDB collections.

Usage:
    python scripts/seed_db.py
"""

import asyncio
import json
import os
import sys
from datetime import UTC, datetime
from typing import Any

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

# Add project root to path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings
from app.core.security import hash_password

# Map collection names to seed files and ID fields
COLLECTIONS = [
    {"name": "users", "file": "users.json", "key": "email"},
    {"name": "vendors", "file": "vendors.json", "key": "name"},
    {"name": "certifications", "file": "certifications.json", "key": "_id"},
    {"name": "job_roles", "file": "job_roles.json", "key": "name"},
    {"name": "course_categories", "file": "course_categories.json", "key": "name"},
    {"name": "courses", "file": "courses.json", "key": "title"},
    {"name": "contact-forms", "file": "contact_forms.json", "key": "_id"},
    {
        "name": "schedules",
        "file": "schedules.json",
        "key": "_id",
        "date_fields": ["start_date", "end_date"],
    },
    {
        "name": "enrollments",
        "file": "enrollments.json",
        "key": "_id",
        "date_fields": ["created_at", "paid_at", "enrolled_at", "completed_at"],
        "nested_date_fields": [("instructor_notes", "date")],
    },
]  # type: list[dict[str, Any]]

SEED_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "seed")


async def seed_collection(db: AsyncIOMotorDatabase[Any], collection_info: dict[str, Any]) -> int:
    """Seed a single collection."""
    collection_name = collection_info["name"]
    file_name = collection_info["file"]
    key_field = collection_info["key"]
    date_fields: list[str] = collection_info.get("date_fields", [])
    nested_date_fields: list[tuple[str, str]] = collection_info.get("nested_date_fields", [])

    file_path = os.path.join(SEED_DIR, file_name)

    if not os.path.exists(file_path):
        print(f"⚠️  File not found: {file_name}. Skipping.")
        return 0

    try:
        with open(file_path, encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"❌ Error reading {file_name}: {e}")
        return 0

    if not isinstance(data, list):
        print(f"❌ Invalid format in {file_name}: Expected a list.")
        return 0

    collection = db[collection_name]
    added_count = 0

    print(f"🌱 Seeding {collection_name} from {file_name}...")

    # Clear collection first
    print(f"   🧹 Clearing existing data from {collection_name}...")
    await collection.delete_many({})

    for item in data:
        # Convert _id to ObjectId if present
        if "_id" in item:
            try:
                item["_id"] = ObjectId(item["_id"])
            except Exception:
                pass  # Keep as string if not valid ObjectId, though typically it should be

        # Hash password for users collection
        if collection_name == "users" and "password" in item:
            item["hashed_password"] = hash_password(item.pop("password"))

        # Parse date fields
        for field in date_fields:
            if field in item and item[field]:
                try:
                    # Handle ISO format strings
                    if isinstance(item[field], str):
                        item[field] = datetime.fromisoformat(item[field])
                except ValueError:
                    pass

        # Parse nested date fields (e.g., instructor_notes[].date)
        for list_field, date_key in nested_date_fields:
            if list_field in item and isinstance(item[list_field], list):
                for nested_item in item[list_field]:
                    if isinstance(nested_item, dict) and date_key in nested_item:
                        if isinstance(nested_item[date_key], str):
                            try:
                                nested_item[date_key] = datetime.fromisoformat(
                                    nested_item[date_key]
                                )
                            except ValueError:
                                pass

        # Add timestamps if missing
        now = datetime.now(UTC)
        if "created_at" not in item:
            item["created_at"] = now
        if "updated_at" not in item:
            item["updated_at"] = now

        # Check existence
        query = {}
        if key_field == "_id":
            query = {"_id": item["_id"]}
        else:
            query = {key_field: item.get(key_field)}

        existing = await collection.find_one(query)

        if existing:
            # Optional: Update existing? For now, just skip or maybe update if needed.
            # Let's skip to avoid overwriting user changes, or we could upsert.
            # For seed data, upserting is often better to ensure state.
            # But let's stick to "skip if exists" to be safe, or maybe replace?
            # Let's use replace_one with upsert=True to ensure the seed state matches.
            await collection.replace_one({"_id": item["_id"]}, item, upsert=True)
            # print(f"   Updated/Verified {item.get(key_field)}")
        else:
            await collection.insert_one(item)
            added_count += 1
            # print(f"   Added {item.get(key_field)}")

    print(f"   ✅ Processed {len(data)} items for {collection_name}.")
    return len(data)


async def verify_collection(
    db: AsyncIOMotorDatabase[Any], collection_info: dict[str, Any], expected_count: int
) -> bool:
    """Verify collection count."""
    collection_name = collection_info["name"]
    collection = db[collection_name]

    # We can't strictly check count == expected_count because there might be other data.
    # But we can check if at least the seed data exists.
    # For simplicity in this script, let's just count total documents.

    count = await collection.count_documents({})
    print(f"🧐 Verifying {collection_name}: Found {count} documents (Seed: {expected_count})")

    if count >= expected_count:
        return True
    else:
        print("   ❌ Warning: Found fewer documents than seeded!")
        return False


async def main() -> None:
    print("🚀 Starting database seed and verification...")
    print(f"   Database: {settings.mongodb_db}")

    client: AsyncIOMotorClient[Any] = AsyncIOMotorClient(settings.mongodb_url)
    db = client[settings.mongodb_db]

    try:
        for col_info in COLLECTIONS:
            expected_count = await seed_collection(db, col_info)
            await verify_collection(db, col_info, expected_count)
            print("-" * 30)

        print("\n✨ Seeding and verification completed!")

    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
    finally:
        client.close()


if __name__ == "__main__":
    asyncio.run(main())
