"""Tests for terse error messages (1-4 lines max at runtime).

This module tests that all dioxide exceptions produce terse, actionable
error messages at runtime. Verbose explanations remain in docstrings only.

Issue #312: Runtime errors should be 1-3 lines max, with key diagnostic info preserved.
Issue #396: Added documentation URLs - error messages can now have 1 extra line for the URL.

Format:
  Line 1: Error title and context
  Lines 2-3: Diagnostic info (what went wrong, what's available)
  Line 4 (optional): Documentation URL (-> See: https://...)
"""

from __future__ import annotations

from typing import (
    TYPE_CHECKING,
    Any,
    Protocol,
)

import pytest

from dioxide import (
    Container,
    Profile,
    adapter,
    lifecycle,
    service,
)
from dioxide.exceptions import (
    AdapterNotFoundError,
    CaptiveDependencyError,
    ScopeError,
    ServiceNotFoundError,
)
from dioxide.scope import Scope

if TYPE_CHECKING:
    pass


# Module-level classes for CircularDependencyError tests
# These must be at module level for forward references to resolve properly
@service
@lifecycle
class _TerseTestCircularA:
    def __init__(self, b: _TerseTestCircularB) -> None:
        self.b = b

    async def initialize(self) -> None:
        pass

    async def dispose(self) -> None:
        pass


@service
@lifecycle
class _TerseTestCircularB:
    def __init__(self, a: _TerseTestCircularA) -> None:
        self.a = a

    async def initialize(self) -> None:
        pass

    async def dispose(self) -> None:
        pass


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


class DescribeTerseAdapterNotFoundError:
    """Tests for terse AdapterNotFoundError messages."""

    def it_produces_message_under_5_lines(self) -> None:
        """Error message is 1-4 lines maximum (3 diagnostic + 1 doc URL)."""

        @adapter.for_(EmailPort, profile=Profile.PRODUCTION)
        class SendGridAdapter:
            async def send(self, to: str, subject: str, body: str) -> None:
                pass

        container = Container()
        container.scan(profile=Profile.TEST)

        with pytest.raises(AdapterNotFoundError) as exc_info:
            container.resolve(EmailPort)

        error_msg = str(exc_info.value)
        line_count = len(error_msg.strip().split('\n'))
        # 3 lines for diagnostics + 1 optional line for doc URL
        assert line_count <= 4, f'Error message has {line_count} lines, expected <= 4:\n{error_msg}'

    def it_includes_port_name_and_profile(self) -> None:
        """Error message includes port name and active profile on first line."""

        @adapter.for_(EmailPort, profile=Profile.PRODUCTION)
        class SendGridAdapter:
            async def send(self, to: str, subject: str, body: str) -> None:
                pass

        container = Container()
        container.scan(profile=Profile.TEST)

        with pytest.raises(AdapterNotFoundError) as exc_info:
            container.resolve(EmailPort)

        error_msg = str(exc_info.value)
        first_line = error_msg.split('\n')[0]
        assert 'EmailPort' in first_line
        assert 'test' in first_line.lower()

    def it_shows_registered_adapters_for_other_profiles(self) -> None:
        """Second line shows what adapters ARE registered (for other profiles)."""

        @adapter.for_(EmailPort, profile=Profile.PRODUCTION)
        class SendGridAdapter:
            async def send(self, to: str, subject: str, body: str) -> None:
                pass

        container = Container()
        container.scan(profile=Profile.TEST)

        with pytest.raises(AdapterNotFoundError) as exc_info:
            container.resolve(EmailPort)

        error_msg = str(exc_info.value)
        # Should show registered adapters
        assert 'SendGridAdapter' in error_msg
        assert 'production' in error_msg.lower()

    def it_does_not_include_code_examples(self) -> None:
        """Error message does NOT include code examples or hints."""

        @adapter.for_(EmailPort, profile=Profile.PRODUCTION)
        class SendGridAdapter:
            async def send(self, to: str, subject: str, body: str) -> None:
                pass

        container = Container()
        container.scan(profile=Profile.TEST)

        with pytest.raises(AdapterNotFoundError) as exc_info:
            container.resolve(EmailPort)

        error_msg = str(exc_info.value)
        # Should NOT have code examples or verbose hints
        assert '@adapter.for_' not in error_msg
        assert 'class YourAdapter' not in error_msg
        assert 'Hint:' not in error_msg


