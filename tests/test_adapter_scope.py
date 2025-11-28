"""Tests for scope parameter on @adapter.for_() decorator.

This module tests the ability to specify instance lifecycle scope
for adapters, enabling transient (FACTORY) adapters that return
new instances on each resolution.
"""

from typing import Protocol

from dioxide import (
    Container,
    Profile,
    Scope,
    adapter,
)


class CounterPort(Protocol):
    """Port for testing scope behavior with instance counting."""

    def get_instance_id(self) -> int:
        """Return unique identifier for this instance."""
        ...


class DescribeAdapterScope:
    """Tests for scope parameter on @adapter.for_()."""

    def it_defaults_to_singleton_scope(self) -> None:
        """Adapters are singleton by default when scope is not specified."""

        @adapter.for_(CounterPort, profile=Profile.TEST)
        class DefaultScopeAdapter:
            def get_instance_id(self) -> int:
                return id(self)

        assert hasattr(DefaultScopeAdapter, '__dioxide_scope__')
        assert DefaultScopeAdapter.__dioxide_scope__ == Scope.SINGLETON

    def it_accepts_explicit_singleton_scope(self) -> None:
        """Adapters can explicitly specify SINGLETON scope."""

        @adapter.for_(CounterPort, profile='explicit-singleton', scope=Scope.SINGLETON)
        class ExplicitSingletonAdapter:
            def get_instance_id(self) -> int:
                return id(self)

        assert ExplicitSingletonAdapter.__dioxide_scope__ == Scope.SINGLETON

    def it_accepts_factory_scope(self) -> None:
        """Adapters can specify FACTORY scope for transient instances."""

        @adapter.for_(CounterPort, profile='factory-scope', scope=Scope.FACTORY)
        class FactoryScopeAdapter:
            def get_instance_id(self) -> int:
                return id(self)

        assert FactoryScopeAdapter.__dioxide_scope__ == Scope.FACTORY

    def it_singleton_returns_same_instance_on_resolve(self) -> None:
        """Singleton adapters return the same instance on each resolution."""

        class SingletonPort(Protocol):
            def get_instance_id(self) -> int: ...

        @adapter.for_(SingletonPort, profile='singleton-test', scope=Scope.SINGLETON)
        class SingletonTestAdapter:
            def get_instance_id(self) -> int:
                return id(self)

        container = Container()
        container.scan(profile='singleton-test')

        instance1 = container.resolve(SingletonPort)
        instance2 = container.resolve(SingletonPort)

        assert instance1 is instance2
        assert instance1.get_instance_id() == instance2.get_instance_id()

    def it_factory_returns_different_instances_on_resolve(self) -> None:
        """Factory adapters return different instances on each resolution."""

        class FactoryPort(Protocol):
            def get_instance_id(self) -> int: ...

        @adapter.for_(FactoryPort, profile='factory-test', scope=Scope.FACTORY)
        class FactoryTestAdapter:
            def get_instance_id(self) -> int:
                return id(self)

        container = Container()
        container.scan(profile='factory-test')

        instance1 = container.resolve(FactoryPort)
        instance2 = container.resolve(FactoryPort)

        assert instance1 is not instance2
        assert instance1.get_instance_id() != instance2.get_instance_id()

    def it_factory_scope_enables_fresh_state_per_resolution(self) -> None:
        """Factory scope allows test fakes to have fresh state per resolution."""

        class EmailPort(Protocol):
            def send(self, to: str, message: str) -> None: ...
            def get_sent_count(self) -> int: ...

        @adapter.for_(EmailPort, profile='fresh-state-test', scope=Scope.FACTORY)
        class FreshFakeEmailAdapter:
            def __init__(self) -> None:
                self.sent_count = 0

            def send(self, to: str, message: str) -> None:
                self.sent_count += 1

            def get_sent_count(self) -> int:
                return self.sent_count

        container = Container()
        container.scan(profile='fresh-state-test')

        # Get first instance and send some emails
        email1 = container.resolve(EmailPort)
        email1.send('alice@example.com', 'Hello')
        email1.send('bob@example.com', 'Hi')
        assert email1.get_sent_count() == 2

        # Get second instance - should have fresh state
        email2 = container.resolve(EmailPort)
        assert email2.get_sent_count() == 0
        email2.send('charlie@example.com', 'Hey')
        assert email2.get_sent_count() == 1

        # Original instance unchanged
        assert email1.get_sent_count() == 2


class DescribeScopeRequestEnum:
    """Tests for Scope.REQUEST enum value."""

    def it_has_request_scope_value(self) -> None:
        """Scope.REQUEST exists with value 'request'."""
        assert Scope.REQUEST.value == 'request'

    def it_can_be_used_with_adapter_decorator(self) -> None:
        """Request scope can be specified on @adapter.for_() decorator."""

        class RequestPort(Protocol):
            def get_request_id(self) -> int: ...

        @adapter.for_(RequestPort, profile='request-scope-test', scope=Scope.REQUEST)
        class RequestScopedAdapter:
            def get_request_id(self) -> int:
                return id(self)

        assert hasattr(RequestScopedAdapter, '__dioxide_scope__')
        assert RequestScopedAdapter.__dioxide_scope__ == Scope.REQUEST

    def it_is_a_valid_member_of_scope_enum(self) -> None:
        """REQUEST is a valid member of the Scope enum alongside SINGLETON and FACTORY."""
        scope_members = {member.value for member in Scope}
        assert 'request' in scope_members
        assert 'singleton' in scope_members
        assert 'factory' in scope_members
        assert len(scope_members) == 3
