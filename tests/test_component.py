"""Tests for @component decorator and auto-discovery."""

from dioxide import (
    Container,
    Profile,
    Scope,
    _get_registered_components,
    component,
    profile,
)


class DescribeComponentDecorator:
    """Tests for @component decorator functionality."""

    def it_can_be_applied_to_a_class(self) -> None:
        """Decorator can be applied to class definitions."""

        @component
        class SimpleService:
            pass

        service = SimpleService()
        assert service is not None

    def it_registers_the_decorated_class(self) -> None:
        """Decorator adds class to global registry."""

        @component
        class UserService:
            pass

        registered = _get_registered_components()
        assert UserService in registered

    def it_can_be_applied_with_parentheses(self) -> None:
        """Decorator can be applied with parentheses and scope argument."""

        @component()
        class DefaultScopeService:
            pass

        @component(scope=Scope.FACTORY)
        class FactoryService:
            pass

        registered = _get_registered_components()
        assert DefaultScopeService in registered
        assert FactoryService in registered


class DescribeScan:
    """Tests for Container.scan() auto-discovery."""

    def it_registers_all_component_classes(self) -> None:
        """Scan finds and registers all @component decorated classes."""

        @component
        class ServiceA:
            pass

        @component
        class ServiceB:
            pass

        container = Container()
        container.scan()

        service_a = container.resolve(ServiceA)
        service_b = container.resolve(ServiceB)

        assert isinstance(service_a, ServiceA)
        assert isinstance(service_b, ServiceB)

    def it_auto_injects_dependencies_from_type_hints(self) -> None:
        """Scan resolves dependencies based on type hints."""

        @component
        class UserService:
            pass

        @component
        class UserController:
            def __init__(self, user_service: UserService):
                self.user_service = user_service

        container = Container()
        container.scan()

        controller = container.resolve(UserController)

        assert isinstance(controller, UserController)
        assert isinstance(controller.user_service, UserService)

    def it_returns_same_instance_for_singleton_scope(self) -> None:
        """Components use singleton scope by default."""

        @component
        class UserService:
            pass

        container = Container()
        container.scan()

        service1 = container.resolve(UserService)
        service2 = container.resolve(UserService)

        assert service1 is service2

    def it_matches_the_developer_experience_example(self) -> None:
        """Integration test matching exact example from DEVELOPER_EXPERIENCE.md."""

        @component
        class UserService:
            pass

        @component
        class UserController:
            def __init__(self, user_service: UserService):
                self.user_service = user_service

        container = Container()
        container.scan()  # Auto-discovers @component classes
        controller = container.resolve(UserController)  # UserService auto-injected!

        # Verify it works as documented
        assert isinstance(controller, UserController)
        assert isinstance(controller.user_service, UserService)

        # Verify singleton behavior
        assert controller.user_service is container.resolve(UserService)

    def it_handles_components_without_init_parameters(self) -> None:
        """Components without __init__ parameters are registered correctly."""

        @component
        class SimpleService:
            value = 'simple'

        container = Container()
        container.scan()

        service = container.resolve(SimpleService)
        assert isinstance(service, SimpleService)
        assert service.value == 'simple'

    def it_handles_components_without_type_hints(self) -> None:
        """Components with __init__ but no type hints are registered."""

        @component
        class LegacyService:
            def __init__(self) -> None:
                self.value = 'legacy'

        container = Container()
        container.scan()

        service = container.resolve(LegacyService)
        assert isinstance(service, LegacyService)
        assert service.value == 'legacy'

    def it_handles_components_with_mixed_type_hints(self) -> None:
        """Components with some parameters lacking type hints skip those parameters."""

        @component
        class DependencyService:
            pass

        @component
        class MixedService:
            def __init__(self, typed: DependencyService, untyped=None) -> None:  # type: ignore[no-untyped-def]
                self.typed = typed
                self.untyped = untyped

        container = Container()
        container.scan()

        service = container.resolve(MixedService)
        assert isinstance(service, MixedService)
        assert isinstance(service.typed, DependencyService)
        assert service.untyped is None  # Not injected since no type hint

    def it_creates_new_instances_for_factory_scope(self) -> None:
        """Components with factory scope create new instances each time."""

        @component(scope=Scope.FACTORY)
        class FactoryService:
            pass

        container = Container()
        container.scan()

        service1 = container.resolve(FactoryService)
        service2 = container.resolve(FactoryService)

        # Different instances for factory scope
        assert service1 is not service2


class DescribeComponentFactorySyntax:
    """Tests for @component.factory attribute syntax (MLP API)."""

    def it_supports_factory_attribute_syntax(self) -> None:
        """@component.factory creates components with factory scope."""

        @component.factory
        class RequestHandler:
            pass

        container = Container()
        container.scan()

        handler1 = container.resolve(RequestHandler)
        handler2 = container.resolve(RequestHandler)

        # Factory scope creates new instances
        assert handler1 is not handler2

    def it_registers_factory_components_in_global_registry(self) -> None:
        """@component.factory adds class to global registry."""

        @component.factory
        class FactoryService:
            pass

        registered = _get_registered_components()
        assert FactoryService in registered

    def it_sets_factory_scope_metadata_on_decorated_class(self) -> None:
        """@component.factory sets __dioxide_scope__ to FACTORY."""

        @component.factory
        class FactoryService:
            pass

        assert hasattr(FactoryService, '__dioxide_scope__')
        assert FactoryService.__dioxide_scope__ == Scope.FACTORY

    def it_supports_dependency_injection_with_factory_scope(self) -> None:
        """@component.factory components can have dependencies injected."""

        @component
        class Database:
            pass

        @component.factory
        class RequestHandler:
            def __init__(self, db: Database):
                self.db = db

        container = Container()
        container.scan()

        handler1 = container.resolve(RequestHandler)
        handler2 = container.resolve(RequestHandler)

        # Factory creates new handlers
        assert handler1 is not handler2
        # But singleton dependency is shared
        assert handler1.db is handler2.db

    def it_maintains_backward_compatibility_with_scope_parameter(self) -> None:
        """Old @component(scope=Scope.FACTORY) still works alongside new syntax."""

        @component(scope=Scope.FACTORY)
        class OldSyntax:
            pass

        @component.factory
        class NewSyntax:
            pass

        container = Container()
        container.scan()

        old1 = container.resolve(OldSyntax)
        old2 = container.resolve(OldSyntax)
        new1 = container.resolve(NewSyntax)
        new2 = container.resolve(NewSyntax)

        # Both syntaxes create factory-scoped components
        assert old1 is not old2
        assert new1 is not new2


