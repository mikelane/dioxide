"""Tests for Profile class (Issue #96, #311).

Tests for the Profile class that defines standard environment profiles
for hexagonal architecture adapter selection. The Profile class is an
extensible string subclass that provides type safety.
"""

from __future__ import annotations

from dioxide import Profile


class DescribeProfileClass:
    """Tests for Profile class functionality."""

    def it_defines_standard_production_profile(self) -> None:
        """Profile.PRODUCTION equals 'production'."""
        assert Profile.PRODUCTION == 'production'

    def it_defines_standard_test_profile(self) -> None:
        """Profile.TEST equals 'test'."""
        assert Profile.TEST == 'test'

    def it_defines_standard_development_profile(self) -> None:
        """Profile.DEVELOPMENT equals 'development'."""
        assert Profile.DEVELOPMENT == 'development'

    def it_defines_standard_staging_profile(self) -> None:
        """Profile.STAGING equals 'staging'."""
        assert Profile.STAGING == 'staging'

    def it_defines_standard_ci_profile(self) -> None:
        """Profile.CI equals 'ci'."""
        assert Profile.CI == 'ci'

    def it_defines_all_profile_with_wildcard(self) -> None:
        """Profile.ALL uses wildcard for universal adapters."""
        assert Profile.ALL == '*'

    def it_is_a_string_subclass(self) -> None:
        """Profile is a string subclass for compatibility."""
        assert isinstance(Profile.PRODUCTION, str)
        assert isinstance(Profile.TEST, str)
        assert isinstance(Profile.DEVELOPMENT, str)

    def it_has_all_expected_builtin_profiles(self) -> None:
        """Profile class has all expected built-in profiles."""
        expected_profiles = {
            Profile.PRODUCTION: 'production',
            Profile.TEST: 'test',
            Profile.DEVELOPMENT: 'development',
            Profile.STAGING: 'staging',
            Profile.CI: 'ci',
            Profile.ALL: '*',
        }
        for profile, expected_value in expected_profiles.items():
            assert profile == expected_value
            assert isinstance(profile, Profile)

    def it_can_be_compared_by_value(self) -> None:
        """Profile members can be compared as strings."""
        assert Profile.PRODUCTION == 'production'
        assert Profile.ALL == '*'

    def it_can_create_custom_profiles(self) -> None:
        """Custom profiles can be created for extensibility."""
        custom = Profile('integration')
        assert custom == 'integration'
        assert isinstance(custom, Profile)
        assert isinstance(custom, str)
