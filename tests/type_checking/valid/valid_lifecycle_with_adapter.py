"""
Valid lifecycle usage with @adapter.for_() decorator.

This file demonstrates correct lifecycle usage with adapters and should type-check cleanly.
"""

from typing import Protocol

from dioxide import (
    Profile,
    adapter,
    lifecycle,
)


class CachePort(Protocol):
    """Port for cache operations."""

    def get(self, key: str) -> str | None: ...


@adapter.for_(CachePort, profile=Profile.PRODUCTION)
@lifecycle
class RedisAdapter:
    """Production adapter with lifecycle."""

    def __init__(self) -> None:
        self.connected = False

    async def initialize(self) -> None:
        """Connect to Redis."""
        self.connected = True

    async def dispose(self) -> None:
        """Disconnect from Redis."""
        self.connected = False

    def get(self, key: str) -> str | None:
        """Get value from cache."""
        return None if not self.connected else 'value'
