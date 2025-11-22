"""
Invalid usage: @lifecycle decorator with missing initialize() method.

This file should FAIL mypy type checking because the class is missing
the required initialize() method.
"""

from dioxide import (
    lifecycle,
    service,
)


@service
@lifecycle
class DatabaseMissingInitialize:
    """Service missing initialize() method - should fail mypy."""

    def __init__(self) -> None:
        self.connected = False

    async def dispose(self) -> None:
        """Has dispose but missing initialize."""
        self.connected = False


# This should fail type checking
db = DatabaseMissingInitialize()
