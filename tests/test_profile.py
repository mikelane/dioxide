"""Tests for extensible Profile class (Issue #311).

Tests for the Profile class which provides type-safe, extensible
profile identifiers for adapter selection.
"""

from __future__ import annotations

from dioxide import Profile


class DescribeProfile:
    """Extensible, type-safe Profile class."""

    class DescribeBuiltInProfiles:
        """Built-in profile constants."""

        def it_has_production_profile(self) -> None:
            """Profile.PRODUCTION is available."""
            assert Profile.PRODUCTION == 'production'

        def it_has_test_profile(self) -> None:
            """Profile.TEST is available."""
            assert Profile.TEST == 'test'

        def it_has_development_profile(self) -> None:
            """Profile.DEVELOPMENT is available."""
            assert Profile.DEVELOPMENT == 'development'

        def it_has_staging_profile(self) -> None:
            """Profile.STAGING is available."""
            assert Profile.STAGING == 'staging'

        def it_has_ci_profile(self) -> None:
            """Profile.CI is available."""
            assert Profile.CI == 'ci'

        def it_has_all_profile(self) -> None:
            """Profile.ALL is available and equals '*'."""
            assert Profile.ALL == '*'

    class DescribeStringSubclass:
        """Profile is a str subclass for compatibility."""

        def it_is_instance_of_str(self) -> None:
            """Profile instances are strings."""
            assert isinstance(Profile.PRODUCTION, str)
            assert isinstance(Profile('custom'), str)

        def it_works_in_string_operations(self) -> None:
            """Profile works like a regular string."""
            assert 'prod' in Profile.PRODUCTION
            assert Profile.PRODUCTION.startswith('prod')
            assert Profile.TEST.upper() == 'TEST'

        def it_can_be_used_in_sets(self) -> None:
            """Profile can be used in set operations."""
            profiles = {Profile.TEST, Profile.DEVELOPMENT}
            assert 'test' in profiles
            assert 'development' in profiles

    class DescribeCustomProfiles:
        """Custom user-defined profiles."""

        def it_creates_custom_profile(self) -> None:
            """Users can create custom profiles."""
            custom = Profile('integration')
            assert custom == 'integration'
            assert isinstance(custom, Profile)

        def it_lowercases_custom_profiles(self) -> None:
            """Custom profiles are normalized to lowercase."""
            custom = Profile('INTEGRATION')
            assert custom == 'integration'

        def it_preserves_type_for_custom_profiles(self) -> None:
            """Custom profiles are Profile instances."""
            custom = Profile('load-test')
            assert type(custom) is Profile

    class DescribeTypeSafety:
        """Type safety features."""

        def it_is_instance_of_profile(self) -> None:
            """Built-in profiles are Profile instances."""
            assert isinstance(Profile.PRODUCTION, Profile)
            assert isinstance(Profile.TEST, Profile)
            assert isinstance(Profile.ALL, Profile)

        def it_can_be_type_checked(self) -> None:
            """Profile type can be used in type hints."""

            def accepts_profile(p: Profile) -> str:
                return str(p)

            # These should work at runtime (type checker validates statically)
            assert accepts_profile(Profile.PRODUCTION) == 'production'
            assert accepts_profile(Profile('custom')) == 'custom'

    class DescribeRepr:
        """String representation."""

        def it_has_informative_repr(self) -> None:
            """repr shows it's a Profile."""
            assert repr(Profile.PRODUCTION) == "Profile('production')"
            assert repr(Profile('custom')) == "Profile('custom')"

        def it_has_value_as_str(self) -> None:
            """str returns the profile value."""
            assert str(Profile.PRODUCTION) == 'production'
            assert str(Profile('custom')) == 'custom'

    class DescribeEquality:
        """Equality comparisons."""

        def it_equals_equivalent_string(self) -> None:
            """Profile equals its string value."""
            assert Profile.PRODUCTION == 'production'
            assert Profile.TEST == 'test'
            assert Profile('custom') == 'custom'

        def it_equals_equivalent_profile(self) -> None:
            """Profile equals another Profile with same value."""
            assert Profile.PRODUCTION == Profile('production')
            assert Profile('custom') == Profile('custom')

        def it_is_hashable(self) -> None:
            """Profile can be used as dict key."""
            mapping: dict[str, str] = {Profile.PRODUCTION: 'prod', Profile.TEST: 'test'}
            assert mapping[Profile.PRODUCTION] == 'prod'
            assert mapping['production'] == 'prod'  # String key works since Profile is str subclass
