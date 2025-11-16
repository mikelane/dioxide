"""Tests for deprecation warnings in old API decorators.

This module tests that the old @component, @component.factory, and
@component.implements APIs emit proper DeprecationWarnings to guide
users toward the new hexagonal architecture API (@service and @adapter.for_()).
"""

import warnings
from typing import Protocol

from dioxide import (
    Scope,
    component,
)


class DescribeComponentDeprecation:
    """Tests for @component decorator deprecation warnings."""

    def it_emits_deprecation_warning_for_basic_component(self) -> None:
        """@component emits DeprecationWarning with migration guidance."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter('always')

            @component
            class TestService:
                pass

            # Should emit exactly one warning
            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)

            # Warning message should guide migration
            message = str(w[0].message)
            assert '@component is deprecated' in message
            assert '@service' in message or '@adapter.for_()' in message
            assert 'MIGRATION.md' in message

    def it_emits_deprecation_warning_for_component_with_scope(self) -> None:
        """@component(scope=...) emits DeprecationWarning."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter('always')

            @component(scope=Scope.SINGLETON)
            class TestService:
                pass

            # Should emit exactly one warning
            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
            assert '@component is deprecated' in str(w[0].message)


class DescribeComponentFactoryDeprecation:
    """Tests for @component.factory decorator deprecation warnings."""

    def it_emits_deprecation_warning_for_factory(self) -> None:
        """@component.factory emits DeprecationWarning."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter('always')

            @component.factory
            class RequestHandler:
                pass

            # Should emit exactly one warning
            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)

            # Warning message should guide migration
            message = str(w[0].message)
            assert '@component.factory is deprecated' in message
            assert '@service' in message or '@adapter.for_()' in message
            assert 'MIGRATION.md' in message


class DescribeComponentImplementsDeprecation:
    """Tests for @component.implements() decorator deprecation warnings."""

    def it_emits_deprecation_warning_for_implements(self) -> None:
        """@component.implements(Protocol) emits DeprecationWarning."""

        # Define a test protocol
        class EmailProvider(Protocol):
            async def send(self, to: str, subject: str, body: str) -> None: ...

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter('always')

            @component.implements(EmailProvider)
            class SendGridEmail:
                async def send(self, to: str, subject: str, body: str) -> None:
                    pass

            # Should emit exactly one warning
            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)

            # Warning message should guide migration
            message = str(w[0].message)
            assert '@component.implements' in message
            assert 'deprecated' in message
            assert '@adapter.for_' in message  # Match actual message format
            assert 'MIGRATION.md' in message


class DescribeWarningStackLevel:
    """Tests that warnings point to user code, not decorator internals."""

    def it_uses_correct_stack_level_for_component(self) -> None:
        """Warning stacklevel points to user's @component line, not decorator."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter('always')

            @component
            class TestService:
                pass

            # Check that warning was emitted
            assert len(w) == 1

            # The filename should be this test file, not decorators.py
            # (stacklevel=2 makes warning point to caller, not decorator)
            assert 'test_deprecation.py' in w[0].filename

    def it_uses_correct_stack_level_for_factory(self) -> None:
        """Warning stacklevel points to user's @component.factory line."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter('always')

            @component.factory
            class TestHandler:
                pass

            assert len(w) == 1
            assert 'test_deprecation.py' in w[0].filename

    def it_uses_correct_stack_level_for_implements(self) -> None:
        """Warning stacklevel points to user's @component.implements line."""

        class TestPort(Protocol):
            def method(self) -> None: ...

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter('always')

            @component.implements(TestPort)
            class TestAdapter:
                def method(self) -> None:
                    pass

            assert len(w) == 1
            assert 'test_deprecation.py' in w[0].filename
