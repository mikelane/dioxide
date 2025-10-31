"""Tests for @component decorator and auto-discovery."""

from dioxide import Container, Scope, component


def _clear_registry() -> None:
    """Clear the component registry between tests."""
    from dioxide import _clear_registry as clear

    clear()


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
        _clear_registry()

        @component
        class UserService:
            pass

        from dioxide import _get_registered_components

        registered = _get_registered_components()
        assert UserService in registered

    def it_can_be_applied_with_parentheses(self) -> None:
        """Decorator can be applied with parentheses and scope argument."""
        _clear_registry()

        @component()
        class DefaultScopeService:
            pass

        @component(scope=Scope.FACTORY)
        class FactoryService:
            pass

        from dioxide import _get_registered_components

        registered = _get_registered_components()
        assert DefaultScopeService in registered
        assert FactoryService in registered


class DescribeScan:
    """Tests for Container.scan() auto-discovery."""

    def it_registers_all_component_classes(self) -> None:
        """Scan finds and registers all @component decorated classes."""
        _clear_registry()

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
        _clear_registry()

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
        _clear_registry()

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
        _clear_registry()

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
        _clear_registry()

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
        _clear_registry()

        @component
        class LegacyService:
            def __init__(self) -> None:
                self.value = 'legacy'

        container = Container()
        container.scan()

        service = container.resolve(LegacyService)
        assert isinstance(service, LegacyService)
        assert service.value == 'legacy'

    def it_creates_new_instances_for_factory_scope(self) -> None:
        """Components with factory scope create new instances each time."""
        _clear_registry()

        @component(scope=Scope.FACTORY)
        class FactoryService:
            pass

        container = Container()
        container.scan()

        service1 = container.resolve(FactoryService)
        service2 = container.resolve(FactoryService)

        # Different instances for factory scope
        assert service1 is not service2


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
