"""
Valid usage of @lifecycle decorator - should PASS mypy.

This file demonstrates correct lifecycle usage and should type-check cleanly.
"""

from dioxide import (
    lifecycle,
    service,
)


@service
@lifecycle
class Database:
    """Service with proper lifecycle methods."""

    def __init__(self) -> None:
        self.connected = False

    async def initialize(self) -> None:
        """Called by container at startup."""
        self.connected = True

    async def dispose(self) -> None:
        """Called by container at shutdown."""
        self.connected = False


# This should type-check correctly
db = Database()
