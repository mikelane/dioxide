"""Caching repository adapter - the decorator pattern in action.

This adapter wraps a database repository with caching behavior.
It implements UserRepositoryPort and delegates to DatabaseUserRepositoryPort.
"""

from dioxide import Profile, adapter

from ..domain.models import User
from ..domain.ports import CachePort, DatabaseUserRepositoryPort, UserRepositoryPort


@adapter.for_(UserRepositoryPort, profile=Profile.PRODUCTION)
class CachingUserRepository:
    """User repository with transparent caching.

    This adapter implements the decorator pattern:
    - Implements UserRepositoryPort (same interface as delegate)
    - Wraps DatabaseUserRepositoryPort (the "real" repository)
    - Adds caching behavior using CachePort

    Cache strategy:
    - Cache individual users by ID and email
    - Invalidate on write (save/delete)
    - TTL-based expiration (default 5 minutes)
    """

    def __init__(
        self,
        delegate: DatabaseUserRepositoryPort,
        cache: CachePort,
    ) -> None:
        """Initialize with delegate repository and cache.

        Args:
            delegate: The underlying database repository
            cache: Cache storage for user data
        """
        self.delegate = delegate
        self.cache = cache
        self._ttl = 300  # 5 minutes

    def _user_key(self, user_id: str) -> str:
        """Generate cache key for user by ID."""
        return f"user:id:{user_id}"

    def _email_key(self, email: str) -> str:
        """Generate cache key for user by email."""
        return f"user:email:{email}"

    async def get_by_id(self, user_id: str) -> User | None:
        """Get user by ID with cache-aside pattern.

        1. Check cache for user
        2. If miss, fetch from database
        3. If found, cache for future requests
        """
        # Check cache first
        key = self._user_key(user_id)
        cached = await self.cache.get(key)
        if cached is not None:
            return User.from_dict(cached)

        # Cache miss - fetch from database
        user = await self.delegate.get_by_id(user_id)

        # Cache the result (even None results could be cached with short TTL)
        if user is not None:
            await self.cache.set(key, user.to_dict(), self._ttl)
            await self.cache.set(self._email_key(user.email), user.to_dict(), self._ttl)

        return user

    async def get_by_email(self, email: str) -> User | None:
        """Get user by email with caching."""
        key = self._email_key(email)
        cached = await self.cache.get(key)
        if cached is not None:
            return User.from_dict(cached)

        user = await self.delegate.get_by_email(email)

        if user is not None:
            await self.cache.set(key, user.to_dict(), self._ttl)
            await self.cache.set(self._user_key(user.id), user.to_dict(), self._ttl)

        return user

    async def save(self, user: User) -> None:
        """Save user and invalidate cache.

        Write-through with cache invalidation:
        1. Save to database
        2. Invalidate cached entries
        """
        await self.delegate.save(user)

        # Invalidate cache (could also update cache here for write-through)
        await self.cache.delete(self._user_key(user.id))
        await self.cache.delete(self._email_key(user.email))

    async def delete(self, user_id: str) -> None:
        """Delete user and invalidate cache."""
        # Get user first to know email for cache invalidation
        user = await self.delegate.get_by_id(user_id)

        await self.delegate.delete(user_id)

        # Invalidate cache
        await self.cache.delete(self._user_key(user_id))
        if user:
            await self.cache.delete(self._email_key(user.email))

    async def list_all(self) -> list[User]:
        """List all users (no caching for list operations).

        Note: Caching list operations is more complex and often not worth it
        because the list can become stale quickly.
        """
        return await self.delegate.list_all()
