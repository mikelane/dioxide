"""Tests for @service decorator.

The @service decorator is used for core domain logic that:
- Is a singleton (one shared instance)
- Available in ALL profiles (doesn't vary by environment)
- Supports constructor-based dependency injection
"""

from dioxide import Container, _clear_registry, _get_registered_components, service


class DescribeServiceDecorator:
    """Tests for @service decorator functionality."""

    def it_can_be_applied_to_classes(self) -> None:
        """Decorator can be applied to classes."""

        @service
        class SimpleService:
            pass

        assert SimpleService is not None

    def it_registers_class_globally(self) -> None:
        """Decorator adds class to global registry."""
        _clear_registry()

        @service
        class TestService:
            pass

        registered = _get_registered_components()
        assert TestService in registered

    def it_creates_singleton_instances(self) -> None:
        """Decorator creates singleton (shared) instances."""
        _clear_registry()

        @service
        class SingletonService:
            pass

        container = Container()
        container.scan()

        instance1 = container.resolve(SingletonService)
        instance2 = container.resolve(SingletonService)

        assert instance1 is instance2

    def it_supports_dependency_injection(self) -> None:
        """Decorator supports constructor injection."""
        _clear_registry()

        @service
        class DependencyService:
            pass

        @service
        class MainService:
            def __init__(self, dep: DependencyService):
                self.dep = dep

        container = Container()
        container.scan()

        main = container.resolve(MainService)
        assert isinstance(main.dep, DependencyService)

    def it_preserves_the_original_class(self) -> None:
        """Decorator returns the original class unchanged."""
        _clear_registry()

        @service
        class OriginalService:
            def method(self) -> str:
                return 'original'

        # Class should work normally
        instance = OriginalService()
        assert instance.method() == 'original'

    def it_supports_classes_with_init(self) -> None:
        """Decorator works with classes that have __init__."""
        _clear_registry()

        @service
        class ServiceWithInit:
            def __init__(self) -> None:
                self.initialized = True

        container = Container()
        container.scan()

        instance = container.resolve(ServiceWithInit)
        assert instance.initialized is True

    def it_supports_classes_without_init(self) -> None:
        """Decorator works with classes without __init__."""
        _clear_registry()

        @service
        class ServiceWithoutInit:
            pass

        container = Container()
        container.scan()

        instance = container.resolve(ServiceWithoutInit)
        assert isinstance(instance, ServiceWithoutInit)
