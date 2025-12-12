"""Tests for Django integration module.

This module tests the dioxide.django integration that provides:
- configure_dioxide() - Sets up container scanning and starts lifecycle components
- DioxideMiddleware - Django middleware for request scoping
- inject(Type) - Resolves from current request scope using thread-local storage
"""

from __future__ import annotations

from typing import Protocol

import pytest

# Skip this entire module if Django is not installed
pytest.importorskip('django')

import django
from django.conf import settings

# Configure Django settings before importing Django test utilities
if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={},
        INSTALLED_APPS=[
            'django.contrib.contenttypes',
            'django.contrib.auth',
        ],
        ROOT_URLCONF=[],
        DEFAULT_CHARSET='utf-8',
        SECRET_KEY='test-secret-key-for-dioxide-testing',
    )
    django.setup()

import pytest
from django.http import (
    HttpRequest,
    HttpResponse,
)
from django.test import RequestFactory

from dioxide import (
    Container,
    Profile,
    Scope,
    _clear_registry,
    adapter,
    lifecycle,
    service,
)

# Clear registry before tests to ensure isolation
pytestmark = pytest.mark.usefixtures('clear_registry')


@pytest.fixture(autouse=True)
def clear_registry() -> None:
    """Clear the global registry and reset django module state before each test."""
    import dioxide.django as django_module

    _clear_registry()
    # Reset module-level container to ensure test isolation
    django_module._container = None


class DescribeConfigureDioxide:
    """Tests for configure_dioxide function."""

    def it_scans_and_starts_container(self) -> None:
        """configure_dioxide scans for components and starts the container."""
        from dioxide.django import configure_dioxide

        initialized: list[str] = []

        @service
        @lifecycle
        class DatabaseService:
            async def initialize(self) -> None:
                initialized.append('db')

            async def dispose(self) -> None:
                pass

        container = Container()
        configure_dioxide(profile=Profile.TEST, container=container)

        assert 'db' in initialized

    def it_uses_global_container_when_not_provided(self) -> None:
        """configure_dioxide uses dioxide.container when container not specified."""
        from dioxide import container as global_container
        from dioxide.django import configure_dioxide

        @service
        class SimpleService:
            pass

        # Reset global container
        global_container.reset()

        configure_dioxide(profile=Profile.TEST)

        # Should not raise - service should be registered
        resolved = global_container.resolve(SimpleService)
        assert resolved is not None

    def it_scans_specified_packages(self) -> None:
        """configure_dioxide can scan specific packages."""
        from dioxide.django import configure_dioxide

        container = Container()

        # This should not raise
        configure_dioxide(
            profile=Profile.TEST,
            container=container,
            packages=['dioxide'],
        )


class DescribeDioxideMiddleware:
    """Tests for DioxideMiddleware class."""

    def it_creates_scope_for_each_request(self) -> None:
        """Middleware creates a ScopedContainer for each request."""
        from dioxide.django import (
            DioxideMiddleware,
            configure_dioxide,
            inject,
        )

        @service(scope=Scope.REQUEST)
        class RequestContext:
            def __init__(self) -> None:
                import uuid

                self.request_id = str(uuid.uuid4())

        container = Container()
        configure_dioxide(profile=Profile.TEST, container=container)

        request_ids: list[str] = []

        def view(request: HttpRequest) -> HttpResponse:
            ctx = inject(RequestContext)
            request_ids.append(ctx.request_id)
            return HttpResponse('ok')

        middleware = DioxideMiddleware(view)

        factory = RequestFactory()
        request1 = factory.get('/')
        request2 = factory.get('/')

        middleware(request1)
        middleware(request2)

        # Each request should get a different request context
        assert len(request_ids) == 2
        assert request_ids[0] != request_ids[1]

    def it_shares_request_scoped_within_same_request(self) -> None:
        """Middleware provides same REQUEST-scoped instance within single request."""
        from dioxide.django import (
            DioxideMiddleware,
            configure_dioxide,
            inject,
        )

        @service(scope=Scope.REQUEST)
        class RequestContext:
            def __init__(self) -> None:
                import uuid

                self.request_id = str(uuid.uuid4())

        container = Container()
        configure_dioxide(profile=Profile.TEST, container=container)

        same_instance: list[bool] = []

        def view(request: HttpRequest) -> HttpResponse:
            ctx1 = inject(RequestContext)
            ctx2 = inject(RequestContext)
            same_instance.append(ctx1 is ctx2)
            return HttpResponse('ok')

        middleware = DioxideMiddleware(view)

        factory = RequestFactory()
        request = factory.get('/')
        middleware(request)

        assert same_instance[0] is True

    def it_disposes_scope_after_request(self) -> None:
        """Middleware disposes ScopedContainer after request completes."""
        from dioxide.django import (
            DioxideMiddleware,
            configure_dioxide,
            inject,
        )

        disposed: list[str] = []

        @service(scope=Scope.REQUEST)
        @lifecycle
        class RequestResource:
            async def initialize(self) -> None:
                pass

            async def dispose(self) -> None:
                disposed.append('resource')

        container = Container()
        configure_dioxide(profile=Profile.TEST, container=container)

        def view(request: HttpRequest) -> HttpResponse:
            inject(RequestResource)
            return HttpResponse('ok')

        middleware = DioxideMiddleware(view)

        factory = RequestFactory()
        request = factory.get('/')
        middleware(request)

        # After request completes, scope should be disposed
        assert 'resource' in disposed


