"""Tests for package scanning functionality in Container.scan()."""

# Imports inside functions are intentional for test isolation

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

        # Assert: Only TEST profile adapters from package_d are registered
        from tests.fixtures.test_package_d import ServicePort

        # Resolve via the port - should get the TEST profile adapter
        test_service = container.resolve(ServicePort)
        assert test_service is not None
        assert test_service.get_name() == 'TestOnlyService'

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


class DescribePackageScanningSecurityValidation:
    """Tests for security validation in package scanning."""

    def it_allows_scanning_when_no_allowed_packages_configured(self) -> None:
        """Allows any package when allowed_packages is None (backward compatible)."""
        # Arrange: Container without allowed_packages restriction
        container = Container(allowed_packages=None)

        # Act & Assert: Can scan any package
        container.scan(package='tests.fixtures.test_package_a')
        from tests.fixtures.test_package_a import ServiceA

        service = container.resolve(ServiceA)
        assert service is not None

    def it_allows_scanning_packages_in_allowed_list(self) -> None:
        """Allows scanning packages that match allowed prefixes."""
        # Arrange: Container with allowed packages
        container = Container(allowed_packages=['tests.fixtures'])

        # Act: Scan allowed package
        container.scan(package='tests.fixtures.test_package_a')

        # Assert: Components registered successfully
        from tests.fixtures.test_package_a import ServiceA

        service = container.resolve(ServiceA)
        assert service is not None

    def it_blocks_scanning_packages_not_in_allowed_list(self) -> None:
        """Raises ValueError when scanning package not in allowed list."""
        # Arrange: Container with restricted allowed packages
        container = Container(allowed_packages=['myapp', 'tests.fixtures'])

        # Act & Assert: Scanning blocked package raises ValueError
        import pytest

        with pytest.raises(ValueError, match='not in allowed_packages list'):
            container.scan(package='os')

    def it_validates_package_prefix_matching(self) -> None:
        """Validates packages using prefix matching."""
        # Arrange: Container with parent package prefix
        container = Container(allowed_packages=['tests'])

        # Act: Scan sub-package (should match prefix)
        container.scan(package='tests.fixtures.test_package_a')

        # Assert: Components registered (prefix matched)
        from tests.fixtures.test_package_a import ServiceA

        service = container.resolve(ServiceA)
        assert service is not None

    def it_prevents_arbitrary_imports_via_package_scanning(self) -> None:
        """Security test: Prevents importing system modules."""
        # Arrange: Container with restricted packages
        container = Container(allowed_packages=['myapp', 'tests'])

        # Act & Assert: Block dangerous imports
        import pytest

        with pytest.raises(ValueError):
            container.scan(package='os')

        with pytest.raises(ValueError):
            container.scan(package='sys')

        with pytest.raises(ValueError):
            container.scan(package='subprocess')


class DescribePackageScanningErrorHandling:
    """Tests for error handling in package scanning."""

    def it_logs_and_skips_modules_that_fail_to_import(self) -> None:
        """Logs import failures and continues scanning."""
        # Arrange: Container
        container = Container()

        # Act: Scan package with a broken module
        # Should log warning but continue and register working components
        # The broken_module.py will fail to import but scan continues
        container.scan(package='tests.fixtures.test_package_with_errors')

        # Assert: Working components still registered despite broken module
        from tests.fixtures.test_package_with_errors import WorkingService

        service = container.resolve(WorkingService)
        assert service is not None

    def it_handles_module_not_found_error_with_clear_message(self) -> None:
        """Converts ModuleNotFoundError to ImportError with clear message."""
        # Arrange
        container = Container()

        # Act & Assert: Clear error message for missing package
        import pytest

        with pytest.raises(ImportError, match="Package 'nonexistent_package' not found"):
            container.scan(package='nonexistent_package')

    def it_allows_scanning_when_package_is_none_with_allowed_packages(self) -> None:
        """Allows scan(package=None) even with allowed_packages configured."""
        # Arrange: Import components first
        import tests.fixtures.test_package_a  # noqa: F401

        # Container with restrictions
        container = Container(allowed_packages=['tests.fixtures'])

        # Act: Scan without package (should not trigger validation)
        container.scan(package=None)

        # Assert: Components registered
        from tests.fixtures.test_package_a import ServiceA

        service = container.resolve(ServiceA)
        assert service is not None

    def it_handles_scanning_single_module_not_package(self) -> None:
        """Handles scanning a module (not a package) correctly."""
        # Arrange
        container = Container()

        # Act: Scan a single module file (has no __path__ attribute)
        # This tests the early return path in _import_package
        container.scan(package='tests.fixtures.test_package_a')

        # Assert: Module imported and components registered
        from tests.fixtures.test_package_a import ServiceA

        service = container.resolve(ServiceA)
        assert service is not None