class DescribeTerseServiceNotFoundError:
    """Tests for terse ServiceNotFoundError messages."""

    def it_produces_message_under_5_lines(self) -> None:
        """Error message is 1-4 lines maximum (3 diagnostic + 1 doc URL)."""

        @service
        class UserService:
            def __init__(self, db: DatabasePort):
                self.db = db

        container = Container()
        container.scan(profile=Profile.TEST)

        with pytest.raises(ServiceNotFoundError) as exc_info:
            container.resolve(UserService)

        error_msg = str(exc_info.value)
        line_count = len(error_msg.strip().split('\n'))
        # 3 lines for diagnostics + 1 optional line for doc URL
        assert line_count <= 4, f'Error message has {line_count} lines, expected <= 4:\n{error_msg}'

    def it_includes_service_name_and_missing_dependency(self) -> None:
        """Error message includes service name and what dependency is missing."""

        @service
        class UserService:
            def __init__(self, db: DatabasePort):
                self.db = db

        container = Container()
        container.scan(profile=Profile.TEST)

        with pytest.raises(ServiceNotFoundError) as exc_info:
            container.resolve(UserService)

        error_msg = str(exc_info.value)
        assert 'UserService' in error_msg
        assert 'DatabasePort' in error_msg

    def it_includes_profile_context(self) -> None:
        """Error message includes the active profile."""

        @service
        class OrderService:
            def __init__(self, email: EmailPort):
                self.email = email

        container = Container()
        container.scan(profile=Profile.PRODUCTION)

        with pytest.raises(ServiceNotFoundError) as exc_info:
            container.resolve(OrderService)

        error_msg = str(exc_info.value)
        assert 'production' in error_msg.lower()

    def it_does_not_include_code_examples_for_unregistered(self) -> None:
        """Error message does NOT include code examples for unregistered services."""

        class UnregisteredService:
            pass

        container = Container()
        container.scan(profile=Profile.TEST)

        with pytest.raises(ServiceNotFoundError) as exc_info:
            container.resolve(UnregisteredService)

        error_msg = str(exc_info.value)
        # Should NOT have multi-line code examples
        assert 'class UnregisteredService' not in error_msg
        assert 'Hint:' not in error_msg
        # Can mention @service briefly but not as code block
        assert '  @service' not in error_msg  # No indented code example


class DescribeTerseCircularDependencyError:
    """Tests for terse CircularDependencyError messages.

    Note: Circular dependencies in @lifecycle components are caught during resolution,
    raising ServiceNotFoundError rather than CircularDependencyError. The
    CircularDependencyError is raised during topological sorting in
    _build_lifecycle_dependency_order() but this is effectively a dead code path
    since resolution catches cycles first.

    These tests verify the terse format of the error message by testing the
    ServiceNotFoundError that gets raised for circular dependencies.
    """

    def it_produces_terse_message_for_circular_dependency(self) -> None:
        """Error message for circular dependency is terse (1-4 lines)."""
        # Module-level classes: _TerseTestCircularA <-> _TerseTestCircularB
        container = Container()
        container.scan()

        # Circular deps raise ServiceNotFoundError during resolution
        with pytest.raises(ServiceNotFoundError) as exc_info:
            container.resolve(_TerseTestCircularA)

        error_msg = str(exc_info.value)
        line_count = len(error_msg.strip().split('\n'))
        # 3 lines for diagnostics + 1 optional line for doc URL
        assert line_count <= 4, f'Error message has {line_count} lines, expected <= 4:\n{error_msg}'

    def it_mentions_component_in_cycle(self) -> None:
        """Error message mentions the component that couldn't be resolved."""
        container = Container()
        container.scan()

        with pytest.raises(ServiceNotFoundError) as exc_info:
            container.resolve(_TerseTestCircularA)

        error_msg = str(exc_info.value)
        assert '_TerseTestCircularA' in error_msg or '_TerseTestCircularB' in error_msg


