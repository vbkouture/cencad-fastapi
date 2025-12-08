"""Script to add vendors to the database with specific IDs.

Usage:
    python scripts/add_vendors.py
    python scripts/add_vendors.py --file courses-2025-11-10.json
    python scripts/add_vendors.py --id "my-vendor-id" --name "Vendor Name" --description "Description" --logo "https://..."
"""

import asyncio
import json
import sys
from argparse import ArgumentParser
from datetime import UTC, datetime

from motor.motor_asyncio import AsyncIOMotorClient

from app.core.config import settings


def utcnow() -> datetime:
    """Get current UTC time."""
    return datetime.now(UTC)


async def add_vendor(
    vendor_id: str,
    name: str | None,
    description: str | None,
    logo: str | None,
    mongodb_url: str,
    db_name: str,
) -> str:
    """Add a vendor to the database with a specific ID."""
    client = AsyncIOMotorClient(mongodb_url)  # type: ignore[var-annotated]
    db = client[db_name]

    try:
        # Check if vendor already exists
        existing_vendor = await db.vendors.find_one({"_id": vendor_id})
        if existing_vendor:
            return f"⏭️  Vendor '{name}' already exists (ID: {vendor_id})"

        # Create vendor document
        now = utcnow()
        vendor = {
            "_id": vendor_id,
            "id": vendor_id,
            "name": name or "Unknown",
            "description": description or "",
            "logo": logo,
            "created_at": now,
            "updated_at": now,
        }

        # Insert vendor
        await db.vendors.insert_one(vendor)
        return f"✅ Vendor '{name}' created (ID: {vendor_id})"

    finally:
        client.close()


async def add_vendors_from_json(json_file: str, mongodb_url: str, db_name: str) -> None:
    """Add vendors from a JSON file."""
    try:
        with open(json_file) as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"❌ Error: File '{json_file}' not found")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"❌ Error: Invalid JSON in '{json_file}'")
        sys.exit(1)

    # Extract unique vendors
    vendors_dict: dict[str, dict[str, str | None]] = {}
    for item in data:
        if "vendor" in item:
            vendor = item["vendor"]
            vendor_id = vendor.get("id")
            if vendor_id and vendor_id not in vendors_dict:
                vendors_dict[vendor_id] = {
                    "name": vendor.get("name", "Unknown"),
                    "description": vendor.get("description", ""),
                    "logo": vendor.get("logo"),
                }

    if not vendors_dict:
        print("⚠️  No vendors found in JSON file")
        return

    print(f"🏢 Adding {len(vendors_dict)} vendors from '{json_file}'...")
    print(f"   MongoDB URL: {mongodb_url}")
    print(f"   Database: {db_name}\n")

    for vendor_id, vendor_data in vendors_dict.items():
        message = await add_vendor(
            vendor_id=vendor_id,
            name=vendor_data["name"],
            description=vendor_data["description"],
            logo=vendor_data["logo"],
            mongodb_url=mongodb_url,
            db_name=db_name,
        )
        print(f"   {message}")

    print("\n✨ Done!")


def main() -> None:
    """Main entry point."""
    parser = ArgumentParser(description="Add vendors to the database with specific IDs")
    parser.add_argument(
        "--file",
        type=str,
        help="JSON file to extract vendors from",
    )
    parser.add_argument(
        "--id",
        type=str,
        help="Vendor ID (required if --file is not provided)",
    )
    parser.add_argument(
        "--name",
        type=str,
        help="Vendor name (required if --file is not provided)",
    )
    parser.add_argument(
        "--description",
        type=str,
        help="Vendor description (optional)",
    )
    parser.add_argument(
        "--logo",
        type=str,
        help="Vendor logo URL (optional)",
    )

    args = parser.parse_args()

    try:
        if args.file:
            # Add vendors from JSON file
            asyncio.run(
                add_vendors_from_json(
                    json_file=args.file,
                    mongodb_url=settings.mongodb_url,
                    db_name=settings.mongodb_db,
                )
            )
        elif args.id and args.name:
            # Add single vendor with specific ID
            message = asyncio.run(
                add_vendor(
                    vendor_id=args.id,
                    name=args.name,
                    description=args.description or "",
                    logo=args.logo,
                    mongodb_url=settings.mongodb_url,
                    db_name=settings.mongodb_db,
                )
            )
            print(message)
        else:
            print("❌ Error: Provide either --file or both --id and --name")
            parser.print_help()
            sys.exit(1)

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
