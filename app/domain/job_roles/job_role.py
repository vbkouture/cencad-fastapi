"""Job role aggregate root."""

from __future__ import annotations

from datetime import datetime
from typing import Any


class JobRole:
    """
    Job Role aggregate.

    Represents a job role in the system with name and description.
    """

    def __init__(
        self,
        id: str,
        name: str,
        description: str,
        created_at: datetime,
        updated_at: datetime,
    ) -> None:
        """
        Initialize a JobRole.

        Args:
            id: Unique identifier (MongoDB ObjectId as string)
            name: Job role name
            description: Job role description
            created_at: Creation timestamp
            updated_at: Last update timestamp
        """
        self.id = id
        self.name = name
        self.description = description
        self.created_at = created_at
        self.updated_at = updated_at

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
