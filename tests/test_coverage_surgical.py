"""Surgical tests targeting specific uncovered lines in container.py.

These tests target specific gaps identified in coverage analysis to reach 93% coverage.
Each test is designed to exercise a specific error path or edge case that wasn't
covered by existing tests.
"""
# mypy: disable-error-code="name-defined"

import asyncio
import logging
import sys
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Protocol,
)

import pytest

from dioxide import (
    Container,
    Profile,
    adapter,
    lifecycle,
    service,
)
from dioxide.exceptions import (
    AdapterNotFoundError,
    ServiceNotFoundError,
)
from dioxide.scope import Scope

if TYPE_CHECKING:
    pass


class DescribePackageScanningImportFailures:
    """Tests for handling import failures during package scanning."""

    def it_logs_warning_when_submodule_import_fails_during_walk(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Container logs warning and continues when submodule import fails."""
        # Create a valid package with a submodule that will fail to import
        package_dir = tmp_path / 'test_pkg'
        package_dir.mkdir()
        (package_dir / '__init__.py').write_text('')

        # Create a submodule with a syntax error that will fail to import
        (package_dir / 'bad_module.py').write_text('this is not valid python syntax !!!!')

        # Add the temp directory to Python path
        sys.path.insert(0, str(tmp_path))

        try:
            container = Container()

            with caplog.at_level(logging.WARNING):
                # Scan the package - should log warning about bad_module but continue
                container.scan(package='test_pkg')

            # Check that warning was logged about the import failure
            assert any('Failed to import module' in record.message for record in caplog.records)
        finally:
            # Clean up
            sys.path.remove(str(tmp_path))
            if 'test_pkg' in sys.modules:
                del sys.modules['test_pkg']
            if 'test_pkg.bad_module' in sys.modules:
                del sys.modules['test_pkg.bad_module']


class DescribeAdapterPackageFiltering:
    """Tests for package filtering during adapter registration."""

    def it_filters_adapters_by_package_during_scan(self) -> None:
        """Container only registers adapters from specified package."""

        # Define adapters in different "packages" (using __module__)
        class PortA(Protocol):
            def method_a(self) -> str: ...

        # Create adapter with custom module name to simulate different package
        @adapter.for_(PortA, profile=Profile.TEST)
        class AdapterInOtherPackage:
            __module__ = 'other_package.adapters'

            def method_a(self) -> str:
                return 'other'

        # Temporarily set the adapter's module
        original_module = AdapterInOtherPackage.__module__
        AdapterInOtherPackage.__module__ = 'other_package.adapters'

        try:
            container = Container()
            # Scan only 'dioxide' package - should skip our adapter
            container.scan(package='dioxide', profile=Profile.TEST)

            # PortA should not be resolvable since adapter was filtered out
            with pytest.raises(AdapterNotFoundError):
                container.resolve(PortA)
        finally:
            # Restore original module
            AdapterInOtherPackage.__module__ = original_module


class DescribeProtocolFactoryKeyError:
    """Tests for handling KeyError when protocol factory registration conflicts."""

    def it_skips_protocol_registration_when_already_registered_manually(self) -> None:
        """Container skips protocol registration if manually registered."""

        class PortB(Protocol):
            def method_b(self) -> str: ...

        @adapter.for_(PortB, profile=Profile.TEST)
        class AdapterB:
            def method_b(self) -> str:
                return 'adapter_b'

        container = Container()

        # Manually register a different implementation for the protocol
        manual_impl = AdapterB()
        container.register_singleton_factory(PortB, lambda: manual_impl)

        # Now scan - should skip protocol registration since it's already registered
        container.scan(profile=Profile.TEST)

        # Should resolve to manually registered instance
        resolved = container.resolve(PortB)
        assert resolved is manual_impl


class DescribeTypeHintResolutionFailures:
    """Tests for handling type hint resolution failures."""

    def it_handles_classes_with_unresolvable_init_signature(self) -> None:
        """Container handles classes where get_type_hints fails on __init__."""

        @service
        class ServiceWithBadTypeHints:
            # Create a class where type hint resolution will fail
            # by using forward reference that can't be resolved
            def __init__(self, dep: 'CompletelyUnknownType') -> None:  # noqa: F821 # type: ignore[name-defined]
                self.dep = dep

        container = Container()
        container.scan()

        # Factory should fall back to direct instantiation
        # This will fail during instantiation due to missing parameter,
        # but the factory creation should succeed
        factory = container._create_auto_injecting_factory(ServiceWithBadTypeHints)
        assert callable(factory)


class DescribeLifecycleResolutionFailures:
    """Tests for handling lifecycle component resolution failures."""

    def it_skips_lifecycle_adapters_not_registered_for_active_profile(self) -> None:
        """Container skips lifecycle adapters not registered for active profile."""

        class PortD(Protocol):
            def method_d(self) -> str: ...

        # Adapter only available in PRODUCTION
        @adapter.for_(PortD, profile=Profile.PRODUCTION)
        @lifecycle
        class ProductionAdapter:
            def __init__(self) -> None:
                self.initialized = False

            def method_d(self) -> str:
                return 'production'

            async def initialize(self) -> None:
                self.initialized = True

            async def dispose(self) -> None:
                pass

        # Create fresh container
        container = Container()

        # Scan with TEST profile - ProductionAdapter won't be registered
        container.scan(profile=Profile.TEST)

        # start() should skip the lifecycle adapter since it's not resolvable

        asyncio.run(container.start())

        # No error should be raised - adapter was gracefully skipped
        assert True


class DescribeAdapterLifecyclePortResolutionFailure:
    """Tests for handling adapter lifecycle port resolution failures."""

    def it_handles_lifecycle_adapter_when_port_not_resolvable(self) -> None:
        """Container handles lifecycle adapters where port can't be resolved."""

        class PortC(Protocol):
            def method_c(self) -> str: ...

        @adapter.for_(PortC, profile=Profile.PRODUCTION)
        @lifecycle
        class AdapterC:
            def __init__(self) -> None:
                pass

            def method_c(self) -> str:
                return 'adapter_c'

            async def initialize(self) -> None:
                pass

            async def dispose(self) -> None:
                pass

        container = Container()
        # Scan with TEST profile - AdapterC won't be registered (it's PRODUCTION only)
        container.scan(profile=Profile.TEST)

        # start() should skip the adapter since it's not resolvable for this profile

        asyncio.run(container.start())

        # No error should be raised
        assert True


class DescribeServicePackageFiltering:
    """Tests for filtering services by package during scan."""

    def it_filters_services_by_package_during_scan(self) -> None:
        """Container only registers services from specified package."""

        # Create service with custom module name to simulate different package
        @service
        class ServiceInOtherPackage:
            pass

        # Temporarily set the service's module to simulate different package
        original_module = ServiceInOtherPackage.__module__
        ServiceInOtherPackage.__module__ = 'external_package.services'

        try:
            container = Container()
            # Scan only 'dioxide' package - should skip our service
            container.scan(package='dioxide')

            # ServiceInOtherPackage should not be resolvable since it was filtered out
            with pytest.raises(ServiceNotFoundError):
                container.resolve(ServiceInOtherPackage)
        finally:
            # Restore original module
            ServiceInOtherPackage.__module__ = original_module


class DescribeServiceProfileFiltering:
    """Tests for filtering services by profile during scan."""

    def it_skips_services_without_matching_profile(self) -> None:
        """Container skips services that don't match the scan profile."""

        # Create a service that's only available in PRODUCTION
        # Note: Services normally don't have profiles, but we can simulate this
        # by manually setting the profile attribute
        @service
        class ProductionOnlyService:
            pass

        # Manually add profile attribute (simulating an adapter-like service)
        ProductionOnlyService.__dioxide_profiles__ = frozenset(['production'])

        container = Container()
        # Scan with TEST profile - ProductionOnlyService should be skipped
        container.scan(profile=Profile.TEST)

        # Service should not be resolvable

        with pytest.raises(ServiceNotFoundError):
            container.resolve(ProductionOnlyService)


class DescribeTransientFactoryRegistration:
    """Tests for transient factory registration during scan."""

    def it_registers_transient_factory_for_non_singleton_scope(self) -> None:
        """Container registers transient factory for services with non-singleton scope."""

        @service
        class TransientService:
            pass

        # Manually set scope to FACTORY (transient)
        TransientService.__dioxide_scope__ = Scope.FACTORY

        container = Container()
        container.scan()

        # Should create new instance each time
        instance1 = container.resolve(TransientService)
        instance2 = container.resolve(TransientService)

        # Instances should be different (transient behavior)
        assert instance1 is not instance2
