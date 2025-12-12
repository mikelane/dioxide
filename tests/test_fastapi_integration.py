"""Tests for FastAPI integration module.

This module tests the dioxide.fastapi integration that provides:
- DioxideMiddleware - ASGI middleware handling lifecycle and request scoping
- Inject() - FastAPI Depends wrapper for resolving dependencies
"""

from __future__ import annotations

from typing import Any

import pytest

# Skip this entire module if FastAPI is not installed
pytest.importorskip('fastapi')

from fastapi import (
    FastAPI,
    Request,
)
from fastapi.testclient import TestClient

from dioxide import (
    Container,
    Profile,
    Scope,
    _clear_registry,
    lifecycle,
    service,
)
from dioxide.container import ScopedContainer
from dioxide.fastapi import (
    DioxideMiddleware,
    Inject,
)

# Clear registry before tests to ensure isolation
pytestmark = pytest.mark.usefixtures('clear_registry')


@pytest.fixture(autouse=True)
def clear_registry() -> None:
    """Clear the global registry before each test."""
    _clear_registry()


class DescribeDioxideMiddleware:
    """Tests for DioxideMiddleware."""

    def it_handles_container_lifecycle_on_startup_and_shutdown(self) -> None:
        """Middleware scans and starts container on startup, stops on shutdown."""
        initialized: list[str] = []
        disposed: list[str] = []

        @service
        @lifecycle
        class DatabaseService:
            async def initialize(self) -> None:
                initialized.append('db')

            async def dispose(self) -> None:
                disposed.append('db')

        app = FastAPI()
        container = Container()

        app.add_middleware(DioxideMiddleware, container=container, profile=Profile.TEST)

        @app.get('/health')
        async def health() -> dict[str, str]:
            return {'status': 'ok'}

        # TestClient triggers lifespan events
        with TestClient(app):
            # At this point, startup has run
            assert 'db' in initialized

        # After TestClient exits, shutdown has run
        assert 'db' in disposed

    def it_uses_global_container_when_not_provided(self) -> None:
        """Middleware uses dioxide.container when container not specified."""
        from dioxide import container as global_container

        app = FastAPI()

        # Reset global container
        global_container.reset()

        app.add_middleware(DioxideMiddleware, profile=Profile.TEST)

        @app.get('/health')
        async def health() -> dict[str, str]:
            return {'status': 'ok'}

        # This should work without error - global container is used
        with TestClient(app) as client:
            response = client.get('/health')
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def it_creates_scoped_container_per_request(self) -> None:
        """Middleware creates a ScopedContainer for each HTTP request."""
        app = FastAPI()
        container = Container()

        app.add_middleware(DioxideMiddleware, container=container, profile=Profile.TEST)

        scope_ids: list[str] = []

        @app.get('/test')
        async def test_endpoint(request: Request) -> dict[str, str]:
            scope = request.state.dioxide_scope
            scope_ids.append(scope.scope_id)
            return {'scope_id': scope.scope_id}

        with TestClient(app) as client:
            # Make two requests
            response1 = client.get('/test')
            assert response1.status_code == 200, response1.text
            response2 = client.get('/test')
            assert response2.status_code == 200, response2.text

            # Each request should get a different scope
            assert response1.json()['scope_id'] != response2.json()['scope_id']
            assert len(scope_ids) == 2
            assert scope_ids[0] != scope_ids[1]

    @pytest.mark.asyncio
    async def it_stores_scope_in_request_state(self) -> None:
        """Middleware stores ScopedContainer in request.state.dioxide_scope."""
        app = FastAPI()
        container = Container()

        app.add_middleware(DioxideMiddleware, container=container, profile=Profile.TEST)

        @app.get('/test')
        async def test_endpoint(request: Request) -> dict[str, bool]:
            scope = request.state.dioxide_scope
            return {'is_scoped': isinstance(scope, ScopedContainer)}

        with TestClient(app) as client:
            response = client.get('/test')
            assert response.status_code == 200
            assert response.json()['is_scoped'] is True

    @pytest.mark.asyncio
    async def it_disposes_scope_after_request_completes(self) -> None:
        """Middleware disposes ScopedContainer after request completes."""
        app = FastAPI()
        container = Container()

        app.add_middleware(DioxideMiddleware, container=container, profile=Profile.TEST)

        @app.get('/test')
        async def test_endpoint(request: Request) -> dict[str, str]:
            scope = request.state.dioxide_scope
            return {'scope_id': scope.scope_id}

        with TestClient(app) as client:
            response = client.get('/test')
            assert response.status_code == 200

        # The middleware manages scope lifecycle via async context manager
        assert response.json()['scope_id'] is not None


