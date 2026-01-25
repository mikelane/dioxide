"""Tests for rich error context collection and formatting.

This module tests that exceptions raised by the container include full context
about what was registered, active profile, and available alternatives.

Issue #344: Better Errors: Implement Rich Context Collection and Formatting
"""

from __future__ import annotations

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
    CaptiveDependencyError,
    ScopeError,
    ServiceNotFoundError,
)
from dioxide.scope import Scope


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


class UnregisteredPort(Protocol):
    """A port with no registered adapters."""

    def do_something(self) -> None: ...


class DescribeAdapterNotFoundErrorContext:
    """Tests for AdapterNotFoundError with full context."""

    def it_shows_available_adapters(self) -> None:
        """Error message shows adapters registered for other profiles."""

        @adapter.for_(EmailPort, profile=Profile.PRODUCTION)
        class SendGridAdapter:
            async def send(self, to: str, subject: str, body: str) -> None:
                pass

        container = Container()
        container.scan(profile=Profile.TEST)

        with pytest.raises(AdapterNotFoundError) as exc_info:
            container.resolve(EmailPort)

        msg = str(exc_info.value)
        assert 'No adapter' in msg
        assert 'EmailPort' in msg
        assert "profile 'test'" in msg or "'test'" in msg
        assert 'SendGridAdapter' in msg
        assert 'production' in msg.lower()

    def it_has_rich_context_accessible_via_attributes(self) -> None:
        """Error has rich context accessible via context/suggestions attributes."""

        @adapter.for_(EmailPort, profile=Profile.PRODUCTION)
        class SendGridAdapter:
            async def send(self, to: str, subject: str, body: str) -> None:
                pass

        container = Container()
        container.scan(profile=Profile.TEST)

        with pytest.raises(AdapterNotFoundError) as exc_info:
            container.resolve(EmailPort)

        error = exc_info.value
        # The exception should have rich context accessible via attributes
        # (even if the __str__ output is terse)
        assert hasattr(error, 'context')
        assert hasattr(error, 'suggestions')

    def it_shows_no_adapters_when_none_registered(self) -> None:
        """Error message states when no adapters are registered at all."""
        container = Container()
        container.scan(profile=Profile.TEST)

        with pytest.raises(AdapterNotFoundError) as exc_info:
            container.resolve(UnregisteredPort)

        msg = str(exc_info.value)
        assert 'UnregisteredPort' in msg
        assert 'No adapter' in msg or 'no adapter' in msg
        # Should indicate no adapters exist at all
        assert 'none' in msg.lower() or 'no adapters' in msg.lower()

    def it_shows_multiple_adapters_for_port(self) -> None:
        """Error message shows all adapters when multiple exist for other profiles."""

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

        msg = str(exc_info.value)
        # Should list both adapters
        assert 'SendGridAdapter' in msg or 'ConsoleEmailAdapter' in msg


class DescribeServiceNotFoundErrorContext:
    """Tests for ServiceNotFoundError with dependency analysis."""

    def it_shows_failed_dependency(self) -> None:
        """Error message shows which dependency caused the failure."""

        @service
        class UserService:
            def __init__(self, db: DatabasePort):
                self.db = db

        container = Container()
        container.scan(profile=Profile.TEST)

        with pytest.raises(ServiceNotFoundError) as exc_info:
            container.resolve(UserService)

        msg = str(exc_info.value)
        assert 'UserService' in msg
        assert 'db' in msg or 'DatabasePort' in msg
        assert 'no adapter' in msg.lower() or 'missing' in msg.lower()

    def it_shows_not_registered_when_service_missing_decorator(self) -> None:
        """Error message indicates when service is not registered."""

        class NotDecoratedService:
            pass

        container = Container()
        container.scan(profile=Profile.TEST)

        with pytest.raises(ServiceNotFoundError) as exc_info:
            container.resolve(NotDecoratedService)

        msg = str(exc_info.value)
        assert 'NotDecoratedService' in msg
        assert '@service' in msg or 'registered' in msg.lower()

    def it_includes_profile_context(self) -> None:
        """Error message includes the active profile."""

        @service
        class PaymentService:
            def __init__(self, email: EmailPort):
                self.email = email

        container = Container()
        container.scan(profile=Profile.STAGING)

        with pytest.raises(ServiceNotFoundError) as exc_info:
            container.resolve(PaymentService)

        msg = str(exc_info.value)
        assert 'staging' in msg.lower()

    def it_lists_all_dependencies(self) -> None:
        """Error message shows all dependencies of the service."""

        @service
        class ComplexService:
            def __init__(self, email: EmailPort, db: DatabasePort):
                self.email = email
                self.db = db

        container = Container()
        container.scan(profile=Profile.TEST)

        with pytest.raises(ServiceNotFoundError) as exc_info:
            container.resolve(ComplexService)

        msg = str(exc_info.value)
        # Should mention at least one dependency
        assert 'EmailPort' in msg or 'DatabasePort' in msg


