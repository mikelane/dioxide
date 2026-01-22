"""Redis adapter for production caching.

In a real application, this would use aioredis or redis-py async.
This example simulates the behavior for demonstration purposes.
"""

from typing import Any

from dioxide import Profile, adapter

from ..domain.ports import CachePort


@adapter.for_(CachePort, profile=Profile.PRODUCTION)
class RedisCache:
    """Production cache using Redis.

    In a real implementation, this would:
    - Use aioredis or redis-py with async support
    - Have connection pooling
    - Handle TTL properly with Redis SETEX
    """

    def __init__(self) -> None:
        """Initialize simulated Redis connection."""
        self._cache: dict[str, Any] = {}
        print("  [Redis] Cache initialized")

    async def get(self, key: str) -> Any | None:
        """Get a value from Redis."""
        value = self._cache.get(key)
        if value is not None:
            print(f"  [Redis] Cache HIT for {key}")
        else:
            print(f"  [Redis] Cache MISS for {key}")
        return value

    async def set(self, key: str, value: Any, ttl_seconds: int = 300) -> None:
        """Set a value in Redis with TTL."""
        self._cache[key] = value
        print(f"  [Redis] Cached {key} with TTL={ttl_seconds}s")

    async def delete(self, key: str) -> None:
        """Delete a value from Redis."""
        if key in self._cache:
            del self._cache[key]
            print(f"  [Redis] Deleted {key}")
