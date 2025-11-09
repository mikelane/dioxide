"""Tests for @component.implements(Protocol) decorator functionality."""

from typing import Protocol

from dioxide import Container, component


def _clear_registry() -> None:
    """Clear the component registry between tests."""
    from dioxide import _clear_registry as clear

    clear()


class EmailProvider(Protocol):
    """Protocol for email sending."""

    async def send(self, to: str, subject: str, body: str) -> None:
        """Send an email."""
        ...


class DescribeComponentImplements:
    """Tests for @component.implements(Protocol) decorator."""

    def it_can_decorate_a_class_implementing_a_protocol(self) -> None:
        """Decorator can mark a class as implementing a protocol."""
        _clear_registry()

        @component.implements(EmailProvider)
        class SendGridEmail:
            async def send(self, to: str, subject: str, body: str) -> None:
                pass

        # Class should exist and be instantiable
        instance = SendGridEmail()
        assert instance is not None

    def it_registers_the_implementation_in_the_component_registry(self) -> None:
        """Decorator adds implementation to global registry."""
        _clear_registry()

        @component.implements(EmailProvider)
        class SendGridEmail:
            async def send(self, to: str, subject: str, body: str) -> None:
                pass

        from dioxide import _get_registered_components

        registered = _get_registered_components()
        assert SendGridEmail in registered

    def it_stores_protocol_metadata_on_the_class(self) -> None:
        """Decorator attaches protocol metadata to the class."""
        _clear_registry()

        @component.implements(EmailProvider)
        class SendGridEmail:
            async def send(self, to: str, subject: str, body: str) -> None:
                pass

        # Check that protocol metadata is stored
        assert hasattr(SendGridEmail, '__dioxide_implements__')
        assert SendGridEmail.__dioxide_implements__ == EmailProvider

    def it_allows_container_to_resolve_protocol_to_implementation(self) -> None:
        """Container resolves protocol type to its implementation."""
        _clear_registry()

        @component.implements(EmailProvider)
        class SendGridEmail:
            async def send(self, to: str, subject: str, body: str) -> None:
                pass

        container = Container()
        container.scan()

        # Resolve using protocol type
        provider = container.resolve(EmailProvider)
        assert isinstance(provider, SendGridEmail)

    def it_supports_multiple_implementations_of_same_protocol(self) -> None:
        """Multiple classes can implement the same protocol."""
        _clear_registry()

        @component.implements(EmailProvider)
        class SendGridEmail:
            async def send(self, to: str, subject: str, body: str) -> None:
                self.provider = 'sendgrid'

        @component.implements(EmailProvider)
        class InMemoryEmail:
            def __init__(self) -> None:
                self.sent_emails: list[dict[str, str]] = []

            async def send(self, to: str, subject: str, body: str) -> None:
                self.sent_emails.append({'to': to, 'subject': subject, 'body': body})

        from dioxide import _get_registered_components

        registered = _get_registered_components()
        assert SendGridEmail in registered
        assert InMemoryEmail in registered

    def it_can_be_combined_with_scope_parameter(self) -> None:
        """Decorator can be combined with scope parameter."""
        _clear_registry()

        from dioxide import Scope

        @component.implements(EmailProvider, scope=Scope.FACTORY)
        class SendGridEmail:
            async def send(self, to: str, subject: str, body: str) -> None:
                pass

        assert hasattr(SendGridEmail, '__dioxide_scope__')
        assert SendGridEmail.__dioxide_scope__ == Scope.FACTORY


class DescribeProtocolResolutionWithProfiles:
    """Tests for protocol resolution combined with profile system."""

    def it_resolves_protocol_based_on_active_profile(self) -> None:
        """Container resolves protocol to profile-specific implementation."""
        _clear_registry()

        from dioxide import profile

        @component.implements(EmailProvider)
        @profile.production
        class SendGridEmail:
            async def send(self, to: str, subject: str, body: str) -> None:
                self.provider = 'sendgrid'

        @component.implements(EmailProvider)
        @profile.test
        class InMemoryEmail:
            def __init__(self) -> None:
                self.sent_emails: list[dict[str, str]] = []

            async def send(self, to: str, subject: str, body: str) -> None:
                self.sent_emails.append({'to': to, 'subject': subject, 'body': body})

        # This will require container.scan() to support profile parameter
        # For now, just verify both are registered
        from dioxide import _get_registered_components

        registered = _get_registered_components()
        assert SendGridEmail in registered
        assert InMemoryEmail in registered

        # Verify profile metadata exists
        assert hasattr(SendGridEmail, '__dioxide_profiles__')
        assert 'production' in SendGridEmail.__dioxide_profiles__
        assert hasattr(InMemoryEmail, '__dioxide_profiles__')
        assert 'test' in InMemoryEmail.__dioxide_profiles__