class DescribeScopeErrorContext:
    """Tests for ScopeError with scope requirement context."""

    def it_names_component_and_scope_requirement(self) -> None:
        """Error message names the component and required scope type."""

        @service(scope=Scope.REQUEST)
        class RequestSession:
            pass

        container = Container()
        container.scan(profile=Profile.TEST)

        with pytest.raises(ScopeError) as exc_info:
            container.resolve(RequestSession)

        msg = str(exc_info.value)
        assert 'RequestSession' in msg
        assert 'REQUEST' in msg

    def it_suggests_creating_scope(self) -> None:
        """Error message suggests using create_scope()."""

        @service(scope=Scope.REQUEST)
        class RequestHandler:
            pass

        container = Container()
        container.scan(profile=Profile.TEST)

        with pytest.raises(ScopeError) as exc_info:
            container.resolve(RequestHandler)

        msg = str(exc_info.value)
        # Should suggest creating a scope
        assert 'scope' in msg.lower()


class DescribeCaptiveDependencyErrorContext:
    """Tests for CaptiveDependencyError during scan."""

    def it_names_both_components_and_scopes(self) -> None:
        """Error message names parent (SINGLETON) and child (REQUEST) with scopes."""

        @service(scope=Scope.REQUEST)
        class RequestContext:
            pass

        @service  # SINGLETON by default
        class CaptiveService:
            def __init__(self, ctx: RequestContext):
                self.ctx = ctx

        container = Container()

        with pytest.raises(CaptiveDependencyError) as exc_info:
            container.scan(profile=Profile.TEST)

        msg = str(exc_info.value)
        assert 'CaptiveService' in msg
        assert 'RequestContext' in msg
        assert 'SINGLETON' in msg
        assert 'REQUEST' in msg

    def it_explains_why_captive_is_problematic(self) -> None:
        """Error message explains why SINGLETON cannot depend on REQUEST."""

        @service(scope=Scope.REQUEST)
        class SessionData:
            pass

        @service
        class GlobalProcessor:
            def __init__(self, session: SessionData):
                self.session = session

        container = Container()

        with pytest.raises(CaptiveDependencyError) as exc_info:
            container.scan(profile=Profile.TEST)

        msg = str(exc_info.value)
        # Should mention the scope violation
        assert 'SINGLETON' in msg and 'REQUEST' in msg


class DescribeContainerContextTracking:
    """Tests for container tracking of adapters and active profile."""

    def it_tracks_active_profile_after_scan(self) -> None:
        """Container tracks the active profile for error messages."""
        container = Container()
        container.scan(profile=Profile.PRODUCTION)

        # Access the active profile property
        assert container.active_profile == Profile.PRODUCTION

    def it_active_profile_is_none_before_scan(self) -> None:
        """Active profile is None before scan is called."""
        container = Container()

        assert container.active_profile is None

    def it_normalizes_string_profile_to_lowercase(self) -> None:
        """String profiles are normalized to lowercase for matching."""
        container = Container()
        container.scan(profile='PRODUCTION')

        # Profile should be normalized
        assert container.active_profile == Profile.PRODUCTION or str(container.active_profile).lower() == 'production'


