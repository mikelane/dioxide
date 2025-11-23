"""Test package B - service in main package."""

from dioxide import service


@service
class ServiceB:
    """Service in package B main module."""

    def get_name(self) -> str:
        """Return service name."""
        return 'ServiceB'