class DescribeContainerBasicOperations:
    """Tests for Container basic operations."""

    def it_registers_instances_directly(self) -> None:
        """Container can register pre-created instances."""
        container = Container()

        class Config:
            def __init__(self) -> None:
                self.value = 'test-config'

        config_instance = Config()
        container.register_instance(Config, config_instance)

        resolved = container.resolve(Config)
        assert resolved is config_instance
        assert resolved.value == 'test-config'

    def it_registers_classes_directly(self) -> None:
        """Container can register classes for instantiation."""
        container = Container()

        class Service:
            def __init__(self) -> None:
                self.created = True

        container.register_class(Service, Service)

        resolved = container.resolve(Service)
        assert isinstance(resolved, Service)
        assert resolved.created is True

    def it_reports_empty_state_correctly(self) -> None:
        """Container correctly reports when empty or populated."""
        container = Container()
        assert container.is_empty() is True
        assert len(container) == 0

        class Service:
            pass

        container.register_class(Service, Service)
        assert container.is_empty() is False
        assert len(container) == 1


class DescribeProfileFiltering:
    """Tests for container.scan() profile filtering."""

    def it_accepts_profile_enum_production(self) -> None:
        """Container.scan() accepts Profile.PRODUCTION enum value."""

        @component
        @profile.production
        class ProductionService:
            pass

        @component
        @profile.test
        class TestService:
            pass

        container = Container()
        container.scan(profile=Profile.PRODUCTION)

        # Production service should be registered
        prod_service = container.resolve(ProductionService)
        assert isinstance(prod_service, ProductionService)

        # Test service should NOT be registered
        try:
            container.resolve(TestService)
            raise AssertionError('TestService should not be registered in PRODUCTION profile')
        except KeyError:
            pass  # Expected - test service not in production profile

    def it_accepts_profile_enum_test(self) -> None:
        """Container.scan() accepts Profile.TEST enum value."""

        @component
        @profile.production
        class ProductionService:
            pass

        @component
        @profile.test
        class TestService:
            pass

        container = Container()
        container.scan(profile=Profile.TEST)

        # Test service should be registered
        test_service = container.resolve(TestService)
        assert isinstance(test_service, TestService)

        # Production service should NOT be registered
        try:
            container.resolve(ProductionService)
            raise AssertionError('ProductionService should not be registered in TEST profile')
        except KeyError:
            pass  # Expected - production service not in test profile

    def it_accepts_string_profile_value(self) -> None:
        """Container.scan() accepts string profile values."""

        @component
        @profile.production
        class ProductionService:
            pass

        @component
        @profile.test
        class TestService:
            pass

        container = Container()
        container.scan(profile='production')

        # Production service should be registered
        prod_service = container.resolve(ProductionService)
        assert isinstance(prod_service, ProductionService)

        # Test service should NOT be registered
        try:
            container.resolve(TestService)
            raise AssertionError('TestService should not be registered with production profile')
        except KeyError:
            pass  # Expected

    def it_handles_profile_all_with_enum(self) -> None:
        """Components with Profile.ALL are available in all profiles."""

        @component
        @profile('*')  # Profile.ALL
        class UniversalService:
            pass

        @component
        @profile.production
        class ProductionService:
            pass

        # Scan with PRODUCTION profile
        container = Container()
        container.scan(profile=Profile.PRODUCTION)

        # Universal service should be registered in PRODUCTION
        universal = container.resolve(UniversalService)
        assert isinstance(universal, UniversalService)

        # Production service should also be registered
        prod = container.resolve(ProductionService)
        assert isinstance(prod, prod.__class__)

        # Scan with TEST profile

        @component
        @profile('*')
        class UniversalService2:
            pass

        test_container = Container()
        test_container.scan(profile=Profile.TEST)

        # Universal service should be registered in TEST too
        universal2 = test_container.resolve(UniversalService2)
        assert isinstance(universal2, UniversalService2)

    def it_maintains_backward_compatibility_without_profile(self) -> None:
        """Container.scan() without profile parameter registers all components."""

        @component
        @profile.production
        class ProductionService:
            pass

        @component
        @profile.test
        class TestService:
            pass

        @component
        class NoProfileService:
            pass

        container = Container()
        container.scan()  # No profile parameter

        # All services should be registered (backward compatibility)
        prod = container.resolve(ProductionService)
        test = container.resolve(TestService)
        no_profile = container.resolve(NoProfileService)

        assert isinstance(prod, ProductionService)
        assert isinstance(test, TestService)
        assert isinstance(no_profile, NoProfileService)
