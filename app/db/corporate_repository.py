from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, cast

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection, AsyncIOMotorDatabase

from app.domain.corporate.models import (
    CorporateAccount,
    CorporateLicense,
    CorporateTrainee,
    TraineeAssignment,
)


class CorporateRepository:
    """Repository for Corporate domain aggregates using MongoDB."""

    def __init__(self, db: AsyncIOMotorDatabase[Any]) -> None:
        self.accounts: AsyncIOMotorCollection[dict[str, Any]] = db["corporate_accounts"]
        self.licenses: AsyncIOMotorCollection[dict[str, Any]] = db["corporate_licenses"]
        self.trainees: AsyncIOMotorCollection[dict[str, Any]] = db["corporate_trainees"]
        self.assignments: AsyncIOMotorCollection[dict[str, Any]] = db["corporate_assignments"]

    # --- Corporate Account ---

    async def create_account(self, account: CorporateAccount) -> bool:
        doc = account.model_dump(mode="json")
        doc["_id"] = ObjectId(account.id)
        del doc["id"]

        try:
            await self.accounts.insert_one(doc)
            return True
        except Exception:
            return False

    async def find_account_by_id(self, account_id: str) -> dict[str, Any] | None:
        try:
            return await self.accounts.find_one({"_id": ObjectId(account_id)})
        except Exception:
            return None

    async def find_account_by_admin(self, user_id: str) -> dict[str, Any] | None:
        return await self.accounts.find_one({"admin_user_ids": user_id})

    async def update_account(self, account_id: str, updates: dict[str, Any]) -> bool:
        try:
            result = await self.accounts.update_one(
                {"_id": ObjectId(account_id)}, {"$set": updates}
            )
            return result.modified_count > 0
        except Exception:
            return False

    # --- Licenses ---

    async def create_license(self, license_obj: CorporateLicense) -> bool:
        doc = license_obj.model_dump(mode="json")
        doc["_id"] = ObjectId(license_obj.id)
        del doc["id"]

        try:
            await self.licenses.insert_one(doc)
            return True
        except Exception:
            return False

    async def get_licenses(
        self, account_id: str, skip: int = 0, limit: int = 20
    ) -> list[dict[str, Any]]:
        cursor = (
            self.licenses.find({"corporate_account_id": account_id})
            .skip(skip)
            .limit(limit)
            .sort("purchased_at", -1)
        )
        return await cursor.to_list(length=limit)

    async def count_licenses(self, account_id: str) -> int:
        return await self.licenses.count_documents({"corporate_account_id": account_id})

    async def find_license_by_id(self, license_id: str) -> dict[str, Any] | None:
        try:
            return await self.licenses.find_one({"_id": ObjectId(license_id)})
        except Exception:
            return None

    async def increment_assigned_seats(self, license_id: str) -> bool:
        try:
            result = await self.licenses.update_one(
                {"_id": ObjectId(license_id)}, {"$inc": {"assigned_seats": 1}}
            )
            return result.modified_count > 0
        except Exception:
            return False

    async def decrement_assigned_seats(self, license_id: str) -> bool:
        try:
            result = await self.licenses.update_one(
                {"_id": ObjectId(license_id), "assigned_seats": {"$gt": 0}},
                {"$inc": {"assigned_seats": -1}},
            )
            return result.modified_count > 0
        except Exception:
            return False

    # --- Trainees ---

    async def create_trainee(self, trainee: CorporateTrainee) -> bool:
        doc = trainee.model_dump(mode="json")
        doc["_id"] = ObjectId(trainee.id)
        del doc["id"]

        try:
            await self.trainees.insert_one(doc)
            return True
        except Exception:
            return False

    async def find_trainee_by_id(self, trainee_id: str) -> dict[str, Any] | None:
        try:
            return await self.trainees.find_one({"_id": ObjectId(trainee_id)})
        except Exception:
            return None

    async def find_trainee_by_email(self, account_id: str, user_id: str) -> dict[str, Any] | None:
        # Check if this user is already a trainee for this account
        return await self.trainees.find_one(
            {"corporate_account_id": account_id, "user_id": user_id}
        )

    async def get_trainees(
        self, account_id: str, skip: int = 0, limit: int = 20
    ) -> list[dict[str, Any]]:
        cursor = (
            self.trainees.find({"corporate_account_id": account_id})
            .skip(skip)
            .limit(limit)
            .sort("invited_at", -1)
        )
        return await cursor.to_list(length=limit)

    async def count_trainees(self, account_id: str) -> int:
        return await self.trainees.count_documents({"corporate_account_id": account_id})

    async def remove_trainee(self, trainee_id: str) -> bool:
        try:
            result = await self.trainees.delete_one({"_id": ObjectId(trainee_id)})
            return result.deleted_count > 0
        except Exception:
            return False

    # --- Assignments ---

    async def create_assignment(self, assignment: TraineeAssignment) -> bool:
        doc = assignment.model_dump(mode="json")
        doc["_id"] = ObjectId(assignment.id)
        del doc["id"]

        try:
            await self.assignments.insert_one(doc)
            return True
        except Exception:
            return False

    async def remove_assignment(self, trainee_id: str, license_id: str) -> bool:
        try:
            result = await self.assignments.delete_one(
                {"trainee_id": trainee_id, "license_id": license_id}
            )
            return result.deleted_count > 0
        except Exception:
            return False

    async def find_assignment(self, trainee_id: str, license_id: str) -> dict[str, Any] | None:
        return await self.assignments.find_one({"trainee_id": trainee_id, "license_id": license_id})

    # --- Dashboard Stats Helper ---

    async def get_dashboard_stats(self, account_id: str) -> dict[str, Any]:
        # Aggregate licenses
        pipeline = [
            {"$match": {"corporate_account_id": account_id}},
            {
                "$group": {
                    "_id": None,
                    "total_licenses": {"$sum": "$total_seats"},
                    "assigned_seats": {"$sum": "$assigned_seats"},
                    "total_spend": {"$sum": "$amount_total"},
                    "courses_count": {"$addToSet": "$course_id"},
                }
            },
        ]
        license_stats = await self.licenses.aggregate(
            cast(Sequence[Mapping[str, Any]], pipeline)
        ).to_list(length=1)

        trainee_count = await self.count_trainees(account_id)
        # Assuming all current trainees in list are active for simplicity,
        # or we could filter by is_active=True
        active_trainees = await self.trainees.count_documents(
            {"corporate_account_id": account_id, "is_active": True}
        )

        if not license_stats:
            return {
                "total_licenses": 0,
                "assigned_seats": 0,
                "total_spend": 0,
                "courses_purchased": 0,
                "total_trainees": trainee_count,
                "active_trainees": active_trainees,
            }

        stats = license_stats[0]
        return {
            "total_licenses": stats["total_licenses"],
            "assigned_seats": stats["assigned_seats"],
            "total_spend": stats["total_spend"],
            "courses_purchased": len(stats["courses_count"]),
            "total_trainees": trainee_count,
            "active_trainees": active_trainees,
        }

    async def create_indexes(self) -> None:
        """Create indexes for corporate collections."""
        # Account
        await self.accounts.create_index("admin_user_ids")

        # License
        await self.licenses.create_index("corporate_account_id")

        # Trainee
        await self.trainees.create_index("corporate_account_id")
        await self.trainees.create_index("user_id")

        # Assignment
        await self.assignments.create_index([("trainee_id", 1), ("license_id", 1)], unique=True)
