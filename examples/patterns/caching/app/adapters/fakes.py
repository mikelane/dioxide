"""Fake adapters for testing.

In tests, we use simple fakes without caching complexity.
This demonstrates profile-based switching.
"""

import fnmatch
from typing import Any

from dioxide import Profile, adapter

from ..domain.models import User
from ..domain.ports import CachePort, UserRepositoryPort


@adapter.for_(UserRepositoryPort, profile=Profile.TEST)
class FakeUserRepository:
    """Simple in-memory user repository for testing.

    No caching complexity - just direct storage.
    This shows how tests can use a simpler implementation.
    """

    def __init__(self) -> None:
        """Initialize with empty storage."""
        self.users: dict[str, User] = {}
        self._email_index: dict[str, str] = {}

    async def get_by_id(self, user_id: str) -> User | None:
        """Get user from in-memory storage."""
        return self.users.get(user_id)

    async def get_by_email(self, email: str) -> User | None:
        """Get user by email from in-memory storage."""
        user_id = self._email_index.get(email)
        if user_id:
            return self.users.get(user_id)
        return None

    async def save(self, user: User) -> None:
        """Save user to in-memory storage."""
        self.users[user.id] = user
        self._email_index[user.email] = user.id

    async def delete(self, user_id: str) -> None:
        """Delete user from in-memory storage."""
        user = self.users.get(user_id)
        if user:
            del self.users[user_id]
            if user.email in self._email_index:
                del self._email_index[user.email]

    async def list_all(self) -> list[User]:
        """List all users from in-memory storage."""
        return list(self.users.values())

    # Test helpers
    def seed(self, *users: User) -> None:
        """Seed repository with test data."""
        for user in users:
            self.users[user.id] = user
            self._email_index[user.email] = user.id

    def clear(self) -> None:
        """Clear all users."""
        self.users.clear()
        self._email_index.clear()


@adapter.for_(CachePort, profile=Profile.TEST)
class FakeCache:
    """Fake cache for testing cache behavior.

    Tracks hits, misses, and operations for test assertions.
    """

    def __init__(self) -> None:
        """Initialize with empty cache and counters."""
        self.data: dict[str, Any] = {}
        self.hit_count: int = 0
        self.miss_count: int = 0
        self.set_count: int = 0
        self.delete_count: int = 0

    async def get(self, key: str) -> Any | None:
        """Get value and track hit/miss."""
        value = self.data.get(key)
        if value is not None:
            self.hit_count += 1
        else:
            self.miss_count += 1
        return value

    async def set(self, key: str, value: Any, ttl_seconds: int = 300) -> None:
        """Set value and track operation."""
        self.data[key] = value
        self.set_count += 1

    async def delete(self, key: str) -> None:
        """Delete value and track operation."""
        if key in self.data:
            del self.data[key]
            self.delete_count += 1

    async def delete_pattern(self, pattern: str) -> None:
        """Delete matching keys."""
        keys_to_delete = [k for k in self.data.keys() if fnmatch.fnmatch(k, pattern)]
        for key in keys_to_delete:
            del self.data[key]
            self.delete_count += 1

    # Test helpers
    def clear(self) -> None:
        """Clear cache and reset counters."""
        self.data.clear()
        self.hit_count = 0
        self.miss_count = 0
        self.set_count = 0
        self.delete_count = 0

    def was_cached(self, key: str) -> bool:
        """Check if a key is in cache."""
        return key in self.data