class DescribeTerseScopeError:
    """Tests for terse ScopeError messages."""

    def it_produces_message_under_5_lines_for_request_scope(self) -> None:
        """Error message is 1-4 lines maximum for REQUEST scope violations."""

        @service(scope=Scope.REQUEST)
        class RequestContext:
            pass

        container = Container()
        container.scan(profile=Profile.TEST)

        with pytest.raises(ScopeError) as exc_info:
            container.resolve(RequestContext)

        error_msg = str(exc_info.value)
        line_count = len(error_msg.strip().split('\n'))
        # 3 lines for diagnostics + 1 optional line for doc URL
        assert line_count <= 4, f'Error message has {line_count} lines, expected <= 4:\n{error_msg}'

    def it_mentions_component_and_scope_requirement(self) -> None:
        """Error message mentions the component and that it requires a scope."""

        @service(scope=Scope.REQUEST)
        class RequestData:
            pass

        container = Container()
        container.scan(profile=Profile.TEST)

        with pytest.raises(ScopeError) as exc_info:
            container.resolve(RequestData)

        error_msg = str(exc_info.value)
        assert 'RequestData' in error_msg
        assert 'REQUEST' in error_msg or 'scope' in error_msg.lower()

    def it_does_not_include_code_examples(self) -> None:
        """Error message does NOT include code examples."""

        @service(scope=Scope.REQUEST)
        class ScopedComponent:
            pass

        container = Container()
        container.scan(profile=Profile.TEST)

        with pytest.raises(ScopeError) as exc_info:
            container.resolve(ScopedComponent)

        error_msg = str(exc_info.value)
        assert 'async with' not in error_msg
        assert 'Hint:' not in error_msg

    @pytest.mark.asyncio
    async def it_produces_terse_message_for_nested_scopes(self) -> None:
        """Error message for nested scope attempt is terse."""
        container = Container()
        container.scan(profile=Profile.TEST)

        # ScopedContainer.create_scope() raises ScopeError for nested scopes
        async with container.create_scope() as scope:
            with pytest.raises(ScopeError) as exc_info:
                scope.create_scope()

            error_msg = str(exc_info.value)
            line_count = len(error_msg.strip().split('\n'))
            # 3 lines for diagnostics + 1 optional line for doc URL
            assert line_count <= 4, f'Error message has {line_count} lines, expected <= 4:\n{error_msg}'


class DescribeTerseCaptiveDependencyError:
    """Tests for terse CaptiveDependencyError messages."""

    def it_produces_message_under_5_lines(self) -> None:
        """Error message is 1-4 lines maximum (3 diagnostic + 1 doc URL)."""

        @service(scope=Scope.REQUEST)
        class RequestCtx:
            pass

        @service  # SINGLETON by default
        class GlobalService:
            def __init__(self, ctx: RequestCtx):
                self.ctx = ctx

        container = Container()

        with pytest.raises(CaptiveDependencyError) as exc_info:
            container.scan(profile=Profile.TEST)

        error_msg = str(exc_info.value)
        line_count = len(error_msg.strip().split('\n'))
        # 3 lines for diagnostics + 1 optional line for doc URL
        assert line_count <= 4, f'Error message has {line_count} lines, expected <= 4:\n{error_msg}'

    def it_names_both_components_and_their_scopes(self) -> None:
        """Error message names parent (SINGLETON) and child (REQUEST) components."""

        @service(scope=Scope.REQUEST)
        class ReqCtx:
            pass

        @service  # SINGLETON
        class SingletonSvc:
            def __init__(self, ctx: ReqCtx):
                self.ctx = ctx

        container = Container()

        with pytest.raises(CaptiveDependencyError) as exc_info:
            container.scan(profile=Profile.TEST)

        error_msg = str(exc_info.value)
        assert 'SingletonSvc' in error_msg
        assert 'ReqCtx' in error_msg
        assert 'SINGLETON' in error_msg
        assert 'REQUEST' in error_msg

    def it_does_not_include_solution_examples(self) -> None:
        """Error message does NOT include solution code examples."""

        @service(scope=Scope.REQUEST)
        class ReqScope:
            pass

        @service
        class CaptiveParent:
            def __init__(self, req: ReqScope):
                self.req = req

        container = Container()

        with pytest.raises(CaptiveDependencyError) as exc_info:
            container.scan(profile=Profile.TEST)

        error_msg = str(exc_info.value)
        assert 'Solutions:' not in error_msg
        assert '@service(scope=Scope.REQUEST)' not in error_msg
        assert 'factory/provider' not in error_msg.lower()
