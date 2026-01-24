"""Tests for rich error message foundation.

This module tests the DioxideError base class and its subclasses that provide
structured, actionable error messages with context, suggestions, and examples.

Issue #343: Better Error Messages API Design
"""

from __future__ import annotations

from dioxide import (
    AdapterNotFoundError,
    CircularDependencyError,
    DioxideError,
    ResolutionError,
    ServiceNotFoundError,
)


class DescribeDioxideError:
    """Tests for the DioxideError base class."""

    def it_has_a_title_attribute(self) -> None:
        """DioxideError has a title attribute for the main error heading."""
        error = DioxideError('Test error')
        assert hasattr(error, 'title')

    def it_has_a_context_attribute(self) -> None:
        """DioxideError has a context dict for error-time state."""
        error = DioxideError('Test error')
        assert hasattr(error, 'context')
        assert isinstance(error.context, dict)

    def it_has_a_suggestions_attribute(self) -> None:
        """DioxideError has a suggestions list for fix recommendations."""
        error = DioxideError('Test error')
        assert hasattr(error, 'suggestions')
        assert isinstance(error.suggestions, list)

    def it_has_an_example_attribute(self) -> None:
        """DioxideError has an optional example code string."""
        error = DioxideError('Test error')
        assert hasattr(error, 'example')
        # Example can be None or a string
        assert error.example is None or isinstance(error.example, str)

    def it_produces_readable_str_output(self) -> None:
        """__str__ produces formatted output with title, context, suggestions, and example."""
        error = DioxideError('No adapter found')
        error.title = 'Resolution Failed'
        error.context = {'profile': 'test', 'requested': 'EmailPort'}
        error.suggestions = ['Check adapter registration', 'Verify profile matches']
        error.example = '@adapter.for_(EmailPort, profile=Profile.TEST)\nclass FakeEmail: ...'

        output = str(error)

        assert 'Resolution Failed' in output
        assert 'No adapter found' in output
        assert 'profile' in output
        assert 'test' in output
        assert 'Check adapter registration' in output
        assert '@adapter.for_' in output


class DescribeResolutionError:
    """Tests for the ResolutionError base class for resolution failures."""

    def it_inherits_from_dioxide_error(self) -> None:
        """ResolutionError is a DioxideError subclass."""
        error = ResolutionError('Cannot resolve type')
        assert isinstance(error, DioxideError)

    def it_has_appropriate_default_title(self) -> None:
        """ResolutionError has a descriptive default title."""
        error = ResolutionError('Cannot resolve type')
        assert 'resolution' in error.title.lower() or 'resolve' in error.title.lower()


class DescribeAdapterNotFoundErrorRich:
    """Tests for the enhanced AdapterNotFoundError with rich formatting."""

    def it_inherits_from_resolution_error(self) -> None:
        """AdapterNotFoundError is a ResolutionError subclass."""
        error = AdapterNotFoundError('No adapter for EmailPort')
        assert isinstance(error, ResolutionError)
        assert isinstance(error, DioxideError)

    def it_has_appropriate_default_title(self) -> None:
        """AdapterNotFoundError has a descriptive default title."""
        error = AdapterNotFoundError('No adapter for EmailPort')
        assert 'adapter' in error.title.lower()


class DescribeServiceNotFoundErrorRich:
    """Tests for the enhanced ServiceNotFoundError with rich formatting."""

    def it_inherits_from_resolution_error(self) -> None:
        """ServiceNotFoundError is a ResolutionError subclass."""
        error = ServiceNotFoundError('Cannot resolve UserService')
        assert isinstance(error, ResolutionError)
        assert isinstance(error, DioxideError)

    def it_has_appropriate_default_title(self) -> None:
        """ServiceNotFoundError has a descriptive default title."""
        error = ServiceNotFoundError('Cannot resolve UserService')
        assert 'service' in error.title.lower()


class DescribeCircularDependencyErrorRich:
    """Tests for the enhanced CircularDependencyError with rich formatting."""

    def it_inherits_from_dioxide_error(self) -> None:
        """CircularDependencyError is a DioxideError subclass."""
        error = CircularDependencyError('Cycle detected')
        assert isinstance(error, DioxideError)

    def it_has_appropriate_default_title(self) -> None:
        """CircularDependencyError has a descriptive default title."""
        error = CircularDependencyError('Cycle detected')
        assert 'circular' in error.title.lower() or 'cycle' in error.title.lower()


class DescribeContextBuilder:
    """Tests for programmatic context building."""

    def it_supports_with_context_method(self) -> None:
        """Errors can be created with context via with_context()."""
        error = DioxideError('Test error').with_context(profile='test', requested='EmailPort')
        assert error.context['profile'] == 'test'
        assert error.context['requested'] == 'EmailPort'

    def it_supports_with_suggestion_method(self) -> None:
        """Errors can have suggestions added via with_suggestion()."""
        error = DioxideError('Test error').with_suggestion('Check your adapter registration')
        assert 'Check your adapter registration' in error.suggestions

    def it_supports_with_example_method(self) -> None:
        """Errors can have example code added via with_example()."""
        code = '@adapter.for_(EmailPort)\nclass FakeEmail: ...'
        error = DioxideError('Test error').with_example(code)
        assert error.example == code

    def it_supports_chained_builder_calls(self) -> None:
        """Builder methods can be chained for fluent API."""
        error = (
            DioxideError('No adapter found')
            .with_context(profile='test', port='EmailPort')
            .with_suggestion('Register an adapter')
            .with_suggestion('Check profile matches')
            .with_example('@adapter.for_(EmailPort)')
        )
        assert error.context['profile'] == 'test'
        assert len(error.suggestions) == 2
        assert error.example is not None


class DescribeExceptionHierarchy:
    """Tests for the complete exception hierarchy."""

    def it_has_correct_inheritance_chain(self) -> None:
        """All resolution errors inherit through the proper chain."""
        # AdapterNotFoundError -> ResolutionError -> DioxideError -> Exception
        adapter_error = AdapterNotFoundError('test')
        assert isinstance(adapter_error, ResolutionError)
        assert isinstance(adapter_error, DioxideError)
        assert isinstance(adapter_error, Exception)

        # ServiceNotFoundError -> ResolutionError -> DioxideError -> Exception
        service_error = ServiceNotFoundError('test')
        assert isinstance(service_error, ResolutionError)
        assert isinstance(service_error, DioxideError)
        assert isinstance(service_error, Exception)

        # CircularDependencyError -> DioxideError -> Exception
        circular_error = CircularDependencyError('test')
        assert isinstance(circular_error, DioxideError)
        assert isinstance(circular_error, Exception)

    def it_preserves_subclass_types_with_builder_methods(self) -> None:
        """Builder methods preserve the subclass type."""
        error = AdapterNotFoundError('No adapter').with_context(profile='test')
        assert isinstance(error, AdapterNotFoundError)
        assert error.title == 'Adapter Not Found'
