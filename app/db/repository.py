"""User repository for MongoDB persistence."""

from __future__ import annotations

from datetime import UTC
from typing import Any

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection, AsyncIOMotorDatabase

from app.domain.users.value_objects import UserRole


class UserRepository:
    """Repository for User aggregate using MongoDB."""

    def __init__(self, db: AsyncIOMotorDatabase[Any]) -> None:
        """Initialize with MongoDB database instance."""
        self.collection: AsyncIOMotorCollection[dict[str, Any]] = db["users"]

    async def create_user(
        self,
        email: str,
        name: str,
        hashed_password: str,
        role: str,
    ) -> dict[str, Any]:
        """
        Create a new user in the database.

        Args:
            email: User email (normalized to lowercase)
            name: User's full name
            hashed_password: Bcrypt hashed password
            role: User role (admin, tutor, or student)

        Returns:
            Created user document with _id

        Raises:
            ValueError: If email already exists
        """
        # Check if email exists (case-insensitive)
        existing = await self.collection.find_one({"email": email.lower()})
        if existing:
            raise ValueError(f"User with email {email} already exists")

        user_doc: dict[str, Any] = {
            "email": email.lower(),
            "name": name,
            "hashed_password": hashed_password,
            "role": role,
            "is_active": True,
        }

        result = await self.collection.insert_one(user_doc)
        user_doc["_id"] = result.inserted_id

        return user_doc

    async def find_by_email(self, email: str) -> dict[str, Any] | None:
        """
        Find a user by email (case-insensitive).

        Args:
            email: User email

        Returns:
            User document if found, None otherwise
        """
        return await self.collection.find_one({"email": email.lower()})

    async def find_by_id(self, user_id: str) -> dict[str, Any] | None:
        """
        Find a user by ID.

        Args:
            user_id: MongoDB ObjectId as string

        Returns:
            User document if found, None otherwise
        """
        try:
            return await self.collection.find_one({"_id": ObjectId(user_id)})
        except Exception:
            return None

    async def get_all_users(self) -> list[dict[str, Any]]:
        """Get all users from database."""
        return await self.collection.find().to_list(length=None)

    async def find_users_by_role(self, role: UserRole) -> list[dict[str, Any]]:
        """
        Find all users with a specific role.

        Args:
            role: User role to filter by

        Returns:
            List of user documents with the specified role
        """
        return await self.collection.find({"role": role}).to_list(length=None)

    async def update_user_role(self, user_id: str, new_role: UserRole) -> bool:
        """
        Update a user's role.

        Args:
            user_id: MongoDB ObjectId as string
            new_role: New role for the user

        Returns:
            True if updated, False if user not found
        """
        try:
            result = await self.collection.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": {"role": new_role}},
            )
            return result.modified_count > 0
        except Exception:
            return False

    async def update_user_status(self, user_id: str, is_active: bool) -> bool:
        """
        Update a user's active status.

        Args:
            user_id: MongoDB ObjectId as string
            is_active: Active status

        Returns:
            True if updated, False if user not found
        """
        try:
            result = await self.collection.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": {"is_active": is_active}},
            )
            return result.modified_count > 0
        except Exception:
            return False

    async def delete_user(self, user_id: str) -> bool:
        """
        Delete a user from database.

        Args:
            user_id: MongoDB ObjectId as string

        Returns:
            True if deleted, False if user not found
        """
        try:
            result = await self.collection.delete_one({"_id": ObjectId(user_id)})
            return result.deleted_count > 0
        except Exception:
            return False

    async def create_indexes(self) -> None:
        """Create necessary database indexes for performance."""
        # Create unique index on email for fast lookups and uniqueness
        await self.collection.create_index("email", unique=True)

        # Create indexes for common queries
        await self.collection.create_index("role")
        await self.collection.create_index("is_active")

    async def update_password(self, user_id: str, hashed_password: str) -> bool:
        """
        Update a user's password.

        Args:
            user_id: MongoDB ObjectId as string
            hashed_password: New hashed password

        Returns:
            True if updated, False if user not found
        """
        try:
            result = await self.collection.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": {"hashed_password": hashed_password}},
            )
            return result.modified_count > 0
        except Exception:
            return False

    async def update_name(self, user_id: str, name: str) -> bool:
        """
        Update a user's name.

        Args:
            user_id: MongoDB ObjectId as string
            name: New name for the user

        Returns:
            True if updated, False if user not found
        """
        try:
            result = await self.collection.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": {"name": name}},
            )
            return result.modified_count > 0
        except Exception:
            return False

    async def create_password_reset_token(
        self,
        user_id: str,
        token: str,
        expires_at: Any,
    ) -> bool:
        """
        Create a password reset token.

        Args:
            user_id: MongoDB ObjectId as string
            token: Reset token
            expires_at: Token expiration datetime

        Returns:
            True if created successfully
        """
        try:
            # Get password_reset_tokens collection
            reset_collection: AsyncIOMotorCollection[dict[str, Any]] = self.collection.database[
                "password_reset_tokens"
            ]

            # Delete any existing tokens for this user
            await reset_collection.delete_many({"user_id": user_id})

            # Create new token
            await reset_collection.insert_one(
                {
                    "user_id": user_id,
                    "token": token,
                    "expires_at": expires_at,
                    "used": False,
                }
            )
            return True
        except Exception:
            return False

    async def find_password_reset_token(self, token: str) -> dict[str, Any] | None:
        """
        Find a valid password reset token.

        Args:
            token: Reset token to find

        Returns:
            Token document if found and valid, None otherwise
        """
        try:
            from datetime import datetime

            reset_collection: AsyncIOMotorCollection[dict[str, Any]] = self.collection.database[
                "password_reset_tokens"
            ]

            token_doc = await reset_collection.find_one(
                {
                    "token": token,
                    "used": False,
                    "expires_at": {"$gt": datetime.now(UTC)},
                }
            )
            return token_doc
        except Exception:
            return None

    async def delete_password_reset_token(self, token: str) -> bool:
        """
        Mark a password reset token as used.

        Args:
            token: Reset token to mark as used

        Returns:
            True if marked successfully
        """
        try:
            reset_collection: AsyncIOMotorCollection[dict[str, Any]] = self.collection.database[
                "password_reset_tokens"
            ]

            result = await reset_collection.update_one(
                {"token": token},
                {"$set": {"used": True}},
            )
            return result.modified_count > 0
        except Exception:
            return False

    async def create_password_reset_indexes(self) -> None:
        """Create indexes for password reset tokens collection."""
        try:
            reset_collection: AsyncIOMotorCollection[dict[str, Any]] = self.collection.database[
                "password_reset_tokens"
            ]

            # Create TTL index to automatically delete expired tokens
            await reset_collection.create_index("expires_at", expireAfterSeconds=0)

            # Create index on token for fast lookups
            await reset_collection.create_index("token")

            # Create index on user_id
            await reset_collection.create_index("user_id")
        except Exception:
            pass
