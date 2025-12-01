"""Script to add courses to the database from a JSON file.

Follows the current database schema for Course, CourseDetails, and SyllabusWeek.

Usage:
    python scripts/add_courses.py --file courses-2025-11-10.json
    python scripts/add_courses.py --file courses.json --skip-errors
"""

import asyncio
import json
import sys
from argparse import ArgumentParser
from datetime import datetime, timezone
from typing import Any

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient

from app.core.config import settings
from app.domain.courses.course import CourseLevel


def utcnow() -> datetime:
    """Get current UTC time."""
    return datetime.now(timezone.utc)


def parse_course_level(level_str: str | None) -> str:
    """Parse and validate course level."""
    if not level_str:
        return CourseLevel.BEGINNER.value

    level_upper = level_str.upper().strip()

    # Try to match against enum values
    for level in CourseLevel:
        if level.value == level_upper:
            return level.value

    # Default fallback
    print(f"   ⚠️  Unknown level '{level_str}', defaulting to BEGINNER")
    return CourseLevel.BEGINNER.value


def build_course_details(item: dict[str, Any]) -> dict[str, Any]:
    """Build courseDetails object from JSON item."""
    course_details = item.get("courseDetails", {})

    return {
        "overview": course_details.get("overview", ""),
        "objectives": course_details.get("objectives", []),
        "prerequisites": course_details.get("prerequisites", []),
        "syllabus": course_details.get("syllabus", []),
    }


async def add_course(
    course_id: str,
    item: dict[str, Any],
    mongodb_url: str,
    db_name: str,
    skip_errors: bool = False,
) -> tuple[bool, str]:
    """Add a single course to the database."""
    client = AsyncIOMotorClient(mongodb_url)
    db = client[db_name]

    try:
        # Check if course already exists
        existing_course = await db.courses.find_one({"_id": course_id})
        if existing_course:
            return True, f"⏭️  Course '{item.get('title', 'Unknown')}' already exists"

        # Build course document
        course_doc: dict[str, Any] = {
            "_id": course_id,
            "id": course_id,
            "title": item.get("title", f"Course {course_id}"),
            "description": item.get("description", ""),
            "duration": item.get("duration", ""),
            "level": parse_course_level(item.get("level")),
            "url": item.get("url"),
            "language": item.get("language"),
            "image": item.get("image"),
            "rating": item.get("rating"),
            "students": item.get("students"),
            "certifications": item.get("certification"),  # Could be string or None
            "cost": item.get("cost"),
            "courseDetails": build_course_details(item),
        }

        # Add optional relationship IDs
        if item.get("vendorId"):
            course_doc["vendorId"] = item["vendorId"]

        if item.get("categoryId"):
            course_doc["categoryId"] = item["categoryId"]

        # Handle job roles
        job_role_ids = item.get("jobRoles", [])
        if job_role_ids and isinstance(job_role_ids, list):
            course_doc["jobRoleIds"] = job_role_ids
        else:
            course_doc["jobRoleIds"] = []

        # Add timestamps
        course_doc["created_at"] = utcnow()
        course_doc["updated_at"] = utcnow()

        # Insert course
        await db.courses.insert_one(course_doc)
        return True, f"✅ Course '{item.get('title', 'Unknown')}' created"

    except Exception as e:
        error_msg = f"❌ Error adding course '{item.get('title', 'Unknown')}': {str(e)}"
        if skip_errors:
            return False, error_msg
        else:
            raise

    finally:
        client.close()


async def add_courses_from_json(
    json_file: str, mongodb_url: str, db_name: str, skip_errors: bool = False
) -> None:
    """Add courses from a JSON file."""
    try:
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"❌ Error: File '{json_file}' not found")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON in '{json_file}': {e}")
        sys.exit(1)

    if not isinstance(data, list):
        print("❌ Error: JSON file must contain an array of courses")
        sys.exit(1)

    print(f"📚 Adding {len(data)} courses from '{json_file}'...")
    print(f"   MongoDB URL: {mongodb_url}")
    print(f"   Database: {db_name}\n")

    successful = 0
    skipped = 0
    failed = 0

    for idx, item in enumerate(data, 1):
        if not isinstance(item, dict):
            print(f"   ⏭️  Skipping item {idx}: Not a valid course object")
            skipped += 1
            continue

        # Use provided ID or generate one
        course_id = item.get("id", str(ObjectId()))

        try:
            success, message = await add_course(
                course_id=course_id,
                item=item,
                mongodb_url=mongodb_url,
                db_name=db_name,
                skip_errors=skip_errors,
            )

            print(f"   [{idx}/{len(data)}] {message}")

            if success:
                if "already exists" in message:
                    skipped += 1
                else:
                    successful += 1
            else:
                failed += 1

        except Exception as e:
            print(f"   [{idx}/{len(data)}] ❌ Error: {str(e)}")
            failed += 1

            if not skip_errors:
                print(f"\n❌ Failed at course {idx}. Use --skip-errors to continue.")
                sys.exit(1)

    print(f"\n✨ Summary:")
    print(f"   ✅ Added: {successful}")
    print(f"   ⏭️  Skipped: {skipped}")
    print(f"   ❌ Failed: {failed}")
    print(f"   📊 Total: {successful + skipped + failed}/{len(data)}")

    if failed > 0 and not skip_errors:
        sys.exit(1)


def main() -> None:
    """Main entry point."""
    parser = ArgumentParser(
        description="Add courses to the database from a JSON file"
    )
    parser.add_argument(
        "--file",
        type=str,
        required=True,
        help="JSON file containing courses (required)",
    )
    parser.add_argument(
        "--skip-errors",
        action="store_true",
        help="Continue on errors instead of stopping",
    )

    args = parser.parse_args()

    try:
        asyncio.run(
            add_courses_from_json(
                json_file=args.file,
                mongodb_url=settings.mongodb_url,
                db_name=settings.mongodb_db,
                skip_errors=args.skip_errors,
            )
        )
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
