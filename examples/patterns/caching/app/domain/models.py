"""Domain models for the caching example."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class User:
    """A user in the system."""

    id: str
    name: str
    email: str
    created_at: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for caching."""
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "User":
        """Create from dictionary (cache deserialization)."""
        created_at = None
        if data.get("created_at"):
            created_at = datetime.fromisoformat(data["created_at"])
        return cls(
            id=data["id"],
            name=data["name"],
            email=data["email"],
            created_at=created_at,
        )
