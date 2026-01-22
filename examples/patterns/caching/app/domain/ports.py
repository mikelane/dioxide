"""Port definitions for the caching example.

This example has three ports:
1. UserRepositoryPort - The main interface services use
2. DatabaseUserRepositoryPort - Direct database access (used by caching wrapper)
3. CachePort - Cache storage interface
"""

from typing import Any, Protocol

from .models import User


class UserRepositoryPort(Protocol):
    """Port for user repository operations.

    Services depend on this port. It may be implemented by:
    - CachingUserRepository (production) - adds caching layer
    - FakeUserRepository (test) - simple in-memory storage
    """

    async def get_by_id(self, user_id: str) -> User | None:
        """Get a user by ID."""
        ...

    async def get_by_email(self, email: str) -> User | None:
        """Get a user by email."""
        ...

    async def save(self, user: User) -> None:
        """Save a user (create or update)."""
        ...

    async def delete(self, user_id: str) -> None:
        """Delete a user by ID."""
        ...

    async def list_all(self) -> list[User]:
        """List all users."""
        ...


class DatabaseUserRepositoryPort(Protocol):
    """Port for direct database access.

    This is the "inner" repository that CachingUserRepository wraps.
    It provides the actual database operations without caching.

    Why a separate port?
    - Caching is an infrastructure concern, not domain
    - We need to inject both the database repo AND cache into the caching wrapper
    - Test fakes don't need this complexity
    """

    async def get_by_id(self, user_id: str) -> User | None:
        """Get a user by ID from database."""
        ...

    async def get_by_email(self, email: str) -> User | None:
        """Get a user by email from database."""
        ...

    async def save(self, user: User) -> None:
        """Save a user to database."""
        ...

    async def delete(self, user_id: str) -> None:
        """Delete a user from database."""
        ...

    async def list_all(self) -> list[User]:
        """List all users from database."""
        ...


class CachePort(Protocol):
    """Port for cache operations."""

    async def get(self, key: str) -> Any | None:
        """Get a value from cache."""
        ...

    async def set(self, key: str, value: Any, ttl_seconds: int = 300) -> None:
        """Set a value in cache with TTL."""
        ...

    async def delete(self, key: str) -> None:
        """Delete a value from cache."""
        ...

    async def delete_pattern(self, pattern: str) -> None:
        """Delete all keys matching pattern."""
        ...
