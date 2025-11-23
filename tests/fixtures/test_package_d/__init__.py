"""Test package D - profile-specific adapters."""

from typing import Protocol

from dioxide import (
    Profile,
    adapter,
)


class ServicePort(Protocol):
    """Protocol for test service."""

    def get_name(self) -> str:
        """Return component name."""
        ...


@adapter.for_(ServicePort, profile=Profile.TEST)
class TestOnlyService:
    """Adapter only available in TEST profile."""

    def get_name(self) -> str:
        """Return component name."""
        return 'TestOnlyService'


@adapter.for_(ServicePort, profile=Profile.PRODUCTION)
class ProductionOnlyService:
    """Adapter only available in PRODUCTION profile."""

    def get_name(self) -> str:
        """Return component name."""
        return 'ProductionOnlyService'
