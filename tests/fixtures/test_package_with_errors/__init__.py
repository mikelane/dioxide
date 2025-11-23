"""Test package with intentionally broken module."""

from dioxide import service


@service
class WorkingService:
    """A working service."""

    pass
