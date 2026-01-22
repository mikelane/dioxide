"""Port definitions using ABC (dependency-injector style).

dependency-injector typically uses ABC-based interfaces.
"""

from abc import ABC, abstractmethod


class UserRepository(ABC):
    """Abstract base class for user persistence."""

    @abstractmethod
    async def get(self, user_id: str) -> dict | None:
        """Get a user by ID."""
        pass

    @abstractmethod
    async def save(self, user: dict) -> dict:
        """Save a user and return the saved user."""
        pass

    @abstractmethod
    async def delete(self, user_id: str) -> bool:
        """Delete a user by ID."""
        pass


class EmailService(ABC):
    """Abstract base class for email sending."""

    @abstractmethod
    async def send(self, to: str, subject: str, body: str) -> bool:
        """Send an email."""
        pass


class CacheService(ABC):
    """Abstract base class for caching."""

    @abstractmethod
    async def get(self, key: str) -> str | None:
        """Get a value from cache."""
        pass

    @abstractmethod
    async def set(self, key: str, value: str, ttl: int = 300) -> None:
        """Set a value in cache with TTL."""
        pass

    @abstractmethod
    async def delete(self, key: str) -> None:
        """Delete a value from cache."""
        pass
