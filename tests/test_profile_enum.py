"""Tests for Profile enum (Issue #96).

Tests for the Profile enum that defines standard environment profiles
for hexagonal architecture adapter selection.
"""

from __future__ import annotations

from dioxide import Profile


class DescribeProfileEnum:
    """Tests for Profile enum functionality."""

    def it_defines_standard_production_profile(self) -> None:
        """Profile.PRODUCTION has value 'production'."""
        assert Profile.PRODUCTION.value == 'production'

    def it_defines_standard_test_profile(self) -> None:
        """Profile.TEST has value 'test'."""
        assert Profile.TEST.value == 'test'

    def it_defines_standard_development_profile(self) -> None:
        """Profile.DEVELOPMENT has value 'development'."""
        assert Profile.DEVELOPMENT.value == 'development'

    def it_defines_standard_staging_profile(self) -> None:
        """Profile.STAGING has value 'staging'."""
        assert Profile.STAGING.value == 'staging'

    def it_defines_standard_ci_profile(self) -> None:
        """Profile.CI has value 'ci'."""
        assert Profile.CI.value == 'ci'

    def it_defines_all_profile_with_wildcard(self) -> None:
        """Profile.ALL uses wildcard for universal adapters."""
        assert Profile.ALL.value == '*'

    def it_is_a_string_enum(self) -> None:
        """Profile is a string enum for serialization."""
        assert isinstance(Profile.PRODUCTION, str)
        assert isinstance(Profile.TEST, str)
        assert isinstance(Profile.DEVELOPMENT, str)

    def it_has_exactly_expected_members(self) -> None:
        """Profile enum has exactly the expected members."""
        expected = {'PRODUCTION', 'TEST', 'DEVELOPMENT', 'STAGING', 'CI', 'ALL'}
        actual = {p.name for p in Profile}
        assert actual == expected

    def it_can_be_compared_by_value(self) -> None:
        """Profile members can be compared as strings."""
        # String enum members inherit from str, so direct comparison works at runtime
        # mypy is overly strict here, but runtime behavior is correct
        assert Profile.PRODUCTION == 'production'  # type: ignore
        assert Profile.ALL == '*'  # type: ignore

    def it_can_be_accessed_by_string_value(self) -> None:
        """Profile members can be accessed by their string value."""
        assert Profile('production') == Profile.PRODUCTION
        assert Profile('test') == Profile.TEST
        assert Profile('*') == Profile.ALL
