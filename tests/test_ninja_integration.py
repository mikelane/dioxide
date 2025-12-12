"""Tests for Django Ninja integration module.

This module tests the dioxide.ninja integration that provides:
- configure_dioxide() - Sets up container scanning and starts lifecycle components
- DioxideMiddleware - Django middleware for request scoping
- inject(Type) - Resolves from current request scope
"""

from __future__ import annotations

from typing import Protocol

import pytest

# Skip this entire module if Django or Django Ninja is not installed
pytest.importorskip('django')
pytest.importorskip('ninja')

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
from ninja import NinjaAPI
from ninja.testing import TestClient

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

# Counter for unique API namespaces
_api_counter = 0


def create_api() -> NinjaAPI:
    """Create a NinjaAPI with a unique namespace to avoid conflicts."""
    global _api_counter
    _api_counter += 1
    return NinjaAPI(urls_namespace=f'test-api-{_api_counter}')


@pytest.fixture(autouse=True)
def clear_registry() -> None:
    """Clear the global registry before each test."""
    _clear_registry()
    # Also reset the ninja module state
    import dioxide.ninja as ninja_module

    ninja_module._container = None
    # Clean up any leftover scope from previous tests
    ninja_module._cleanup_scope()


class DescribeConfigureDioxide:
    """Tests for configure_dioxide function."""

    def it_scans_and_starts_container(self) -> None:
        """configure_dioxide scans for components and starts the container."""
        from dioxide.ninja import configure_dioxide

        initialized: list[str] = []

        @service
        @lifecycle
        class DatabaseService:
            async def initialize(self) -> None:
                initialized.append('db')

            async def dispose(self) -> None:
                pass

        api = create_api()
        container = Container()
        configure_dioxide(api, profile=Profile.TEST, container=container)

        assert 'db' in initialized

    def it_uses_global_container_when_not_provided(self) -> None:
        """configure_dioxide uses dioxide.container when container not specified."""
        from dioxide import container as global_container
        from dioxide.ninja import configure_dioxide

        @service
        class SimpleService:
            pass

        # Reset global container
        global_container.reset()

        api = create_api()
        configure_dioxide(api, profile=Profile.TEST)

        # Should not raise - service should be registered
        resolved = global_container.resolve(SimpleService)
        assert resolved is not None

    def it_scans_specified_packages(self) -> None:
        """configure_dioxide can scan specific packages."""
        from dioxide.ninja import configure_dioxide

        api = create_api()
        container = Container()

        # This should not raise
        configure_dioxide(
            api,
            profile=Profile.TEST,
            container=container,
            packages=['dioxide'],
        )

    def it_raises_import_error_when_ninja_not_installed(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """configure_dioxide raises ImportError when Django Ninja is unavailable."""
        import dioxide.ninja as ninja_module

        # Simulate Ninja not being installed
        monkeypatch.setattr(ninja_module, 'NinjaAPI', None)

        with pytest.raises(ImportError, match='Django Ninja is not installed'):
            ninja_module.configure_dioxide(None, profile=Profile.TEST)  # type: ignore[arg-type]


class DescribeInjectHelper:
    """Tests for inject() helper function."""

    def it_resolves_singleton_from_container(self) -> None:
        """inject() resolves SINGLETON-scoped components from container."""
        from dioxide.ninja import (
            _cleanup_scope,
            configure_dioxide,
            inject,
        )

        @service
        class SingletonService:
            def get_value(self) -> str:
                return 'singleton'

        api = create_api()
        container = Container()
        configure_dioxide(api, profile=Profile.TEST, container=container)

        @api.get('/test')
        def test_endpoint(request: object) -> dict[str, str]:
            svc = inject(SingletonService)
            return {'value': svc.get_value()}

        # Manually set up scope for test (simulating middleware)
        import dioxide.ninja as ninja_module

        scope_ctx = container.create_scope()
        import asyncio

        scope = asyncio.run(scope_ctx.__aenter__())
        ninja_module._request_scope.scope = scope
        ninja_module._request_scope.scope_ctx = scope_ctx

        try:
            client = TestClient(api)
            response = client.get('/test')

            assert response.status_code == 200
            assert response.json()['value'] == 'singleton'
        finally:
            _cleanup_scope()

    def it_resolves_request_scoped_fresh_per_request(self) -> None:
        """inject() resolves REQUEST-scoped components fresh per request."""
        from dioxide.ninja import (
            _cleanup_scope,
            configure_dioxide,
            inject,
        )

        @service(scope=Scope.REQUEST)
        class RequestContext:
            def __init__(self) -> None:
                import uuid

                self.request_id = str(uuid.uuid4())

        api = create_api()
        container = Container()
        configure_dioxide(api, profile=Profile.TEST, container=container)

        @api.get('/test')
        def test_endpoint(request: object) -> dict[str, str]:
            ctx = inject(RequestContext)
            return {'request_id': ctx.request_id}

        client = TestClient(api)
        import asyncio

        import dioxide.ninja as ninja_module

        # First request
        scope_ctx1 = container.create_scope()
        scope1 = asyncio.run(scope_ctx1.__aenter__())
        ninja_module._request_scope.scope = scope1
        ninja_module._request_scope.scope_ctx = scope_ctx1

        response1 = client.get('/test')
        _cleanup_scope()

        # Second request
        scope_ctx2 = container.create_scope()
        scope2 = asyncio.run(scope_ctx2.__aenter__())
        ninja_module._request_scope.scope = scope2
        ninja_module._request_scope.scope_ctx = scope_ctx2

        response2 = client.get('/test')
        _cleanup_scope()

        # Each request should get a different request context
        assert response1.json()['request_id'] != response2.json()['request_id']

    def it_shares_request_scoped_within_same_request(self) -> None:
        """inject() returns same REQUEST-scoped instance within a single request."""
        from dioxide.ninja import (
            _cleanup_scope,
            configure_dioxide,
            inject,
        )

        @service(scope=Scope.REQUEST)
        class RequestContext:
            def __init__(self) -> None:
                import uuid

                self.request_id = str(uuid.uuid4())

        api = create_api()
        container = Container()
        configure_dioxide(api, profile=Profile.TEST, container=container)

        @api.get('/test')
        def test_endpoint(request: object) -> dict[str, bool]:
            ctx1 = inject(RequestContext)
            ctx2 = inject(RequestContext)
            return {'same_instance': ctx1 is ctx2, 'same_id': ctx1.request_id == ctx2.request_id}

        # Manually set up scope
        import asyncio

        import dioxide.ninja as ninja_module

        scope_ctx = container.create_scope()
        scope = asyncio.run(scope_ctx.__aenter__())
        ninja_module._request_scope.scope = scope
        ninja_module._request_scope.scope_ctx = scope_ctx

        try:
            client = TestClient(api)
            response = client.get('/test')

            data = response.json()
            assert data['same_instance'] is True
            assert data['same_id'] is True
        finally:
            _cleanup_scope()

    def it_resolves_adapter_for_port(self) -> None:
        """inject() resolves the correct adapter for a port."""
        from dioxide.ninja import (
            _cleanup_scope,
            configure_dioxide,
            inject,
        )

        class EmailPort(Protocol):
            def send(self, to: str) -> str: ...

        @adapter.for_(EmailPort, profile=Profile.TEST)
        class FakeEmailAdapter:
            def send(self, to: str) -> str:
                return f'sent to {to}'

        api = create_api()
        container = Container()
        configure_dioxide(api, profile=Profile.TEST, container=container)

        @api.get('/test')
        def test_endpoint(request: object) -> dict[str, str]:
            email = inject(EmailPort)
            return {'result': email.send('test@example.com')}

        # Manually set up scope
        import asyncio

        import dioxide.ninja as ninja_module

        scope_ctx = container.create_scope()
        scope = asyncio.run(scope_ctx.__aenter__())
        ninja_module._request_scope.scope = scope
        ninja_module._request_scope.scope_ctx = scope_ctx

        try:
            client = TestClient(api)
            response = client.get('/test')

            assert response.status_code == 200
            assert response.json()['result'] == 'sent to test@example.com'
        finally:
            _cleanup_scope()

    def it_raises_import_error_when_ninja_not_installed(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """inject() raises ImportError when Django Ninja dependencies are unavailable."""
        import dioxide.ninja as ninja_module

        # Simulate Ninja not being installed
        monkeypatch.setattr(ninja_module, 'NinjaAPI', None)

        with pytest.raises(ImportError, match='Django Ninja is not installed'):
            ninja_module.inject(object)

    def it_raises_runtime_error_when_container_not_configured(self) -> None:
        """inject() raises RuntimeError if called outside request context."""
        import dioxide.ninja as ninja_module
        from dioxide.ninja import configure_dioxide

        # Configure container but don't set up scope
        api = create_api()
        container = Container()

        @service
        class SomeService:
            pass

        configure_dioxide(api, profile=Profile.TEST, container=container)

        # Reset the scope (simulating outside request context)
        ninja_module._request_scope.scope = None

        with pytest.raises(RuntimeError, match='request context'):
            ninja_module.inject(SomeService)


class DescribeRequestScoping:
    """Tests for request scoping behavior."""

    def it_disposes_scope_after_cleanup(self) -> None:
        """Scope is disposed when _cleanup_scope is called."""
        from dioxide.ninja import (
            _cleanup_scope,
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

        api = create_api()
        container = Container()
        configure_dioxide(api, profile=Profile.TEST, container=container)

        @api.get('/test')
        def test_endpoint(request: object) -> dict[str, str]:
            inject(RequestResource)
            return {'status': 'ok'}

        # Manually set up scope
        import asyncio

        import dioxide.ninja as ninja_module

        scope_ctx = container.create_scope()
        scope = asyncio.run(scope_ctx.__aenter__())
        ninja_module._request_scope.scope = scope
        ninja_module._request_scope.scope_ctx = scope_ctx

        client = TestClient(api)
        client.get('/test')
        _cleanup_scope()  # This triggers disposal

        # After cleanup, scope should be disposed
        assert 'resource' in disposed


class DescribeDioxideMiddleware:
    """Tests for DioxideMiddleware class."""

    def it_creates_scope_for_each_request(self) -> None:
        """Middleware creates a ScopedContainer for each request."""
        from django.http import (
            HttpRequest,
            HttpResponse,
        )
        from django.test import RequestFactory

        from dioxide.ninja import (
            DioxideMiddleware,
            configure_dioxide,
            inject,
        )

        @service(scope=Scope.REQUEST)
        class RequestContext:
            def __init__(self) -> None:
                import uuid

                self.request_id = str(uuid.uuid4())

        api = create_api()
        container = Container()
        configure_dioxide(api, profile=Profile.TEST, container=container)

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
        from django.http import (
            HttpRequest,
            HttpResponse,
        )
        from django.test import RequestFactory

        from dioxide.ninja import (
            DioxideMiddleware,
            configure_dioxide,
            inject,
        )

        @service(scope=Scope.REQUEST)
        class RequestContext:
            def __init__(self) -> None:
                import uuid

                self.request_id = str(uuid.uuid4())

        api = create_api()
        container = Container()
        configure_dioxide(api, profile=Profile.TEST, container=container)

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
        from django.http import (
            HttpRequest,
            HttpResponse,
        )
        from django.test import RequestFactory

        from dioxide.ninja import (
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

        api = create_api()
        container = Container()
        configure_dioxide(api, profile=Profile.TEST, container=container)

        def view(request: HttpRequest) -> HttpResponse:
            inject(RequestResource)
            return HttpResponse('ok')

        middleware = DioxideMiddleware(view)

        factory = RequestFactory()
        request = factory.get('/')
        middleware(request)

        # After request completes, scope should be disposed
        assert 'resource' in disposed


class DescribeSyncAndAsyncSupport:
    """Tests for sync and async endpoint support."""

    def it_works_with_sync_endpoints(self) -> None:
        """inject() works with synchronous endpoints."""
        from dioxide.ninja import (
            _cleanup_scope,
            configure_dioxide,
            inject,
        )

        @service
        class ConfigService:
            def get_setting(self, key: str) -> str:
                return f'value-for-{key}'

        api = create_api()
        container = Container()
        configure_dioxide(api, profile=Profile.TEST, container=container)

        @api.get('/config/{key}')
        def config_endpoint(request: object, key: str) -> dict[str, str]:
            svc = inject(ConfigService)
            return {'value': svc.get_setting(key)}

        # Manually set up scope
        import asyncio

        import dioxide.ninja as ninja_module

        scope_ctx = container.create_scope()
        scope = asyncio.run(scope_ctx.__aenter__())
        ninja_module._request_scope.scope = scope
        ninja_module._request_scope.scope_ctx = scope_ctx

        try:
            client = TestClient(api)
            response = client.get('/config/debug')

            assert response.status_code == 200
            assert response.json()['value'] == 'value-for-debug'
        finally:
            _cleanup_scope()

    @pytest.mark.asyncio
    async def it_works_with_async_endpoints(self) -> None:
        """inject() works with async endpoints."""
        from ninja.testing import TestAsyncClient

        from dioxide.ninja import (
            _cleanup_scope,
            inject,
        )

        @service
        class AsyncService:
            async def do_work(self) -> str:
                return 'async-work-done'

        api = create_api()
        container = Container()

        # Scan and start container manually to avoid asyncio.run() conflict
        container.scan(profile=Profile.TEST)
        await container.start()

        # Set module container
        import dioxide.ninja as ninja_module

        ninja_module._container = container

        @api.post('/work')
        async def work_endpoint(request: object) -> dict[str, str]:
            svc = inject(AsyncService)
            result = await svc.do_work()
            return {'result': result}

        # Manually set up scope
        scope_ctx = container.create_scope()
        scope = await scope_ctx.__aenter__()
        ninja_module._request_scope.scope = scope
        ninja_module._request_scope.scope_ctx = scope_ctx

        try:
            client = TestAsyncClient(api)
            response = await client.post('/work')

            assert response.status_code == 200
            assert response.json()['result'] == 'async-work-done'
        finally:
            _cleanup_scope()


class DescribeLifecycleManagement:
    """Tests for lifecycle management with Django Ninja."""

    def it_initializes_lifecycle_components_at_startup(self) -> None:
        """Container starts lifecycle components when configure_dioxide is called."""
        from dioxide.ninja import configure_dioxide

        initialized: list[str] = []

        @service
        @lifecycle
        class DatabaseService:
            async def initialize(self) -> None:
                initialized.append('db')

            async def dispose(self) -> None:
                pass

        api = create_api()
        container = Container()
        configure_dioxide(api, profile=Profile.TEST, container=container)

        assert 'db' in initialized


class DescribeThreadSafety:
    """Tests for thread safety in Django's WSGI mode."""

    def it_creates_separate_scopes_for_concurrent_requests(self) -> None:
        """Each concurrent request gets its own scope (via thread-local storage)."""
        import threading
        from concurrent.futures import (
            ThreadPoolExecutor,
            as_completed,
        )

        from django.http import (
            HttpRequest,
            HttpResponse,
        )
        from django.test import RequestFactory

        from dioxide.ninja import (
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

        api = create_api()
        container = Container()
        configure_dioxide(api, profile=Profile.TEST, container=container)

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


class DescribeErrorHandling:
    """Tests for error handling."""

    def it_cleans_up_scope_on_view_exception(self) -> None:
        """Middleware disposes scope even if view raises an exception."""
        from django.http import (
            HttpRequest,
            HttpResponse,
        )
        from django.test import RequestFactory

        from dioxide.ninja import (
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

        api = create_api()
        container = Container()
        configure_dioxide(api, profile=Profile.TEST, container=container)

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
        from django.http import (
            HttpRequest,
            HttpResponse,
        )
        from django.test import RequestFactory

        import dioxide.ninja as ninja_module
        from dioxide.ninja import DioxideMiddleware

        # Reset the module-level container
        ninja_module._container = None

        def view(request: HttpRequest) -> HttpResponse:
            return HttpResponse('ok')

        middleware = DioxideMiddleware(view)

        factory = RequestFactory()
        request = factory.get('/')

        with pytest.raises(RuntimeError, match='container not configured'):
            middleware(request)


class DescribeImportErrorHandling:
    """Tests for handling missing Django Ninja dependency."""

    def it_raises_import_error_for_inject_when_ninja_not_installed(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """inject() raises ImportError when Django Ninja dependencies are unavailable."""
        import dioxide.ninja as ninja_module

        # Simulate Ninja not being installed
        monkeypatch.setattr(ninja_module, 'NinjaAPI', None)

        with pytest.raises(ImportError, match='Django Ninja is not installed'):
            ninja_module.inject(object)