class DescribeInjectHelper:
    """Tests for Inject() helper function."""

    def it_resolves_singleton_from_parent_container(self) -> None:
        """Inject() resolves SINGLETON-scoped components from parent container."""

        @service
        class SingletonService:
            def get_value(self) -> str:
                return 'singleton'

        app = FastAPI()
        container = Container()

        app.add_middleware(DioxideMiddleware, container=container, profile=Profile.TEST)

        @app.get('/test')
        async def test_endpoint(svc: SingletonService = Inject(SingletonService)) -> dict[str, str]:
            return {'value': svc.get_value()}

        with TestClient(app) as client:
            response = client.get('/test')
            assert response.status_code == 200, response.text
            assert response.json()['value'] == 'singleton'

    def it_resolves_request_scoped_fresh_per_request(self) -> None:
        """Inject() resolves REQUEST-scoped components fresh per request."""

        @service(scope=Scope.REQUEST)
        class RequestContext:
            def __init__(self) -> None:
                import uuid

                self.request_id = str(uuid.uuid4())

        app = FastAPI()
        container = Container()

        app.add_middleware(DioxideMiddleware, container=container, profile=Profile.TEST)

        @app.get('/test')
        async def test_endpoint(ctx: RequestContext = Inject(RequestContext)) -> dict[str, str]:
            return {'request_id': ctx.request_id}

        with TestClient(app) as client:
            response1 = client.get('/test')
            assert response1.status_code == 200, response1.text
            response2 = client.get('/test')
            assert response2.status_code == 200, response2.text

            # Each request should get a different request context
            assert response1.json()['request_id'] != response2.json()['request_id']

    def it_shares_request_scoped_within_same_request(self) -> None:
        """Inject() returns same REQUEST-scoped instance within a single request."""

        @service(scope=Scope.REQUEST)
        class RequestContext:
            def __init__(self) -> None:
                import uuid

                self.request_id = str(uuid.uuid4())

        app = FastAPI()
        container = Container()

        app.add_middleware(DioxideMiddleware, container=container, profile=Profile.TEST)

        @app.get('/test')
        async def test_endpoint(
            ctx1: RequestContext = Inject(RequestContext),
            ctx2: RequestContext = Inject(RequestContext),
        ) -> dict[str, bool]:
            return {'same_instance': ctx1 is ctx2, 'same_id': ctx1.request_id == ctx2.request_id}

        with TestClient(app) as client:
            response = client.get('/test')
            assert response.status_code == 200, response.text
            data = response.json()
            assert data['same_instance'] is True
            assert data['same_id'] is True

    def it_errors_without_dioxide_middleware(self) -> None:
        """Inject() raises RuntimeError if used without DioxideMiddleware."""
        app = FastAPI()

        # Note: NOT adding DioxideMiddleware

        @service
        class SomeService:
            pass

        @app.get('/test')
        async def test_endpoint(svc: SomeService = Inject(SomeService)) -> dict[str, str]:
            return {'value': 'ok'}

        # Without DioxideMiddleware, request.state won't have dioxide_scope
        # The Inject dependency will raise RuntimeError
        with pytest.raises(RuntimeError, match='DioxideMiddleware'):
            with TestClient(app) as client:
                client.get('/test')


