"""Test package with intentionally broken module."""

from dioxide import component


@component
class WorkingService:
    """A working service."""

    pass
