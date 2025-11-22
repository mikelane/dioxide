"""Test package D - profile-specific components."""

from dioxide import (
    Profile,
    component,
)
from dioxide.profile import profile


@component
@profile(Profile.TEST)
class TestOnlyService:
    """Component only available in TEST profile."""

    def get_name(self) -> str:
        """Return component name."""
        return 'TestOnlyService'


@component
@profile(Profile.PRODUCTION)
class ProductionOnlyService:
    """Component only available in PRODUCTION profile."""

    def get_name(self) -> str:
        """Return component name."""
        return 'ProductionOnlyService'
