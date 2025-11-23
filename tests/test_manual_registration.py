"""Tests for manual provider registration."""

from dioxide import (
    Container,
    service,
)


class DescribeRegisterSingleton:
    """Tests for manually registering singleton providers."""

    def it_registers_a_singleton_factory(self) -> None:
        """Registers a singleton factory and returns same instance each time."""
        # Arrange
        container = Container()
        call_count = 0

        class DatabaseConnection:
            def __init__(self) -> None:
                nonlocal call_count
                call_count += 1
                self.connection_id = call_count

        def factory() -> DatabaseConnection:
            return DatabaseConnection()

        # Act
        container.register_singleton(DatabaseConnection, factory)
        instance1 = container.resolve(DatabaseConnection)
        instance2 = container.resolve(DatabaseConnection)

        # Assert
        assert instance1 is instance2, 'Should return same instance'
        assert call_count == 1, 'Factory should be called only once'
        assert instance1.connection_id == 1


class DescribeRegisterFactory:
    """Tests for manually registering transient (factory) providers."""

    def it_registers_a_transient_factory(self) -> None:
        """Registers a transient factory and returns new instance each time."""
        # Arrange
        container = Container()
        call_count = 0

        class RequestContext:
            def __init__(self) -> None:
                nonlocal call_count
                call_count += 1
                self.request_id = call_count

        def factory() -> RequestContext:
            return RequestContext()

        # Act
        container.register_factory(RequestContext, factory)
        instance1 = container.resolve(RequestContext)
        instance2 = container.resolve(RequestContext)

        # Assert
        assert instance1 is not instance2, 'Should return different instances'
        assert call_count == 2, 'Factory should be called twice'
        assert instance1.request_id == 1
        assert instance2.request_id == 2


class DescribeManualRegistrationPrecedence:
    """Tests for manual registration taking precedence over @service."""

    def it_uses_manual_registration_over_service_decorator(self) -> None:
        """Manual registration overrides @service auto-discovery."""
        # Arrange
        container = Container()
        custom_value = 'custom_instance'

        @service
        class ServiceA:
            def __init__(self) -> None:
                self.value = 'auto_discovered'

        def custom_factory() -> ServiceA:
            instance = ServiceA()
            instance.value = custom_value
            return instance

        # Act - Register manually BEFORE scan
        container.register_singleton(ServiceA, custom_factory)
        container.scan()  # This should NOT override manual registration
        result = container.resolve(ServiceA)

        # Assert
        assert result.value == custom_value, 'Should use custom factory, not auto-discovered'
