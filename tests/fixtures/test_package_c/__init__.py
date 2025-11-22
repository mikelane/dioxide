"""Test package C - another simple service."""

from dioxide import service


@service
class ServiceC:
    """Simple service in package C."""

    def get_name(self) -> str:
        """Return service name."""
        return 'ServiceC'