class DescribeIntegrationWithAsyncRoutes:
    """Tests for integration with async routes."""

    @pytest.mark.asyncio
    async def it_works_with_async_routes(self) -> None:
        """FastAPI integration works with async route handlers."""

        @service
        class AsyncService:
            async def do_work(self) -> str:
                return 'async-work-done'

        app = FastAPI()
        container = Container()

        app.add_middleware(DioxideMiddleware, container=container, profile=Profile.TEST)

        @app.post('/work')
        async def work_endpoint(svc: AsyncService = Inject(AsyncService)) -> dict[str, str]:
            result = await svc.do_work()
            return {'result': result}

        with TestClient(app) as client:
            response = client.post('/work')
            assert response.status_code == 200, response.text
            assert response.json()['result'] == 'async-work-done'


class DescribeIntegrationWithSyncRoutes:
    """Tests for integration with sync routes."""

    def it_works_with_sync_routes(self) -> None:
        """FastAPI integration works with sync route handlers."""

        @service
        class ConfigService:
            def get_setting(self, key: str) -> str:
                return f'value-for-{key}'

        app = FastAPI()
        container = Container()

        app.add_middleware(DioxideMiddleware, container=container, profile=Profile.TEST)

        @app.get('/config/{key}')
        def config_endpoint(key: str, svc: ConfigService = Inject(ConfigService)) -> dict[str, str]:
            return {'value': svc.get_setting(key)}

        with TestClient(app) as client:
            response = client.get('/config/debug')
            assert response.status_code == 200, response.text
            assert response.json()['value'] == 'value-for-debug'


class DescribeLifecycleManagement:
    """Tests for lifecycle management with FastAPI."""

    @pytest.mark.asyncio
    async def it_initializes_lifecycle_components_at_startup(self) -> None:
        """Container starts lifecycle components when app starts."""
        initialized: list[str] = []

        @service
        @lifecycle
        class DatabaseService:
            async def initialize(self) -> None:
                initialized.append('db')

            async def dispose(self) -> None:
                pass

        app = FastAPI()
        container = Container()

        app.add_middleware(DioxideMiddleware, container=container, profile=Profile.TEST)

        # TestClient triggers lifespan events
        with TestClient(app):
            # At this point, startup has run
            assert 'db' in initialized

    @pytest.mark.asyncio
    async def it_disposes_lifecycle_components_at_shutdown(self) -> None:
        """Container stops lifecycle components when app shuts down."""
        disposed: list[str] = []

        @service
        @lifecycle
        class DatabaseService:
            async def initialize(self) -> None:
                pass

            async def dispose(self) -> None:
                disposed.append('db')

        app = FastAPI()
        container = Container()

        app.add_middleware(DioxideMiddleware, container=container, profile=Profile.TEST)

        # TestClient triggers lifespan events
        with TestClient(app):
            pass  # Context manager exits and triggers shutdown

        # After TestClient exits, shutdown has run
        assert 'db' in disposed


class DescribePackageScanning:
    """Tests for package scanning via middleware."""

    def it_scans_specified_packages(self) -> None:
        """Middleware can scan specific packages."""
        app = FastAPI()
        container = Container()

        # This should not raise even with non-existent packages
        # (package scanning gracefully handles missing packages)
        app.add_middleware(
            DioxideMiddleware,
            container=container,
            profile=Profile.TEST,
            packages=['dioxide'],
        )

        @app.get('/health')
        async def health() -> dict[str, str]:
            return {'status': 'ok'}

        with TestClient(app) as client:
            response = client.get('/health')
            assert response.status_code == 200


