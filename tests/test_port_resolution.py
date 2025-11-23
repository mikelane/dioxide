"""Tests for port-based resolution in Container.

Port-based resolution enables hexagonal architecture by allowing the container
to resolve implementations (adapters) based on their port (Protocol/ABC) and
active profile, rather than just concrete class types.
"""

from abc import (
    ABC,
    abstractmethod,
)
from typing import Protocol

import pytest

from dioxide import (
    Container,
    Scope,
    adapter,
)
from dioxide._registry import PROFILE_ATTRIBUTE
from dioxide.adapter import _adapter_registry
from dioxide.exceptions import AdapterNotFoundError


class EmailPort(Protocol):
    """Test protocol for email functionality."""

    async def send(self, to: str, subject: str, body: str) -> None:
        """Send an email."""
        ...


class StoragePort(ABC):
    """Test ABC for storage functionality."""

    @abstractmethod
    async def save(self, key: str, value: str) -> None:
        """Save a key-value pair."""
        ...


class DescribePortResolution:
    """Tests for resolving adapters by their port (Protocol/ABC)."""

    def it_resolves_protocol_adapter_for_active_profile(self) -> None:
        """container.resolve(EmailPort) returns adapter for active profile."""

        @adapter.for_(EmailPort, profile='production')
        class ProductionEmailAdapter:
            async def send(self, to: str, subject: str, body: str) -> None:
                pass

        @adapter.for_(EmailPort, profile='test')
        class TestEmailAdapter:
            async def send(self, to: str, subject: str, body: str) -> None:
                pass

        # Scan with production profile
        container = Container()
        container.scan(profile='production')

        # Should resolve production adapter when requesting EmailPort
        resolved = container.resolve(EmailPort)
        assert isinstance(resolved, ProductionEmailAdapter)
        assert not isinstance(resolved, TestEmailAdapter)

    def it_resolves_different_adapter_for_different_profile(self) -> None:
        """container.resolve(Port) returns different adapter for different profile."""

        @adapter.for_(EmailPort, profile='production')
        class ProductionEmailAdapter:
            async def send(self, to: str, subject: str, body: str) -> None:
                pass

        @adapter.for_(EmailPort, profile='test')
        class TestEmailAdapter:
            async def send(self, to: str, subject: str, body: str) -> None:
                pass

        # Test profile
        test_container = Container()
        test_container.scan(profile='test')
        test_resolved = test_container.resolve(EmailPort)
        assert isinstance(test_resolved, TestEmailAdapter)

        # Production profile
        prod_container = Container()
        prod_container.scan(profile='production')
        prod_resolved = prod_container.resolve(EmailPort)
        assert isinstance(prod_resolved, ProductionEmailAdapter)

    def it_resolves_abc_adapter_for_active_profile(self) -> None:
        """container.resolve(ABC) returns adapter for active profile."""

        @adapter.for_(StoragePort, profile='production')
        class PostgresAdapter(StoragePort):
            async def save(self, key: str, value: str) -> None:
                pass

        @adapter.for_(StoragePort, profile='test')
        class InMemoryAdapter(StoragePort):
            async def save(self, key: str, value: str) -> None:
                pass

        container = Container()
        container.scan(profile='production')

        resolved = container.resolve(StoragePort)
        assert isinstance(resolved, PostgresAdapter)
        assert not isinstance(resolved, InMemoryAdapter)

    def it_raises_on_port_without_adapter_for_profile(self) -> None:
        """container.resolve(Port) raises if no adapter for active profile."""

        @adapter.for_(EmailPort, profile='production')
        class ProductionEmailAdapter:
            async def send(self, to: str, subject: str, body: str) -> None:
                pass

        container = Container()
        container.scan(profile='test')  # No test adapter registered

        with pytest.raises(AdapterNotFoundError) as exc_info:
            container.resolve(EmailPort)

        # Error should mention port and profile
        error_msg = str(exc_info.value)
        assert 'EmailPort' in error_msg
        assert 'test' in error_msg.lower()

    def it_raises_on_multiple_adapters_for_same_port_and_profile(self) -> None:
        """container.resolve(Port) raises if multiple adapters for port+profile."""

        @adapter.for_(EmailPort, profile='production')
        class SendGridAdapter:
            async def send(self, to: str, subject: str, body: str) -> None:
                pass

        @adapter.for_(EmailPort, profile='production')
        class MailgunAdapter:
            async def send(self, to: str, subject: str, body: str) -> None:
                pass

        container = Container()

        # Scanning should detect ambiguity
        with pytest.raises(ValueError) as exc_info:
            container.scan(profile='production')

        # Error should mention ambiguity/multiple/conflict
        error_msg = str(exc_info.value).lower()
        assert any(word in error_msg for word in ['ambiguous', 'multiple', 'conflict'])

    def it_resolves_singleton_adapter_returns_same_instance(self) -> None:
        """container.resolve(Port) returns same instance for singleton adapters."""

        @adapter.for_(EmailPort, profile='production')
        class ProductionEmailAdapter:
            async def send(self, to: str, subject: str, body: str) -> None:
                pass

        container = Container()
        container.scan(profile='production')

        first = container.resolve(EmailPort)
        second = container.resolve(EmailPort)

        # Should be the same instance (singleton)
        assert first is second

    def it_resolves_adapter_with_multiple_profiles(self) -> None:
        """container.resolve(Port) works with adapter having multiple profiles."""

        @adapter.for_(EmailPort, profile=['test', 'development'])
        class FakeEmailAdapter:
            def __init__(self) -> None:
                self.sent_emails: list[dict[str, str]] = []

            async def send(self, to: str, subject: str, body: str) -> None:
                self.sent_emails.append({'to': to, 'subject': subject, 'body': body})

        # Should work with test profile
        test_container = Container()
        test_container.scan(profile='test')
        test_resolved = test_container.resolve(EmailPort)
        assert isinstance(test_resolved, FakeEmailAdapter)

        # Should work with development profile
        dev_container = Container()
        dev_container.scan(profile='development')
        dev_resolved = dev_container.resolve(EmailPort)
        assert isinstance(dev_resolved, FakeEmailAdapter)

    def it_resolves_port_case_insensitive_profile(self) -> None:
        """container.resolve(Port) normalizes profile names to lowercase."""

        @adapter.for_(EmailPort, profile='PRODUCTION')
        class ProductionEmailAdapter:
            async def send(self, to: str, subject: str, body: str) -> None:
                pass

        container = Container()
        container.scan(profile='production')  # lowercase

        resolved = container.resolve(EmailPort)
        assert isinstance(resolved, ProductionEmailAdapter)

    def it_resolves_adapter_when_scanning_without_profile(self) -> None:
        """container.scan() without profile parameter registers adapters."""

        @adapter.for_(EmailPort, profile='production')
        class ProductionEmailAdapter:
            async def send(self, to: str, subject: str, body: str) -> None:
                pass

        # Scan without profile - should register the adapter
        container = Container()
        container.scan()  # No profile parameter

        # Should resolve the adapter
        resolved = container.resolve(EmailPort)
        assert isinstance(resolved, ProductionEmailAdapter)

    def it_skips_adapter_without_port_attribute_during_scan(self) -> None:
        """container.scan() skips malformed adapters without __dioxide_port__."""

        # Manually add a malformed adapter to the registry (missing __dioxide_port__)
        # Give it a profile so it passes the profile filter
        class MalformedAdapter:
            pass

        setattr(MalformedAdapter, PROFILE_ATTRIBUTE, frozenset(['production']))

        # Temporarily inject into adapter registry
        _adapter_registry.add(MalformedAdapter)

        try:
            container = Container()
            # Should not raise - malformed adapter is skipped
            container.scan(profile='production')
        finally:
            # Clean up
            _adapter_registry.discard(MalformedAdapter)

    def it_skips_adapter_when_port_already_registered_manually_singleton(self) -> None:
        """container.scan() skips adapter if port already registered manually (singleton)."""

        @adapter.for_(EmailPort, profile='production')
        class ProductionEmailAdapter:
            async def send(self, to: str, subject: str, body: str) -> None:
                pass

        # Manually register a different implementation first
        class ManualEmailAdapter:
            async def send(self, to: str, subject: str, body: str) -> None:
                pass

        container = Container()
        container.register_singleton_factory(EmailPort, lambda: ManualEmailAdapter())

        # Scan should skip ProductionEmailAdapter (manual takes precedence)
        container.scan(profile='production')

        # Should get the manually registered one
        resolved = container.resolve(EmailPort)
        assert isinstance(resolved, ManualEmailAdapter)

    def it_skips_adapter_when_port_already_registered_manually_transient(self) -> None:
        """container.scan() skips adapter if port already registered manually (transient)."""

        @adapter.for_(EmailPort, profile='production')
        class ProductionEmailAdapter:
            async def send(self, to: str, subject: str, body: str) -> None:
                pass

        # Set the adapter to FACTORY scope to test transient path
        ProductionEmailAdapter.__dioxide_scope__ = Scope.FACTORY

        # Manually register a different implementation first
        class ManualEmailAdapter:
            async def send(self, to: str, subject: str, body: str) -> None:
                pass

        container = Container()
        container.register_transient_factory(EmailPort, lambda: ManualEmailAdapter())

        # Scan should skip ProductionEmailAdapter (manual takes precedence)
        container.scan(profile='production')

        # Should get the manually registered one
        resolved = container.resolve(EmailPort)
        assert isinstance(resolved, ManualEmailAdapter)
