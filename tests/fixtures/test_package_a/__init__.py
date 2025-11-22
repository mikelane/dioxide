"""Test package A - simple service."""

from dioxide import service


@service
class ServiceA:
    """Simple service in package A."""

    def get_name(self) -> str:
        """Return service name."""
        return 'ServiceA'
