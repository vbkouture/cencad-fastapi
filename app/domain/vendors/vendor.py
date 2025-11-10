"""Vendor aggregate root."""

from __future__ import annotations

from datetime import datetime
from typing import Any


class Vendor:
    """
    Vendor aggregate.

    Represents a vendor in the system with name, description, and logo.
    """

    def __init__(
        self,
        id: str,
        name: str,
        description: str,
        logo: str | None,
        created_at: datetime,
        updated_at: datetime,
    ) -> None:
        """
        Initialize a Vendor.

        Args:
            id: Unique identifier (MongoDB ObjectId as string)
            name: Vendor name
            description: Vendor description
            logo: Optional vendor logo URL
            created_at: Creation timestamp
            updated_at: Last update timestamp
        """
        self.id = id
        self.name = name
        self.description = description
        self.logo = logo
        self.created_at = created_at
        self.updated_at = updated_at

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "logo": self.logo,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
