"""Certification aggregate root."""

from __future__ import annotations

from datetime import datetime
from typing import Any


class Certification:
    """
    Certification aggregate.

    Represents a certification provided by a vendor.
    """

    def __init__(
        self,
        id: str,
        vendor_id: str,
        name: str,
        description: str | None,
        url: str | None,
        created_at: datetime,
        updated_at: datetime,
    ) -> None:
        """
        Initialize a Certification.

        Args:
            id: Unique identifier (MongoDB ObjectId as string)
            vendor_id: Reference to Vendor ID
            name: Certification name
            description: Optional textual description
            url: Optional URL info
            created_at: Creation timestamp
            updated_at: Last update timestamp
        """
        self.id = id
        self.vendor_id = vendor_id
        self.name = name
        self.description = description
        self.url = url
        self.created_at = created_at
        self.updated_at = updated_at

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "vendor_id": self.vendor_id,
            "name": self.name,
            "description": self.description,
            "url": self.url,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
