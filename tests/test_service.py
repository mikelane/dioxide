"""Tests for @service decorator.

The @service decorator is used for core domain logic that:
- Is a singleton by default (one shared instance)
- Can use FACTORY scope for fresh instances per resolution
- Available in ALL profiles (doesn't vary by environment)
- Supports constructor-based dependency injection
"""

from dioxide import (
    Container,
    Scope,
    _get_registered_components,
    service,
)


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

        @service
        class TestService:
            pass

        registered = _get_registered_components()
        assert TestService in registered

    def it_creates_singleton_instances(self) -> None:
        """Decorator creates singleton (shared) instances."""

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

        @service
        class OriginalService:
            def method(self) -> str:
                return 'original'

        # Class should work normally
        instance = OriginalService()
        assert instance.method() == 'original'

    def it_supports_classes_with_init(self) -> None:
        """Decorator works with classes that have __init__."""

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

        @service
        class ServiceWithoutInit:
            pass

        container = Container()
        container.scan()

        instance = container.resolve(ServiceWithoutInit)
        assert isinstance(instance, ServiceWithoutInit)


class DescribeServiceScope:
    """Tests for @service decorator scope behavior."""

    def it_defaults_to_singleton_scope(self) -> None:
        """Service without explicit scope defaults to SINGLETON."""

        @service
        class DefaultScopeService:
            pass

        assert hasattr(DefaultScopeService, '__dioxide_scope__')
        assert DefaultScopeService.__dioxide_scope__ == Scope.SINGLETON

    def it_accepts_explicit_singleton_scope(self) -> None:
        """Service can explicitly specify SINGLETON scope."""

        @service(scope=Scope.SINGLETON)
        class ExplicitSingletonService:
            pass

        assert ExplicitSingletonService.__dioxide_scope__ == Scope.SINGLETON

    def it_accepts_factory_scope(self) -> None:
        """Service can specify FACTORY scope for per-resolution instances."""

        @service(scope=Scope.FACTORY)
        class FactoryScopeService:
            pass

        assert FactoryScopeService.__dioxide_scope__ == Scope.FACTORY

    def it_returns_same_instance_for_singleton_scope(self) -> None:
        """SINGLETON scope returns same instance on each resolve."""

        @service(scope=Scope.SINGLETON)
        class SingletonService:
            pass

        container = Container()
        container.scan()

        instance1 = container.resolve(SingletonService)
        instance2 = container.resolve(SingletonService)

        assert instance1 is instance2

    def it_returns_new_instance_for_factory_scope(self) -> None:
        """FACTORY scope returns new instance on each resolve."""

        @service(scope=Scope.FACTORY)
        class FactoryService:
            pass

        container = Container()
        container.scan()

        instance1 = container.resolve(FactoryService)
        instance2 = container.resolve(FactoryService)
        instance3 = container.resolve(FactoryService)

        assert instance1 is not instance2
        assert instance2 is not instance3
        assert instance1 is not instance3

    def it_preserves_factory_instance_independence(self) -> None:
        """FACTORY scope instances have independent state."""

        @service(scope=Scope.FACTORY)
        class StatefulFactoryService:
            instance_count = 0

            def __init__(self) -> None:
                StatefulFactoryService.instance_count += 1
                self.id = StatefulFactoryService.instance_count

        container = Container()
        container.scan()

        instance1 = container.resolve(StatefulFactoryService)
        instance2 = container.resolve(StatefulFactoryService)

        assert instance1.id != instance2.id

    def it_accepts_request_scope(self) -> None:
        """Service can specify REQUEST scope for per-scope instances."""

        @service(scope=Scope.REQUEST)
        class RequestScopeService:
            pass

        assert RequestScopeService.__dioxide_scope__ == Scope.REQUEST
