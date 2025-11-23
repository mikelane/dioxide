"""Test package B subpackage - service in nested package."""

from dioxide import service


@service
class ServiceBSub:
    """Service in package B subpackage."""

    def get_name(self) -> str:
        """Return service name."""
        return 'ServiceBSub'
