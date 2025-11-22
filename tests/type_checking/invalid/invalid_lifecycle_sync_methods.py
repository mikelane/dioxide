"""
Invalid usage: @lifecycle decorator with synchronous methods instead of async.

This file should FAIL mypy type checking because the methods are not async.
"""

from dioxide import (
    lifecycle,
    service,
)


@service
@lifecycle
class DatabaseWithSyncMethods:
    """Service with sync methods instead of async - should fail mypy."""

    def __init__(self) -> None:
        self.connected = False

    def initialize(self) -> None:
        """Wrong - should be async def."""
        self.connected = True

    def dispose(self) -> None:
        """Wrong - should be async def."""
        self.connected = False


# This should fail type checking
db = DatabaseWithSyncMethods()
