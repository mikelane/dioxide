"""Tests for descriptive error messages when resolution fails.

This module tests the new AdapterNotFoundError and ServiceNotFoundError
exceptions that provide helpful, actionable error messages when dependency
resolution fails.
"""

from typing import (
    Any,
    Protocol,
)

import pytest

from dioxide import (
    Container,
    Profile,
    adapter,
    service,
)
from dioxide.exceptions import (
    AdapterNotFoundError,
    ServiceNotFoundError,
)


class EmailPort(Protocol):
    """Test protocol for email adapters."""

    async def send(self, to: str, subject: str, body: str) -> None:
        """Send an email message."""
        ...


class DatabasePort(Protocol):
    """Test protocol for database adapters."""

    def query(self, sql: str) -> list[dict[str, Any]]:
        """Execute a database query."""
        ...


class DescribeAdapterNotFoundError:
    """Tests for AdapterNotFoundError when no adapter is registered for a port."""

    def it_raises_when_no_adapter_exists_for_profile(self) -> None:
        """Raises AdapterNotFoundError when resolving port with no matching adapter."""

        @adapter.for_(EmailPort, profile=Profile.PRODUCTION)
        class SendGridAdapter:
            async def send(self, to: str, subject: str, body: str) -> None:
                pass

        container = Container()
        container.scan(profile=Profile.TEST)  # No TEST adapter registered

        with pytest.raises(AdapterNotFoundError) as exc_info:
            container.resolve(EmailPort)

        error_msg = str(exc_info.value)
        # Error should mention the port
        assert 'EmailPort' in error_msg
        # Error should mention the active profile
        assert 'test' in error_msg.lower()
        # Error should list available adapters
        assert 'SendGridAdapter' in error_msg or 'production' in error_msg.lower()

    def it_provides_helpful_hint_when_no_adapters_at_all(self) -> None:
        """Error message includes hint to add @adapter.for_() when no adapters exist."""

        container = Container()
        container.scan(profile=Profile.TEST)

        with pytest.raises(AdapterNotFoundError) as exc_info:
            container.resolve(DatabasePort)

        error_msg = str(exc_info.value)
        # Should mention the port
        assert 'DatabasePort' in error_msg
        # Should suggest how to fix
        assert '@adapter.for_' in error_msg or 'adapter' in error_msg.lower()
        # Should mention the profile
        assert 'test' in error_msg.lower()

    def it_shows_available_adapters_for_other_profiles(self) -> None:
        """Error lists adapters that ARE available (for different profiles)."""

        @adapter.for_(EmailPort, profile=Profile.PRODUCTION)
        class SendGridAdapter:
            async def send(self, to: str, subject: str, body: str) -> None:
                pass

        @adapter.for_(EmailPort, profile=Profile.DEVELOPMENT)
        class ConsoleEmailAdapter:
            async def send(self, to: str, subject: str, body: str) -> None:
                pass

        container = Container()
        container.scan(profile=Profile.TEST)

        with pytest.raises(AdapterNotFoundError) as exc_info:
            container.resolve(EmailPort)

        error_msg = str(exc_info.value)
        # Should show available adapters (even for wrong profiles)
        assert 'SendGridAdapter' in error_msg or 'ConsoleEmailAdapter' in error_msg


class DescribeServiceNotFoundError:
    """Tests for ServiceNotFoundError when service resolution fails."""

    def it_raises_when_service_has_unresolvable_dependency(self) -> None:
        """Raises ServiceNotFoundError when service depends on unregistered type."""

        @service
        class UserService:
            def __init__(self, db: DatabasePort):
                self.db = db

        container = Container()
        container.scan(profile=Profile.TEST)  # No DatabasePort adapter registered

        with pytest.raises(ServiceNotFoundError) as exc_info:
            container.resolve(UserService)

        error_msg = str(exc_info.value)
        # Should mention the service being resolved
        assert 'UserService' in error_msg
        # Should mention the missing dependency
        assert 'DatabasePort' in error_msg
        # Should be helpful
        assert 'dependencies' in error_msg.lower() or 'could not be resolved' in error_msg.lower()

    def it_raises_when_component_not_registered(self) -> None:
        """Raises ServiceNotFoundError when trying to resolve unregistered component."""

        class UnregisteredService:
            """A service that was never decorated with @service or @service."""

            pass

        container = Container()
        container.scan(profile=Profile.TEST)

        with pytest.raises(ServiceNotFoundError) as exc_info:
            container.resolve(UnregisteredService)

        error_msg = str(exc_info.value)
        # Should mention the type
        assert 'UnregisteredService' in error_msg
        # Should suggest registration
        assert '@service' in error_msg or '@service' in error_msg or 'register' in error_msg.lower()

    def it_includes_helpful_context_in_error_message(self) -> None:
        """Error message includes context like active profile and available types."""

        @service
        class OrderService:
            def __init__(self, email: EmailPort):
                self.email = email

        container = Container()
        container.scan(profile=Profile.PRODUCTION)

        with pytest.raises(ServiceNotFoundError) as exc_info:
            container.resolve(OrderService)

        error_msg = str(exc_info.value)
        # Should provide context
        assert 'OrderService' in error_msg
        assert 'EmailPort' in error_msg
        # Should mention the profile
        assert 'production' in error_msg.lower()
