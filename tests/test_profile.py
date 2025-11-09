"""Tests for @profile decorator system (Issue #68)."""

from __future__ import annotations

import pytest

from dioxide import profile


class DescribeProfileDecorator:
    """Tests for @profile decorator functionality."""

    def it_supports_predefined_production_profile(self) -> None:
        """@profile.production adds 'production' to __dioxide_profiles__."""

        @profile.production
        class ProductionService:
            pass

        assert hasattr(ProductionService, '__dioxide_profiles__')
        assert 'production' in ProductionService.__dioxide_profiles__

    def it_supports_predefined_test_profile(self) -> None:
        """@profile.test adds 'test' to __dioxide_profiles__."""

        @profile.test
        class TestService:
            pass

        assert hasattr(TestService, '__dioxide_profiles__')
        assert 'test' in TestService.__dioxide_profiles__

    def it_supports_predefined_development_profile(self) -> None:
        """@profile.development adds 'development' to __dioxide_profiles__."""

        @profile.development
        class DevelopmentService:
            pass

        assert hasattr(DevelopmentService, '__dioxide_profiles__')
        assert 'development' in DevelopmentService.__dioxide_profiles__

    def it_supports_custom_profiles_via_getattr(self) -> None:
        """@profile.staging (custom) adds 'staging' to __dioxide_profiles__."""

        @profile.staging
        class StagingService:
            pass

        assert hasattr(StagingService, '__dioxide_profiles__')
        assert 'staging' in StagingService.__dioxide_profiles__

    def it_supports_multiple_profiles_via_callable(self) -> None:
        """@profile("prod", "staging") adds both profiles."""

        @profile('prod', 'staging')
        class SharedService:
            pass

        assert hasattr(SharedService, '__dioxide_profiles__')
        assert 'prod' in SharedService.__dioxide_profiles__
        assert 'staging' in SharedService.__dioxide_profiles__

    def it_supports_single_profile_via_callable(self) -> None:
        """@profile("custom") adds single custom profile."""

        @profile('custom')
        class CustomService:
            pass

        assert hasattr(CustomService, '__dioxide_profiles__')
        assert 'custom' in CustomService.__dioxide_profiles__

    def it_preserves_class_identity(self) -> None:
        """Decorator returns the same class, not a wrapper."""

        @profile.production
        class OriginalService:
            """Original docstring."""

            value = 42

        assert OriginalService.__name__ == 'OriginalService'
        assert OriginalService.__doc__ == 'Original docstring.'
        assert OriginalService.value == 42

    def it_allows_stacking_profiles(self) -> None:
        """Multiple @profile decorators combine profiles."""

        @profile.production
        @profile.test
        class MultiProfileService:
            pass

        assert 'production' in MultiProfileService.__dioxide_profiles__
        assert 'test' in MultiProfileService.__dioxide_profiles__

    def it_stores_profiles_as_frozenset(self) -> None:
        """Profiles stored as immutable frozenset."""

        @profile.production
        class ImmutableService:
            pass

        assert isinstance(ImmutableService.__dioxide_profiles__, frozenset)

    def it_creates_unique_profile_attribute_per_class(self) -> None:
        """Each decorated class gets its own profile set."""

        @profile.production
        class Service1:
            pass

        @profile.test
        class Service2:
            pass

        assert 'production' in Service1.__dioxide_profiles__
        assert 'production' not in Service2.__dioxide_profiles__
        assert 'test' in Service2.__dioxide_profiles__
        assert 'test' not in Service1.__dioxide_profiles__


class DescribeProfileDecoratorEdgeCases:
    """Edge cases and error handling for @profile decorator."""

    def it_handles_bare_profile_decorator_as_production(self) -> None:
        """@profile (bare, no parens) defaults to production profile."""
        # Note: This is an edge case - normal usage is @profile.production
        # But if someone uses bare @profile, it should work gracefully

        @profile
        class BareProfileService:
            pass

        assert hasattr(BareProfileService, '__dioxide_profiles__')
        assert 'production' in BareProfileService.__dioxide_profiles__

    def it_raises_error_for_empty_profile_list(self) -> None:
        """@profile() with no arguments raises ValueError."""
        with pytest.raises(ValueError, match='At least one profile name required'):

            @profile()
            class EmptyProfileService:
                pass

    def it_raises_error_for_non_string_profile_name(self) -> None:
        """@profile(123) with non-string raises TypeError."""
        with pytest.raises(TypeError, match='Profile names must be strings'):

            @profile(123)  # type: ignore[call-overload]
            class InvalidProfileService:
                pass

    def it_raises_error_for_empty_string_profile(self) -> None:
        """@profile("") with empty string raises ValueError."""
        with pytest.raises(ValueError, match='Profile names cannot be empty'):

            @profile('')
            class EmptyStringProfileService:
                pass

    def it_normalizes_profile_names_to_lowercase(self) -> None:
        """Profile names are normalized to lowercase."""

        @profile('PRODUCTION')
        class UpperCaseService:
            pass

        assert 'production' in UpperCaseService.__dioxide_profiles__
        assert 'PRODUCTION' not in UpperCaseService.__dioxide_profiles__

    def it_deduplicates_profile_names(self) -> None:
        """Duplicate profile names are deduplicated."""

        @profile('prod', 'staging', 'prod')
        class DuplicateService:
            pass

        profile_list = list(DuplicateService.__dioxide_profiles__)
        assert profile_list.count('prod') == 1
        assert 'staging' in DuplicateService.__dioxide_profiles__


class DescribeProfileDecoratorWithComponent:
    """Tests for @profile working alongside @component decorator."""

    def it_works_with_component_decorator(self) -> None:
        """@profile and @component can be stacked."""
        from dioxide import component

        @component
        @profile.production
        class ComponentWithProfile:
            pass

        assert hasattr(ComponentWithProfile, '__dioxide_profiles__')
        assert 'production' in ComponentWithProfile.__dioxide_profiles__
        # Component decorator behavior tested in test_component.py