class DescribeProtocolResolutionEdgeCases:
    """Tests for edge cases in protocol resolution."""

    def it_raises_error_when_protocol_not_registered(self) -> None:
        """Container raises KeyError when protocol has no implementations."""
        _clear_registry()

        class UnusedProtocol(Protocol):
            def method(self) -> None: ...

        container = Container()
        container.scan()

        # Attempting to resolve unregistered protocol should raise KeyError
        try:
            container.resolve(UnusedProtocol)
            raise AssertionError('Expected KeyError')
        except KeyError:
            pass

    def it_resolves_concrete_class_directly_without_protocol(self) -> None:
        """Container can still resolve concrete classes without protocol."""
        _clear_registry()

        @component
        class ConcreteService:
            pass

        container = Container()
        container.scan()

        service = container.resolve(ConcreteService)
        assert isinstance(service, ConcreteService)


class DescribeDependencyInjectionWithProtocols:
    """Tests for dependency injection with protocol-based components."""

    def it_injects_protocol_implementation_into_dependent_component(self) -> None:
        """Container injects protocol implementation when component depends on protocol."""
        _clear_registry()

        @component.implements(EmailProvider)
        class SimpleEmail:
            async def send(self, to: str, subject: str, body: str) -> None:
                self.last_to = to

        @component
        class NotificationService:
            def __init__(self, email: EmailProvider):
                self.email = email

        container = Container()
        container.scan()

        service = container.resolve(NotificationService)

        # Should have injected SimpleEmail instance
        assert isinstance(service.email, SimpleEmail)

    def it_injects_multiple_protocol_implementations(self) -> None:
        """Container can inject multiple different protocols into a single component."""
        _clear_registry()

        class StorageBackend(Protocol):
            """Protocol for storage operations."""

            def save(self, key: str, value: str) -> None:
                """Save a key-value pair."""
                ...

            def get(self, key: str) -> str | None:
                """Retrieve a value by key."""
                ...

        @component.implements(EmailProvider)
        class SimpleEmail:
            async def send(self, to: str, subject: str, body: str) -> None:
                pass

        @component.implements(StorageBackend)
        class InMemoryStorage:
            def __init__(self) -> None:
                self._data: dict[str, str] = {}

            def save(self, key: str, value: str) -> None:
                self._data[key] = value

            def get(self, key: str) -> str | None:
                return self._data.get(key)

        @component
        class UserService:
            def __init__(self, email: EmailProvider, storage: StorageBackend):
                self.email = email
                self.storage = storage

        container = Container()
        container.scan()

        service = container.resolve(UserService)

        assert isinstance(service.email, SimpleEmail)
        assert isinstance(service.storage, InMemoryStorage)


class DescribeSingletonAndFactoryScopes:
    """Tests for singleton and factory scopes with protocol implementations."""

    def it_resolves_singleton_protocol_implementation_to_same_instance(self) -> None:
        """Protocol resolution respects SINGLETON scope."""
        _clear_registry()

        @component.implements(EmailProvider)
        class SingletonEmail:
            async def send(self, to: str, subject: str, body: str) -> None:
                pass

        container = Container()
        container.scan()

        provider1 = container.resolve(EmailProvider)
        provider2 = container.resolve(EmailProvider)

        # Same instance (singleton)
        assert provider1 is provider2

    def it_resolves_factory_protocol_implementation_to_different_instances(self) -> None:
        """Protocol resolution respects FACTORY scope."""
        _clear_registry()

        from dioxide import Scope

        @component.implements(EmailProvider, scope=Scope.FACTORY)
        class FactoryEmail:
            async def send(self, to: str, subject: str, body: str) -> None:
                pass

        container = Container()
        container.scan()

        provider1 = container.resolve(EmailProvider)
        provider2 = container.resolve(EmailProvider)

        # Different instances (factory)
        assert provider1 is not provider2

    def it_can_resolve_both_concrete_class_and_protocol(self) -> None:
        """Implementation can be resolved both by concrete type and protocol."""
        _clear_registry()

        @component.implements(EmailProvider)
        class SimpleEmail:
            async def send(self, to: str, subject: str, body: str) -> None:
                self.sent = True

        container = Container()
        container.scan()

        # Resolve by protocol
        by_protocol = container.resolve(EmailProvider)
        # Resolve by concrete type
        by_concrete = container.resolve(SimpleEmail)

        # Both should be the same singleton instance
        assert by_protocol is by_concrete
        assert isinstance(by_protocol, SimpleEmail)
        assert isinstance(by_concrete, SimpleEmail)
