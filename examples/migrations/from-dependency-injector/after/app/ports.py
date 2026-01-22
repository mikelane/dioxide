"""Port definitions using Protocol (dioxide style).

dioxide uses Protocol-based interfaces which work better with type checkers
and don't require inheritance from ABC.
"""

from typing import Protocol


class UserRepositoryPort(Protocol):
    """Port for user persistence.

    Protocols define the interface contract without requiring inheritance.
    Type checkers verify that adapters implement all methods.
    """

    async def get(self, user_id: str) -> dict | None:
        """Get a user by ID."""
        ...

    async def save(self, user: dict) -> dict:
        """Save a user and return the saved user."""
        ...

    async def delete(self, user_id: str) -> bool:
        """Delete a user by ID."""
        ...


class EmailPort(Protocol):
    """Port for email sending."""

    async def send(self, to: str, subject: str, body: str) -> bool:
        """Send an email."""
        ...


class CachePort(Protocol):
    """Port for caching."""

    async def get(self, key: str) -> str | None:
        """Get a value from cache."""
        ...

    async def set(self, key: str, value: str, ttl: int = 300) -> None:
        """Set a value in cache with TTL."""
        ...

    async def delete(self, key: str) -> None:
        """Delete a value from cache."""
        ...