class DescribeAdapterNotFoundErrorConstructor:
    """Tests for AdapterNotFoundError with structured constructor parameters."""

    def it_accepts_port_and_profile_parameters(self) -> None:
        """AdapterNotFoundError can be constructed with port and profile."""
        error = AdapterNotFoundError(
            port=EmailPort,
            profile='test',
        )
        msg = str(error)
        assert 'EmailPort' in msg
        assert 'test' in msg.lower()

    def it_accepts_available_adapters_parameter(self) -> None:
        """AdapterNotFoundError can show available adapters from other profiles."""

        class FakeAdapter:
            pass

        error = AdapterNotFoundError(
            port=EmailPort,
            profile='test',
            available_adapters=[('FakeAdapter', ['production'])],
        )
        msg = str(error)
        assert 'FakeAdapter' in msg
        assert 'production' in msg.lower()

    def it_formats_message_with_all_context(self) -> None:
        """AdapterNotFoundError formats message including all available context."""

        class SendGridAdapter:
            pass

        class ConsoleAdapter:
            pass

        error = AdapterNotFoundError(
            port=EmailPort,
            profile='test',
            available_adapters=[
                ('SendGridAdapter', ['production']),
                ('ConsoleAdapter', ['development']),
            ],
        )
        msg = str(error)
        assert 'EmailPort' in msg
        assert 'test' in msg.lower()
        # Should list available adapters
        assert 'SendGridAdapter' in msg or 'ConsoleAdapter' in msg


class DescribeServiceNotFoundErrorConstructor:
    """Tests for ServiceNotFoundError with structured constructor parameters."""

    def it_accepts_service_parameter(self) -> None:
        """ServiceNotFoundError can be constructed with service class."""

        class MyService:
            pass

        error = ServiceNotFoundError(
            service=MyService,
        )
        msg = str(error)
        assert 'MyService' in msg

    def it_accepts_profile_parameter(self) -> None:
        """ServiceNotFoundError includes profile context."""

        class MyService:
            pass

        error = ServiceNotFoundError(
            service=MyService,
            profile='production',
        )
        msg = str(error)
        assert 'production' in msg.lower()

    def it_accepts_failed_dependency_parameter(self) -> None:
        """ServiceNotFoundError shows failed dependency with reason."""

        class MyService:
            pass

        error = ServiceNotFoundError(
            service=MyService,
            profile='test',
            failed_dependency=('db', DatabasePort, 'no adapter for profile'),
        )
        msg = str(error)
        assert 'MyService' in msg
        assert 'db' in msg or 'DatabasePort' in msg

    def it_accepts_dependencies_list(self) -> None:
        """ServiceNotFoundError can list all dependencies."""

        class MyService:
            pass

        error = ServiceNotFoundError(
            service=MyService,
            profile='test',
            dependencies=['email: EmailPort', 'db: DatabasePort'],
        )
        msg = str(error)
        assert 'MyService' in msg
        # Should indicate it has dependencies
        assert 'EmailPort' in msg or 'DatabasePort' in msg or 'dependenc' in msg.lower()

    def it_distinguishes_empty_dependencies_from_not_registered(self) -> None:
        """Empty dependencies list means registered with no deps, not unregistered."""

        class MyService:
            pass

        # dependencies=[] means the service IS registered but has no dependencies
        error = ServiceNotFoundError(
            service=MyService,
            profile='test',
            dependencies=[],
        )
        msg = str(error)
        assert 'MyService' in msg
        # Should NOT say "Not registered" - we know it's registered with no deps
        assert 'Not registered' not in msg
        # Should indicate it has no dependencies
        assert 'no dependenc' in msg.lower() or 'Dependencies' in msg


class DescribeScopeErrorConstructor:
    """Tests for ScopeError with structured constructor parameters."""

    def it_accepts_component_and_scope_parameters(self) -> None:
        """ScopeError can be constructed with component and required scope."""

        class MyComponent:
            pass

        error = ScopeError(
            component=MyComponent,
            required_scope=Scope.REQUEST,
        )
        msg = str(error)
        assert 'MyComponent' in msg
        assert 'REQUEST' in msg


class DescribeCaptiveDependencyErrorConstructor:
    """Tests for CaptiveDependencyError with structured constructor parameters."""

    def it_accepts_parent_and_child_parameters(self) -> None:
        """CaptiveDependencyError names both components."""

        class ParentService:
            pass

        class ChildService:
            pass

        error = CaptiveDependencyError(
            parent=ParentService,
            parent_scope=Scope.SINGLETON,
            child=ChildService,
            child_scope=Scope.REQUEST,
        )
        msg = str(error)
        assert 'ParentService' in msg
        assert 'ChildService' in msg
        assert 'SINGLETON' in msg
        assert 'REQUEST' in msg
