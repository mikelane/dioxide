"""Redis adapter for caching."""

import fnmatch
from typing import Any

from dioxide import Profile, adapter

from ..domain.ports import CachePort


@adapter.for_(CachePort, profile=Profile.PRODUCTION)
class RedisCache:
    """Redis cache adapter (simulated).

    In a real application, this would use aioredis or redis-py.
    """

    def __init__(self) -> None:
        """Initialize simulated Redis."""
        self._cache: dict[str, Any] = {}
        print("  [Redis] Cache initialized")

    async def get(self, key: str) -> Any | None:
        """Get value from Redis (simulated)."""
        value = self._cache.get(key)
        if value is not None:
            print(f"  [Redis] Cache HIT: {key}")
        else:
            print(f"  [Redis] Cache MISS: {key}")
        return value

    async def set(self, key: str, value: Any, ttl_seconds: int = 300) -> None:
        """Set value in Redis with TTL (simulated)."""
        self._cache[key] = value
        print(f"  [Redis] Cache SET: {key} (TTL={ttl_seconds}s)")

    async def delete(self, key: str) -> None:
        """Delete value from Redis (simulated)."""
        if key in self._cache:
            del self._cache[key]
            print(f"  [Redis] Cache DELETE: {key}")

    async def delete_pattern(self, pattern: str) -> None:
        """Delete all keys matching pattern (simulated SCAN + DEL)."""
        keys_to_delete = [k for k in self._cache.keys() if fnmatch.fnmatch(k, pattern)]
        for key in keys_to_delete:
            del self._cache[key]
        print(f"  [Redis] Cache DELETE pattern {pattern}: {len(keys_to_delete)} keys")
