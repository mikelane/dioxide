"""Tests for documentation URL formatting in exception messages.

Issue #396: Error Documentation Links + Doc Cleanup

This module verifies that all dioxide exceptions include documentation URLs
in their string representation, pointing to the appropriate troubleshooting pages.
"""

from __future__ import annotations

from typing import Protocol

import pytest

from dioxide import (
    Container,
    Profile,
    service,
)
from dioxide.exceptions import (
    DOCS_BASE_URL,
    AdapterNotFoundError,
    CaptiveDependencyError,
    CircularDependencyError,
    DioxideError,
    ResolutionError,
    ScopeError,
    ServiceNotFoundError,
)
from dioxide.scope import Scope


class EmailPort(Protocol):
    """Test protocol for email adapters."""

    async def send(self, to: str, subject: str, body: str) -> None:
        """Send an email message."""
        ...


class DescribeDocsBaseUrl:
    """Tests for the DOCS_BASE_URL constant."""

    def it_is_stable_readthedocs_url(self) -> None:
        """Base URL points to stable ReadTheDocs documentation."""
        assert DOCS_BASE_URL == 'https://dioxide.readthedocs.io/en/stable'


class DescribeDioxideErrorDocsUrl:
    """Tests for DioxideError documentation URL."""

    def it_has_class_level_docs_url(self) -> None:
        """DioxideError has a docs_url class attribute."""
        assert hasattr(DioxideError, 'docs_url')
        assert DioxideError.docs_url is not None

    def it_docs_url_points_to_troubleshooting_index(self) -> None:
        """Base class docs_url points to troubleshooting index."""
        assert DioxideError.docs_url == f'{DOCS_BASE_URL}/troubleshooting/'

    def it_includes_docs_url_in_str_output(self) -> None:
        """String representation includes documentation URL."""
        error = DioxideError('Something went wrong')
        msg = str(error)
        assert '-> See:' in msg
        assert 'https://dioxide.readthedocs.io' in msg
        assert '/troubleshooting/' in msg


class DescribeAdapterNotFoundErrorDocsUrl:
    """Tests for AdapterNotFoundError documentation URL."""

    def it_has_specific_docs_url(self) -> None:
        """AdapterNotFoundError has a specific troubleshooting URL."""
        assert AdapterNotFoundError.docs_url is not None
        assert 'adapter-not-found.html' in AdapterNotFoundError.docs_url

    def it_includes_docs_url_in_str_output(self) -> None:
        """String representation includes the specific docs URL."""
        error = AdapterNotFoundError(
            port=EmailPort,
            profile='test',
        )
        msg = str(error)
        assert '-> See:' in msg
        assert 'adapter-not-found.html' in msg

    def it_docs_url_is_full_path(self) -> None:
        """Docs URL is a complete path to the page."""
        assert AdapterNotFoundError.docs_url == (f'{DOCS_BASE_URL}/troubleshooting/adapter-not-found.html')


class DescribeServiceNotFoundErrorDocsUrl:
    """Tests for ServiceNotFoundError documentation URL."""

    def it_has_specific_docs_url(self) -> None:
        """ServiceNotFoundError has a specific troubleshooting URL."""
        assert ServiceNotFoundError.docs_url is not None
        assert 'service-not-found.html' in ServiceNotFoundError.docs_url

    def it_includes_docs_url_in_str_output(self) -> None:
        """String representation includes the specific docs URL."""

        class MyService:
            pass

        error = ServiceNotFoundError(
            service=MyService,
            profile='test',
        )
        msg = str(error)
        assert '-> See:' in msg
        assert 'service-not-found.html' in msg


class DescribeScopeErrorDocsUrl:
    """Tests for ScopeError documentation URL."""

    def it_has_specific_docs_url(self) -> None:
        """ScopeError has a specific troubleshooting URL."""
        assert ScopeError.docs_url is not None
        assert 'scope-error.html' in ScopeError.docs_url

    def it_includes_docs_url_in_str_output(self) -> None:
        """String representation includes the specific docs URL."""

        class MyComponent:
            pass

        error = ScopeError(
            component=MyComponent,
            required_scope=Scope.REQUEST,
        )
        msg = str(error)
        assert '-> See:' in msg
        assert 'scope-error.html' in msg


class DescribeCaptiveDependencyErrorDocsUrl:
    """Tests for CaptiveDependencyError documentation URL."""

    def it_has_specific_docs_url(self) -> None:
        """CaptiveDependencyError has a specific troubleshooting URL."""
        assert CaptiveDependencyError.docs_url is not None
        assert 'captive-dependency.html' in CaptiveDependencyError.docs_url

    def it_includes_docs_url_in_str_output(self) -> None:
        """String representation includes the specific docs URL."""

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
        assert '-> See:' in msg
        assert 'captive-dependency.html' in msg


class DescribeCircularDependencyErrorDocsUrl:
    """Tests for CircularDependencyError documentation URL."""

    def it_has_specific_docs_url(self) -> None:
        """CircularDependencyError has a specific troubleshooting URL."""
        assert CircularDependencyError.docs_url is not None
        assert 'circular-dependency.html' in CircularDependencyError.docs_url

    def it_includes_docs_url_in_str_output(self) -> None:
        """String representation includes the specific docs URL."""
        error = CircularDependencyError('Circular dependency detected')
        msg = str(error)
        assert '-> See:' in msg
        assert 'circular-dependency.html' in msg


class DescribeResolutionErrorDocsUrl:
    """Tests for ResolutionError documentation URL."""

    def it_has_docs_url(self) -> None:
        """ResolutionError has a docs_url class attribute."""
        assert hasattr(ResolutionError, 'docs_url')
        assert ResolutionError.docs_url is not None

    def it_docs_url_points_to_troubleshooting(self) -> None:
        """ResolutionError docs_url points to troubleshooting section."""
        assert ResolutionError.docs_url == f'{DOCS_BASE_URL}/troubleshooting/'


class DescribeDocsUrlInRealContainerErrors:
    """Tests for docs URL appearing in real container error scenarios."""

    def it_appears_in_adapter_not_found_from_container(self) -> None:
        """Docs URL appears when container raises AdapterNotFoundError."""
        container = Container()
        container.scan(profile=Profile.TEST)

        with pytest.raises(AdapterNotFoundError) as exc_info:
            container.resolve(EmailPort)

        msg = str(exc_info.value)
        assert '-> See:' in msg
        assert 'adapter-not-found.html' in msg

    def it_appears_in_service_not_found_from_container(self) -> None:
        """Docs URL appears when container raises ServiceNotFoundError."""

        class UnregisteredService:
            pass

        container = Container()
        container.scan(profile=Profile.TEST)

        with pytest.raises(ServiceNotFoundError) as exc_info:
            container.resolve(UnregisteredService)

        msg = str(exc_info.value)
        assert '-> See:' in msg
        assert 'service-not-found.html' in msg

    def it_appears_in_scope_error_from_container(self) -> None:
        """Docs URL appears when container raises ScopeError."""

        @service(scope=Scope.REQUEST)
        class RequestScoped:
            pass

        container = Container()
        container.scan(profile=Profile.TEST)

        with pytest.raises(ScopeError) as exc_info:
            container.resolve(RequestScoped)

        msg = str(exc_info.value)
        assert '-> See:' in msg
        assert 'scope-error.html' in msg

    def it_appears_in_captive_dependency_from_container(self) -> None:
        """Docs URL appears when container raises CaptiveDependencyError."""

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
        assert '-> See:' in msg
        assert 'captive-dependency.html' in msg
