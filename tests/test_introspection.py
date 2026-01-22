"""Tests for container introspection API (#316).

The introspection API provides methods to inspect container state for debugging:
- list_registered(): List all registered ports
- is_registered(port): Check if a port has an adapter
- get_adapters_for(port): Get adapters by profile for a port
- active_profile: Get the current container profile
"""

from typing import Protocol

from dioxide import (
    Container,
    Profile,
    adapter,
    service,
)


class EmailPort(Protocol):
    """Test protocol for email functionality."""

    async def send(self, to: str, subject: str, body: str) -> None:
        """Send an email."""
        ...


class CachePort(Protocol):
    """Test protocol for cache functionality."""

    def get(self, key: str) -> str | None:
        """Get a cached value."""
        ...

    def set(self, key: str, value: str) -> None:
        """Set a cached value."""
        ...


class DescribeListRegistered:
    """Tests for Container.list_registered() method."""

    def it_returns_empty_list_for_empty_container(self) -> None:
        """list_registered() returns empty list when no types are registered."""
        container = Container()

        result = container.list_registered()

        assert result == []

    def it_returns_registered_port_types(self) -> None:
        """list_registered() returns ports that have registered adapters."""

        @adapter.for_(EmailPort, profile=Profile.PRODUCTION)
        class SendGridAdapter:
            async def send(self, to: str, subject: str, body: str) -> None:
                pass

        container = Container()
        container.scan(profile=Profile.PRODUCTION)

        result = container.list_registered()

        assert EmailPort in result

    def it_returns_registered_service_types(self) -> None:
        """list_registered() returns services that are registered."""

        @service
        class UserService:
            pass

        container = Container()
        container.scan(profile=Profile.PRODUCTION)

        result = container.list_registered()

        assert UserService in result

    def it_returns_all_registered_types(self) -> None:
        """list_registered() returns both services and port types."""

        @adapter.for_(EmailPort, profile=Profile.PRODUCTION)
        class SendGridAdapter:
            async def send(self, to: str, subject: str, body: str) -> None:
                pass

        @service
        class UserService:
            pass

        container = Container()
        container.scan(profile=Profile.PRODUCTION)

        result = container.list_registered()

        assert EmailPort in result
        assert UserService in result
        assert len(result) == 2


class DescribeIsRegistered:
    """Tests for Container.is_registered() method."""

    def it_returns_false_for_unregistered_type(self) -> None:
        """is_registered() returns False for types not in the container."""
        container = Container()

        result = container.is_registered(EmailPort)

        assert result is False

    def it_returns_true_for_registered_port(self) -> None:
        """is_registered() returns True for registered ports."""

        @adapter.for_(EmailPort, profile=Profile.PRODUCTION)
        class SendGridAdapter:
            async def send(self, to: str, subject: str, body: str) -> None:
                pass

        container = Container()
        container.scan(profile=Profile.PRODUCTION)

        result = container.is_registered(EmailPort)

        assert result is True

    def it_returns_true_for_registered_service(self) -> None:
        """is_registered() returns True for registered services."""

        @service
        class UserService:
            pass

        container = Container()
        container.scan(profile=Profile.PRODUCTION)

        result = container.is_registered(UserService)

        assert result is True


class DescribeActiveProfile:
    """Tests for Container.active_profile property."""

    def it_returns_none_before_scan(self) -> None:
        """active_profile is None before scan is called."""
        container = Container()

        result = container.active_profile

        assert result is None

    def it_returns_profile_after_scan(self) -> None:
        """active_profile returns the profile used in scan()."""
        container = Container()
        container.scan(profile=Profile.PRODUCTION)

        result = container.active_profile

        assert result == Profile.PRODUCTION

    def it_returns_test_profile_when_scanned_with_test(self) -> None:
        """active_profile returns TEST when scanned with Profile.TEST."""
        container = Container()
        container.scan(profile=Profile.TEST)

        result = container.active_profile

        assert result == Profile.TEST

    def it_returns_profile_when_initialized_with_profile(self) -> None:
        """active_profile returns profile when container created with profile."""
        container = Container(profile=Profile.DEVELOPMENT)

        result = container.active_profile

        assert result == Profile.DEVELOPMENT

    def it_returns_profile_for_custom_string_profile(self) -> None:
        """active_profile returns Profile instance for custom string profiles."""
        container = Container()
        # Manually set a custom profile (extensible Profile supports any string)
        container._active_profile = 'custom-environment'

        result = container.active_profile

        # Custom profiles are valid Profile instances (Profile is extensible)
        assert result == Profile('custom-environment')
        assert isinstance(result, Profile)


class DescribeGetAdaptersFor:
    """Tests for Container.get_adapters_for() method."""

    def it_returns_empty_dict_for_unregistered_port(self) -> None:
        """get_adapters_for() returns empty dict for unregistered ports."""
        container = Container()

        result = container.get_adapters_for(EmailPort)

        assert result == {}

    def it_returns_adapter_for_active_profile(self) -> None:
        """get_adapters_for() returns the adapter for the active profile."""

        @adapter.for_(EmailPort, profile=Profile.PRODUCTION)
        class SendGridAdapter:
            async def send(self, to: str, subject: str, body: str) -> None:
                pass

        container = Container()
        container.scan(profile=Profile.PRODUCTION)

        result = container.get_adapters_for(EmailPort)

        assert Profile.PRODUCTION in result
        assert result[Profile.PRODUCTION] is SendGridAdapter

    def it_shows_all_profile_adapters_from_global_registry(self) -> None:
        """get_adapters_for() shows adapters from all profiles in global registry."""

        @adapter.for_(EmailPort, profile=Profile.PRODUCTION)
        class SendGridAdapter:
            async def send(self, to: str, subject: str, body: str) -> None:
                pass

        @adapter.for_(EmailPort, profile=Profile.TEST)
        class FakeEmailAdapter:
            async def send(self, to: str, subject: str, body: str) -> None:
                pass

        # Even with only production profile scanned, show all registered adapters
        container = Container()
        container.scan(profile=Profile.PRODUCTION)

        result = container.get_adapters_for(EmailPort)

        # Both adapters should be visible for debugging
        assert Profile.PRODUCTION in result
        assert result[Profile.PRODUCTION] is SendGridAdapter
        assert Profile.TEST in result
        assert result[Profile.TEST] is FakeEmailAdapter

    def it_returns_empty_dict_for_service_type(self) -> None:
        """get_adapters_for() returns empty dict for service types (not ports)."""

        @service
        class UserService:
            pass

        container = Container()
        container.scan(profile=Profile.PRODUCTION)

        result = container.get_adapters_for(UserService)

        assert result == {}
