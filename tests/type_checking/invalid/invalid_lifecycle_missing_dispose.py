"""
Invalid usage: @lifecycle decorator with missing dispose() method.

This file should FAIL mypy type checking because the class is missing
the required dispose() method.
"""

from dioxide import (
    lifecycle,
    service,
)


@service
@lifecycle
class DatabaseMissingDispose:
    """Service missing dispose() method - should fail mypy."""

    def __init__(self) -> None:
        self.connected = False

    async def initialize(self) -> None:
        """Has initialize but missing dispose."""
        self.connected = True


# This should fail type checking
db = DatabaseMissingDispose()