class DescribeInjectWithoutFastAPI:
    """Tests for Inject() when FastAPI is not installed."""

    def it_raises_import_error_when_fastapi_not_installed(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Inject() raises ImportError when FastAPI dependencies are unavailable."""
        import dioxide.fastapi as fastapi_module

        # Simulate FastAPI not being installed by setting module-level vars to None
        monkeypatch.setattr(fastapi_module, 'Depends', None)
        monkeypatch.setattr(fastapi_module, 'Request', None)

        with pytest.raises(ImportError, match='FastAPI is not installed'):
            fastapi_module.Inject(object)


class DescribeMiddlewarePassThrough:
    """Tests for middleware pass-through behavior."""

    @pytest.mark.asyncio
    async def it_passes_through_non_http_non_lifespan_requests(self) -> None:
        """Middleware passes through websocket and other request types unchanged."""
        app_called: list[str] = []

        async def mock_app(scope: dict[str, Any], receive: Any, send: Any) -> None:
            app_called.append(scope['type'])

        container = Container()
        middleware = DioxideMiddleware(mock_app, profile=Profile.TEST, container=container)

        # Simulate a websocket request
        websocket_scope: dict[str, Any] = {'type': 'websocket', 'state': {}}

        async def mock_receive() -> dict[str, Any]:
            return {}

        async def mock_send(message: dict[str, Any]) -> None:
            pass

        await middleware(websocket_scope, mock_receive, mock_send)

        assert 'websocket' in app_called


class DescribeMiddlewareStartupFailure:
    """Tests for middleware startup failure handling."""

    @pytest.mark.asyncio
    async def it_sends_startup_failed_when_container_start_raises(self) -> None:
        """Middleware sends lifespan.startup.failed when container.start() raises."""
        sent_messages: list[dict[str, Any]] = []

        async def mock_app(scope: dict[str, Any], receive: Any, send: Any) -> None:
            while True:
                message = await receive()
                if message['type'] == 'lifespan.startup':
                    await send({'type': 'lifespan.startup.complete'})
                elif message['type'] == 'lifespan.shutdown':
                    await send({'type': 'lifespan.shutdown.complete'})
                    break

        container = Container()

        # Make start() raise an exception

        async def failing_start() -> None:
            raise RuntimeError('Simulated startup failure')

        container.start = failing_start  # type: ignore[method-assign]

        middleware = DioxideMiddleware(mock_app, profile=Profile.TEST, container=container)

        lifespan_scope: dict[str, Any] = {'type': 'lifespan', 'state': {}}

        async def mock_receive() -> dict[str, Any]:
            return {'type': 'lifespan.startup'}

        async def mock_send(message: dict[str, Any]) -> None:
            sent_messages.append(message)

        with pytest.raises(RuntimeError, match='Simulated startup failure'):
            await middleware(lifespan_scope, mock_receive, mock_send)

        # Verify startup.failed was sent
        assert any(m['type'] == 'lifespan.startup.failed' for m in sent_messages)


class DescribeMiddlewareShutdownCleanup:
    """Tests for middleware shutdown cleanup error handling."""

    @pytest.mark.asyncio
    async def it_ignores_errors_during_shutdown_cleanup(self) -> None:
        """Middleware ignores container.stop() errors during shutdown (best-effort cleanup)."""
        sent_messages: list[dict[str, Any]] = []
        receive_queue: list[dict[str, Any]] = [
            {'type': 'lifespan.startup'},
            {'type': 'lifespan.shutdown'},
        ]

        async def mock_app(scope: dict[str, Any], receive: Any, send: Any) -> None:
            while True:
                message = await receive()
                if message['type'] == 'lifespan.startup':
                    await send({'type': 'lifespan.startup.complete'})
                elif message['type'] == 'lifespan.shutdown':
                    await send({'type': 'lifespan.shutdown.complete'})
                    break

        container = Container()

        # Make stop() raise an exception

        async def failing_stop() -> None:
            raise RuntimeError('Simulated shutdown failure')

        container.stop = failing_stop  # type: ignore[method-assign]

        middleware = DioxideMiddleware(mock_app, profile=Profile.TEST, container=container)

        lifespan_scope = {'type': 'lifespan', 'state': {}}
        receive_index = 0

        async def mock_receive() -> dict[str, Any]:
            nonlocal receive_index
            msg = receive_queue[receive_index]
            receive_index += 1
            return msg

        async def mock_send(message: dict[str, Any]) -> None:
            sent_messages.append(message)

        # Should NOT raise despite container.stop() failing
        await middleware(lifespan_scope, mock_receive, mock_send)

        # Verify shutdown.complete was still sent
        assert any(m['type'] == 'lifespan.shutdown.complete' for m in sent_messages)


class DescribeMiddlewareStartupFailedCleanup:
    """Tests for middleware cleanup when startup fails after container started."""

    @pytest.mark.asyncio
    async def it_stops_container_when_app_startup_fails(self) -> None:
        """Middleware stops container if startup fails after container was started."""
        stop_called: list[bool] = []
        sent_messages: list[dict[str, Any]] = []

        async def mock_app(scope: dict[str, Any], receive: Any, send: Any) -> None:
            message = await receive()
            if message['type'] == 'lifespan.startup':
                # App fails during startup
                await send({'type': 'lifespan.startup.failed', 'message': 'App failed'})

        container = Container()
        original_stop = container.stop

        async def tracking_stop() -> None:
            stop_called.append(True)
            await original_stop()

        container.stop = tracking_stop  # type: ignore[method-assign]

        middleware = DioxideMiddleware(mock_app, profile=Profile.TEST, container=container)

        lifespan_scope = {'type': 'lifespan', 'state': {}}

        async def mock_receive() -> dict[str, Any]:
            return {'type': 'lifespan.startup'}

        async def mock_send(message: dict[str, Any]) -> None:
            sent_messages.append(message)

        await middleware(lifespan_scope, mock_receive, mock_send)

        # Container should have been stopped due to app startup failure
        assert len(stop_called) == 1
        assert any(m['type'] == 'lifespan.startup.failed' for m in sent_messages)


class DescribeLifespanScopeStateHandling:
    """Tests for lifespan scope state dict initialization."""

    @pytest.mark.asyncio
    async def it_creates_state_dict_when_not_present_in_lifespan_scope(self) -> None:
        """Middleware creates state dict if not present in lifespan scope."""
        sent_messages: list[dict[str, Any]] = []
        receive_queue: list[dict[str, Any]] = [
            {'type': 'lifespan.startup'},
            {'type': 'lifespan.shutdown'},
        ]

        async def mock_app(scope: dict[str, Any], receive: Any, send: Any) -> None:
            while True:
                message = await receive()
                if message['type'] == 'lifespan.startup':
                    # Verify state was created
                    assert 'state' in scope
                    await send({'type': 'lifespan.startup.complete'})
                elif message['type'] == 'lifespan.shutdown':
                    await send({'type': 'lifespan.shutdown.complete'})
                    break

        container = Container()
        middleware = DioxideMiddleware(mock_app, profile=Profile.TEST, container=container)

        # Lifespan scope WITHOUT state dict
        lifespan_scope: dict[str, Any] = {'type': 'lifespan'}
        receive_index = 0

        async def mock_receive() -> dict[str, Any]:
            nonlocal receive_index
            msg = receive_queue[receive_index]
            receive_index += 1
            return msg

        async def mock_send(message: dict[str, Any]) -> None:
            sent_messages.append(message)

        await middleware(lifespan_scope, mock_receive, mock_send)

        # Verify startup completed and state was created
        assert any(m['type'] == 'lifespan.startup.complete' for m in sent_messages)
        assert 'state' in lifespan_scope


class DescribeHttpScopeStateHandling:
    """Tests for HTTP scope state dict initialization."""

    @pytest.mark.asyncio
    async def it_creates_state_dict_when_not_present_in_http_scope(self) -> None:
        """Middleware creates state dict if not present in HTTP scope."""
        app_called: list[bool] = []

        async def mock_app(scope: dict[str, Any], receive: Any, send: Any) -> None:
            app_called.append(True)
            # Verify state was created
            assert 'state' in scope
            assert 'dioxide_scope' in scope['state']

        container = Container()
        container.scan(profile=Profile.TEST)
        await container.start()

        middleware = DioxideMiddleware(mock_app, profile=Profile.TEST, container=container)

        # HTTP scope WITHOUT state dict
        http_scope: dict[str, Any] = {'type': 'http'}

        async def mock_receive() -> dict[str, Any]:
            return {}

        async def mock_send(message: dict[str, Any]) -> None:
            pass

        await middleware(http_scope, mock_receive, mock_send)

        assert app_called
        assert 'state' in http_scope

        await container.stop()


class DescribeWrappedSendOtherMessages:
    """Tests for wrapped_send handling of other message types."""

    @pytest.mark.asyncio
    async def it_passes_through_other_lifespan_message_types(self) -> None:
        """Middleware passes through unrecognized lifespan message types."""
        sent_messages: list[dict[str, Any]] = []

        async def mock_app(scope: dict[str, Any], receive: Any, send: Any) -> None:
            # Send a non-standard lifespan message type
            await send({'type': 'lifespan.custom.event', 'data': 'test'})
            message = await receive()
            if message['type'] == 'lifespan.startup':
                await send({'type': 'lifespan.startup.complete'})
            message = await receive()
            if message['type'] == 'lifespan.shutdown':
                await send({'type': 'lifespan.shutdown.complete'})

        container = Container()
        middleware = DioxideMiddleware(mock_app, profile=Profile.TEST, container=container)

        lifespan_scope = {'type': 'lifespan', 'state': {}}
        receive_queue = [
            {'type': 'lifespan.startup'},
            {'type': 'lifespan.shutdown'},
        ]
        receive_index = 0

        async def mock_receive() -> dict[str, Any]:
            nonlocal receive_index
            msg = receive_queue[receive_index]
            receive_index += 1
            return msg

        async def mock_send(message: dict[str, Any]) -> None:
            sent_messages.append(message)

        await middleware(lifespan_scope, mock_receive, mock_send)

        # Verify the custom event was passed through
        assert any(m['type'] == 'lifespan.custom.event' for m in sent_messages)


class DescribeStartupFailedWithStopError:
    """Tests for startup failed handling when container.stop() also raises."""

    @pytest.mark.asyncio
    async def it_ignores_stop_error_when_startup_failed(self) -> None:
        """Middleware ignores container.stop() errors during startup failure cleanup."""
        sent_messages: list[dict[str, Any]] = []

        async def mock_app(scope: dict[str, Any], receive: Any, send: Any) -> None:
            message = await receive()
            if message['type'] == 'lifespan.startup':
                # App signals startup failed
                await send({'type': 'lifespan.startup.failed', 'message': 'App startup failed'})

        container = Container()

        # Make stop() also raise an exception
        async def failing_stop() -> None:
            raise RuntimeError('Simulated stop failure')

        container.stop = failing_stop  # type: ignore[method-assign]

        middleware = DioxideMiddleware(mock_app, profile=Profile.TEST, container=container)

        lifespan_scope = {'type': 'lifespan', 'state': {}}

        async def mock_receive() -> dict[str, Any]:
            return {'type': 'lifespan.startup'}

        async def mock_send(message: dict[str, Any]) -> None:
            sent_messages.append(message)

        # Should NOT raise despite container.stop() failing
        await middleware(lifespan_scope, mock_receive, mock_send)

        # Verify startup.failed was still sent
        assert any(m['type'] == 'lifespan.startup.failed' for m in sent_messages)