class DescribeInjectHelper:
    """Tests for inject() helper function."""

    def it_resolves_singleton_from_container(self) -> None:
        """inject() resolves SINGLETON-scoped components from container."""
        from dioxide.django import (
            DioxideMiddleware,
            configure_dioxide,
            inject,
        )

        @service
        class SingletonService:
            def get_value(self) -> str:
                return 'singleton'

        container = Container()
        configure_dioxide(profile=Profile.TEST, container=container)

        result: list[str] = []

        def view(request: HttpRequest) -> HttpResponse:
            svc = inject(SingletonService)
            result.append(svc.get_value())
            return HttpResponse('ok')

        middleware = DioxideMiddleware(view)

        factory = RequestFactory()
        request = factory.get('/')
        middleware(request)

        assert result[0] == 'singleton'

    def it_resolves_adapter_for_port(self) -> None:
        """inject() resolves the correct adapter for a port."""
        from dioxide.django import (
            DioxideMiddleware,
            configure_dioxide,
            inject,
        )

        class EmailPort(Protocol):
            def send(self, to: str) -> str: ...

        @adapter.for_(EmailPort, profile=Profile.TEST)
        class FakeEmailAdapter:
            def send(self, to: str) -> str:
                return f'sent to {to}'

        container = Container()
        configure_dioxide(profile=Profile.TEST, container=container)

        result: list[str] = []

        def view(request: HttpRequest) -> HttpResponse:
            email = inject(EmailPort)
            result.append(email.send('test@example.com'))
            return HttpResponse('ok')

        middleware = DioxideMiddleware(view)

        factory = RequestFactory()
        request = factory.get('/')
        middleware(request)

        assert result[0] == 'sent to test@example.com'

    def it_errors_outside_request_context(self) -> None:
        """inject() raises RuntimeError if used outside request context."""
        from dioxide.django import (
            configure_dioxide,
            inject,
        )

        @service
        class SomeService:
            pass

        container = Container()
        configure_dioxide(profile=Profile.TEST, container=container)

        # Outside request context, inject() should fail
        with pytest.raises(RuntimeError, match='request context'):
            inject(SomeService)


class DescribeThreadSafety:
    """Tests for thread safety in Django's WSGI mode."""

    def it_creates_separate_scopes_for_concurrent_requests(self) -> None:
        """Each concurrent request gets its own scope (via thread-local storage)."""
        import threading
        from concurrent.futures import (
            ThreadPoolExecutor,
            as_completed,
        )

        from dioxide.django import (
            DioxideMiddleware,
            configure_dioxide,
            inject,
        )

        @service(scope=Scope.REQUEST)
        class RequestContext:
            def __init__(self) -> None:
                import uuid

                self.request_id = str(uuid.uuid4())
                self.thread_id = threading.current_thread().ident

        container = Container()
        configure_dioxide(profile=Profile.TEST, container=container)

        results: list[dict[str, str | int | None]] = []
        lock = threading.Lock()

        def view(request: HttpRequest) -> HttpResponse:
            ctx = inject(RequestContext)
            with lock:
                results.append({'request_id': ctx.request_id, 'thread_id': ctx.thread_id})
            return HttpResponse('ok')

        middleware = DioxideMiddleware(view)
        factory = RequestFactory()

        def make_request() -> None:
            request = factory.get('/')
            middleware(request)

        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(make_request) for _ in range(4)]
            for future in as_completed(futures):
                future.result()

        # All request IDs should be unique
        request_ids = [r['request_id'] for r in results]
        assert len(set(request_ids)) == 4


class DescribeImportErrorHandling:
    """Tests for handling missing Django dependency."""

    def it_raises_import_error_when_django_not_installed(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Module raises ImportError when Django dependencies are unavailable."""
        import dioxide.django as django_module

        # Simulate Django not being installed
        monkeypatch.setattr(django_module, 'Django', None)

        with pytest.raises(ImportError, match='Django is not installed'):
            django_module.configure_dioxide(profile=Profile.TEST)

    def it_inject_raises_import_error_when_django_not_installed(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """inject() raises ImportError when Django dependencies are unavailable."""
        import dioxide.django as django_module

        # Simulate Django not being installed
        monkeypatch.setattr(django_module, 'Django', None)

        with pytest.raises(ImportError, match='Django is not installed'):
            django_module.inject(object)


class DescribeMiddlewareErrorHandling:
    """Tests for middleware error handling."""

    def it_cleans_up_scope_on_view_exception(self) -> None:
        """Middleware disposes scope even if view raises an exception."""
        from dioxide.django import (
            DioxideMiddleware,
            configure_dioxide,
            inject,
        )

        disposed: list[str] = []

        @service(scope=Scope.REQUEST)
        @lifecycle
        class RequestResource:
            async def initialize(self) -> None:
                pass

            async def dispose(self) -> None:
                disposed.append('resource')

        container = Container()
        configure_dioxide(profile=Profile.TEST, container=container)

        def failing_view(request: HttpRequest) -> HttpResponse:
            inject(RequestResource)
            raise ValueError('Simulated error')

        middleware = DioxideMiddleware(failing_view)

        factory = RequestFactory()
        request = factory.get('/')

        with pytest.raises(ValueError, match='Simulated error'):
            middleware(request)

        # Scope should still be disposed
        assert 'resource' in disposed

    def it_raises_error_when_container_not_configured(self) -> None:
        """Middleware raises RuntimeError if configure_dioxide was not called."""
        # Reset the module-level container
        import dioxide.django as django_module
        from dioxide.django import DioxideMiddleware

        django_module._container = None

        def view(request: HttpRequest) -> HttpResponse:
            return HttpResponse('ok')

        middleware = DioxideMiddleware(view)

        factory = RequestFactory()
        request = factory.get('/')

        with pytest.raises(RuntimeError, match='container not configured'):
            middleware(request)
