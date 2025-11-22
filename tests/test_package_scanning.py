"""Tests for package scanning functionality in Container.scan()."""

# ruff: noqa: PLC0415  # Imports inside functions are intentional for test isolation

from dioxide import (
    Container,
)


class DescribePackageScanning:
    """Tests for package parameter in Container.scan()."""

    def it_scans_a_specific_package(self) -> None:
        """Scans and registers components from a specific package."""
        # Arrange: Create container (decorators will register during scan)
        container = Container()

        # Act: Scan only the test_package_a (imports modules automatically)
        container.scan(package='tests.fixtures.test_package_a')

        # Assert: Components from test_package_a are registered
        # Import AFTER scan to get the registered classes
        from tests.fixtures.test_package_a import ServiceA

        service_a = container.resolve(ServiceA)
        assert service_a is not None
        assert isinstance(service_a, ServiceA)

    def it_scans_package_with_subpackages(self) -> None:
        """Scans package including all sub-packages."""
        # Arrange
        container = Container()

        # Act: Scan package with nested subpackages
        container.scan(package='tests.fixtures.test_package_b')

        # Assert: Components from main package and subpackages are registered
        from tests.fixtures.test_package_b import ServiceB
        from tests.fixtures.test_package_b.subpkg import ServiceBSub

        service_b = container.resolve(ServiceB)
        service_b_sub = container.resolve(ServiceBSub)

        assert service_b is not None
        assert service_b_sub is not None

    def it_only_registers_components_from_scanned_package(self) -> None:
        """Only registers components from the specified package."""
        # Arrange
        container = Container()

        # Act: Scan only test_package_a (will import and filter components)
        container.scan(package='tests.fixtures.test_package_a')

        # Assert: test_package_a components are registered
        from tests.fixtures.test_package_a import ServiceA

        service_a = container.resolve(ServiceA)
        assert service_a is not None

        # Assert: test_package_c components are NOT registered
        # Import ServiceC but don't expect it to be in container
        import pytest

        from dioxide.exceptions import ServiceNotFoundError
        from tests.fixtures.test_package_c import ServiceC

        with pytest.raises(ServiceNotFoundError):
            container.resolve(ServiceC)

    def it_handles_invalid_package_name(self) -> None:
        """Raises ImportError for invalid package names."""
        # Arrange
        container = Container()

        # Act & Assert: Invalid package name raises ImportError
        import pytest

        with pytest.raises(ImportError):
            container.scan(package='nonexistent.invalid.package')

    def it_combines_package_and_profile_filtering(self) -> None:
        """Applies both package and profile filters together."""
        # Arrange
        container = Container()

        # Act: Scan specific package with profile filter
        from dioxide import Profile

        container.scan(package='tests.fixtures.test_package_d', profile=Profile.TEST)

        # Assert: Only TEST profile components from package_d are registered
        from tests.fixtures.test_package_d import (
            ProductionOnlyService,
            TestOnlyService,
        )

        test_service = container.resolve(TestOnlyService)
        assert test_service is not None

        # Production-only service should NOT be registered
        import pytest

        from dioxide.exceptions import ServiceNotFoundError

        with pytest.raises(ServiceNotFoundError):
            container.resolve(ProductionOnlyService)

    def it_scans_all_packages_when_package_is_none(self) -> None:
        """Scans all registered components when package=None."""
        # Arrange
        container = Container()

        # Import packages explicitly to register decorators
        import tests.fixtures.test_package_a
        import tests.fixtures.test_package_c  # noqa: F401

        # Act: Scan without package parameter (scans all registered components)
        container.scan(package=None)

        # Assert: Components from all imported packages are registered
        from tests.fixtures.test_package_a import ServiceA
        from tests.fixtures.test_package_c import ServiceC

        service_a = container.resolve(ServiceA)
        service_c = container.resolve(ServiceC)

        assert service_a is not None
        assert service_c is not None
