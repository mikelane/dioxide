"""Tests for @component decorator and auto-discovery."""

from rivet_di import Container, component


def _clear_registry() -> None:
    """Clear the component registry between tests."""
    from rivet_di import _clear_registry as clear

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

        from rivet_di import _get_registered_components

        registered = _get_registered_components()
        assert UserService in registered


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
