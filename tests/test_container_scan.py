"""Tests for container.scan() with package and profile parameters (Issue #69)."""

from __future__ import annotations

import pytest

from dioxide import Container, Scope, component, profile
from dioxide.decorators import _clear_registry


class DescribeContainerScanWithPackageParameter:
    """Tests for container.scan(package) - scanning specific packages."""

    def setup_method(self) -> None:
        """Clear component registry before each test."""
        _clear_registry()

    def it_scans_all_components_when_package_is_none(self) -> None:
        """scan() with no package parameter scans all registered components."""

        @component
        class ServiceA:
            pass

        @component
        class ServiceB:
            pass

        container = Container()
        container.scan()

        assert len(container) == 2
        assert container.resolve(ServiceA) is not None
        assert container.resolve(ServiceB) is not None


class DescribeContainerScanWithProfileParameter:
    """Tests for container.scan(profile=...) - profile-based filtering."""

    def setup_method(self) -> None:
        """Clear component registry before each test."""
        _clear_registry()

    def it_scans_all_components_when_profile_is_none(self) -> None:
        """scan() with no profile parameter scans all components regardless of profile."""

        @component
        @profile.production
        class ProdService:
            pass

        @component
        @profile.test
        class TestService:
            pass

        @component
        class NoProfileService:
            pass

        container = Container()
        container.scan()

        # All components registered regardless of profile
        assert len(container) == 3

    def it_filters_components_by_production_profile(self) -> None:
        """scan(profile='production') only registers components with production profile."""

        @component
        @profile.production
        class ProdService:
            pass

        @component
        @profile.test
        class TestService:
            pass

        @component
        class NoProfileService:
            pass

        container = Container()
        container.scan(profile='production')

        # Only production components registered
        assert len(container) == 1
        assert container.resolve(ProdService) is not None

    def it_filters_components_by_test_profile(self) -> None:
        """scan(profile='test') only registers components with test profile."""

        @component
        @profile.production
        class ProdService:
            pass

        @component
        @profile.test
        class TestService:
            pass

        container = Container()
        container.scan(profile='test')

        # Only test components registered
        assert len(container) == 1
        assert container.resolve(TestService) is not None

    def it_normalizes_profile_parameter_to_lowercase(self) -> None:
        """scan(profile='PRODUCTION') normalizes to lowercase for matching."""

        @component
        @profile.production
        class ProdService:
            pass

        container = Container()
        container.scan(profile='PRODUCTION')

        # Should match despite case difference
        assert len(container) == 1
        assert container.resolve(ProdService) is not None

    def it_handles_components_with_multiple_profiles(self) -> None:
        """Components with multiple profiles match any of them."""

        @component
        @profile('production', 'staging')
        class SharedService:
            pass

        @component
        @profile.production
        class ProdOnlyService:
            pass

        container_prod = Container()
        container_prod.scan(profile='production')

        # Both services have production profile
        assert len(container_prod) == 2

        container_staging = Container()
        container_staging.scan(profile='staging')

        # Only SharedService has staging profile
        assert len(container_staging) == 1
        assert container_staging.resolve(SharedService) is not None

    def it_registers_zero_components_when_profile_matches_none(self) -> None:
        """scan(profile='nonexistent') registers no components."""

        @component
        @profile.production
        class ProdService:
            pass

        container = Container()
        container.scan(profile='nonexistent')

        # No components match
        assert len(container) == 0


class DescribeContainerScanBackwardCompatibility:
    """Tests ensuring backward compatibility with existing scan() behavior."""

    def setup_method(self) -> None:
        """Clear component registry before each test."""
        _clear_registry()

    def it_maintains_backward_compatibility_with_no_parameters(self) -> None:
        """scan() with no parameters works as before (scans all components)."""

        @component
        class ServiceA:
            pass

        @component
        @profile.production
        class ServiceB:
            pass

        container = Container()
        container.scan()

        # All components registered (backward compatible behavior)
        assert len(container) == 2
        assert container.resolve(ServiceA) is not None
        assert container.resolve(ServiceB) is not None

    def it_respects_scope_metadata_with_profile_filtering(self) -> None:
        """Profile filtering respects SINGLETON vs FACTORY scope."""

        @component(scope=Scope.SINGLETON)
        @profile.production
        class SingletonService:
            pass

        @component(scope=Scope.FACTORY)
        @profile.production
        class FactoryService:
            pass

        container = Container()
        container.scan(profile='production')

        # Both registered
        assert len(container) == 2

        # Singleton returns same instance
        s1 = container.resolve(SingletonService)
        s2 = container.resolve(SingletonService)
        assert s1 is s2

        # Factory returns different instances
        f1 = container.resolve(FactoryService)
        f2 = container.resolve(FactoryService)
        assert f1 is not f2


class DescribeContainerScanCombinedParameters:
    """Tests for scan(package, profile) with both parameters."""

    def setup_method(self) -> None:
        """Clear component registry before each test."""
        _clear_registry()

    def it_applies_both_package_and_profile_filters(self) -> None:
        """scan('pkg', profile='prod') filters by both package and profile."""
        # This test will pass once package scanning is implemented
        # For now, we'll focus on profile filtering
        pytest.skip('Package scanning not yet implemented')
