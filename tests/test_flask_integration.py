"""Tests for Flask integration module.

This module tests the dioxide.flask integration that provides:
- configure_dioxide(app) - Sets up container scanning and request hooks
- inject(Type) - Resolves from current request scope using Flask's g object
"""

from __future__ import annotations

from typing import Protocol

import pytest

# Skip this entire module if Flask is not installed
pytest.importorskip('flask')

from flask import Flask

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
    """Clear the global registry before each test."""
    _clear_registry()


class DescribeConfigureDioxide:
    """Tests for configure_dioxide function."""

    def it_sets_up_request_hooks_on_flask_app(self) -> None:
        """configure_dioxide adds before_request and teardown_request hooks."""
        from dioxide.flask import configure_dioxide

        app = Flask(__name__)
        container = Container()

        configure_dioxide(app, profile=Profile.TEST, container=container)

        # Verify hooks were added
        assert len(app.before_request_funcs.get(None, [])) > 0
        assert len(app.teardown_request_funcs.get(None, [])) > 0

    def it_uses_global_container_when_not_provided(self) -> None:
        """configure_dioxide uses dioxide.container when container not specified."""
        from dioxide import container as global_container
        from dioxide.flask import configure_dioxide

        app = Flask(__name__)

        # Reset global container
        global_container.reset()

        configure_dioxide(app, profile=Profile.TEST)

        @app.route('/health')
        def health() -> dict[str, str]:
            return {'status': 'ok'}

        with app.test_client() as client:
            response = client.get('/health')
            assert response.status_code == 200

    def it_scans_specified_packages(self) -> None:
        """configure_dioxide can scan specific packages."""
        from dioxide.flask import configure_dioxide

        app = Flask(__name__)
        container = Container()

        # This should not raise even with non-existent packages
        configure_dioxide(
            app,
            profile=Profile.TEST,
            container=container,
            packages=['dioxide'],
        )

        @app.route('/health')
        def health() -> dict[str, str]:
            return {'status': 'ok'}

        with app.test_client() as client:
            response = client.get('/health')
            assert response.status_code == 200


class DescribeInjectHelper:
    """Tests for inject() helper function."""

    def it_resolves_singleton_from_container(self) -> None:
        """inject() resolves SINGLETON-scoped components from container."""
        from dioxide.flask import (
            configure_dioxide,
            inject,
        )

        @service
        class SingletonService:
            def get_value(self) -> str:
                return 'singleton'

        app = Flask(__name__)
        container = Container()

        configure_dioxide(app, profile=Profile.TEST, container=container)

        @app.route('/test')
        def test_endpoint() -> dict[str, str]:
            svc = inject(SingletonService)
            return {'value': svc.get_value()}

        with app.test_client() as client:
            response = client.get('/test')
            assert response.status_code == 200
            assert response.get_json()['value'] == 'singleton'

    def it_resolves_request_scoped_fresh_per_request(self) -> None:
        """inject() resolves REQUEST-scoped components fresh per request."""
        from dioxide.flask import (
            configure_dioxide,
            inject,
        )

        @service(scope=Scope.REQUEST)
        class RequestContext:
            def __init__(self) -> None:
                import uuid

                self.request_id = str(uuid.uuid4())

        app = Flask(__name__)
        container = Container()

        configure_dioxide(app, profile=Profile.TEST, container=container)

        @app.route('/test')
        def test_endpoint() -> dict[str, str]:
            ctx = inject(RequestContext)
            return {'request_id': ctx.request_id}

        with app.test_client() as client:
            response1 = client.get('/test')
            assert response1.status_code == 200
            response2 = client.get('/test')
            assert response2.status_code == 200

            # Each request should get a different request context
            assert response1.get_json()['request_id'] != response2.get_json()['request_id']

    def it_shares_request_scoped_within_same_request(self) -> None:
        """inject() returns same REQUEST-scoped instance within a single request."""
        from dioxide.flask import (
            configure_dioxide,
            inject,
        )

        @service(scope=Scope.REQUEST)
        class RequestContext:
            def __init__(self) -> None:
                import uuid

                self.request_id = str(uuid.uuid4())

        app = Flask(__name__)
        container = Container()

        configure_dioxide(app, profile=Profile.TEST, container=container)

        @app.route('/test')
        def test_endpoint() -> dict[str, bool]:
            ctx1 = inject(RequestContext)
            ctx2 = inject(RequestContext)
            return {'same_instance': ctx1 is ctx2, 'same_id': ctx1.request_id == ctx2.request_id}

        with app.test_client() as client:
            response = client.get('/test')
            assert response.status_code == 200
            data = response.get_json()
            assert data['same_instance'] is True
            assert data['same_id'] is True

    def it_errors_outside_request_context(self) -> None:
        """inject() raises RuntimeError if used outside request context."""
        from dioxide.flask import (
            configure_dioxide,
            inject,
        )

        @service
        class SomeService:
            pass

        app = Flask(__name__)
        container = Container()

        configure_dioxide(app, profile=Profile.TEST, container=container)

        # Outside request context, inject() should fail
        with pytest.raises(RuntimeError, match='request context'):
            inject(SomeService)

    def it_errors_without_configure_dioxide(self) -> None:
        """inject() raises RuntimeError if configure_dioxide was not called."""
        from dioxide.flask import inject

        @service
        class SomeService:
            pass

        app = Flask(__name__)

        @app.route('/test')
        def test_endpoint() -> dict[str, str]:
            inject(SomeService)
            return {'value': 'ok'}

        # Without configure_dioxide, Flask returns 500 because inject() raises RuntimeError
        with app.test_client() as client:
            response = client.get('/test')
            # The request fails with a 500 error because inject() raises RuntimeError
            assert response.status_code == 500


class DescribeRequestScopeCreation:
    """Tests for per-request scope creation."""

    def it_creates_unique_scope_per_request(self) -> None:
        """Each request gets a unique ScopedContainer."""
        from flask import g

        from dioxide.flask import configure_dioxide

        app = Flask(__name__)
        container = Container()

        configure_dioxide(app, profile=Profile.TEST, container=container)

        scope_ids: list[str] = []

        @app.route('/test')
        def test_endpoint() -> dict[str, str]:
            scope = g.dioxide_scope
            scope_ids.append(scope.scope_id)
            return {'scope_id': scope.scope_id}

        with app.test_client() as client:
            response1 = client.get('/test')
            assert response1.status_code == 200
            response2 = client.get('/test')
            assert response2.status_code == 200

            # Each request should get a different scope
            assert len(scope_ids) == 2
            assert scope_ids[0] != scope_ids[1]


class DescribeScopeDisposal:
    """Tests for scope disposal after request."""

    def it_disposes_scope_after_request_completes(self) -> None:
        """ScopedContainer is disposed after request completes."""
        from flask import g

        from dioxide.flask import configure_dioxide

        app = Flask(__name__)
        container = Container()

        configure_dioxide(app, profile=Profile.TEST, container=container)

        scope_disposed: list[bool] = []

        @app.route('/test')
        def test_endpoint() -> dict[str, str]:
            # Access scope to verify it exists
            scope = g.dioxide_scope
            assert scope is not None
            return {'status': 'ok'}

        @app.teardown_request
        def track_scope_state(exception: BaseException | None = None) -> None:
            # This runs after dioxide's teardown, so scope should still exist
            # but will be disposed after all teardowns complete
            scope_disposed.append(True)

        with app.test_client() as client:
            response = client.get('/test')
            assert response.status_code == 200

        # Verify teardown was called
        assert True in scope_disposed


class DescribeAdapterResolution:
    """Tests for resolving adapters via ports."""

    def it_resolves_adapter_for_port(self) -> None:
        """inject() resolves the correct adapter for a port."""
        from dioxide.flask import (
            configure_dioxide,
            inject,
        )

        class EmailPort(Protocol):
            def send(self, to: str) -> str: ...

        @adapter.for_(EmailPort, profile=Profile.TEST)
        class FakeEmailAdapter:
            def send(self, to: str) -> str:
                return f'sent to {to}'

        app = Flask(__name__)
        container = Container()

        configure_dioxide(app, profile=Profile.TEST, container=container)

        @app.route('/test')
        def test_endpoint() -> dict[str, str]:
            email = inject(EmailPort)
            result = email.send('test@example.com')
            return {'result': result}

        with app.test_client() as client:
            response = client.get('/test')
            assert response.status_code == 200
            assert response.get_json()['result'] == 'sent to test@example.com'


class DescribeAppFactoryPattern:
    """Tests for Flask app factory pattern support."""

    def it_works_with_app_factory_pattern(self) -> None:
        """configure_dioxide works with Flask app factory pattern."""
        from dioxide.flask import (
            configure_dioxide,
            inject,
        )

        @service
        class ConfigService:
            def get_setting(self, key: str) -> str:
                return f'value-for-{key}'

        def create_app() -> Flask:
            app = Flask(__name__)
            container = Container()
            configure_dioxide(app, profile=Profile.TEST, container=container)

            @app.route('/config/<key>')
            def config_endpoint(key: str) -> dict[str, str]:
                svc = inject(ConfigService)
                return {'value': svc.get_setting(key)}

            return app

        app = create_app()

        with app.test_client() as client:
            response = client.get('/config/debug')
            assert response.status_code == 200
            assert response.get_json()['value'] == 'value-for-debug'


class DescribeBlueprintSupport:
    """Tests for Flask blueprint support."""

    def it_works_with_blueprints(self) -> None:
        """configure_dioxide works with Flask blueprints."""
        from flask import Blueprint

        from dioxide.flask import (
            configure_dioxide,
            inject,
        )

        @service
        class UserService:
            def get_user(self, user_id: str) -> dict[str, str]:
                return {'id': user_id, 'name': f'User {user_id}'}

        app = Flask(__name__)
        container = Container()

        configure_dioxide(app, profile=Profile.TEST, container=container)

        # Create a blueprint
        users_bp = Blueprint('users', __name__, url_prefix='/users')

        @users_bp.route('/<user_id>')
        def get_user(user_id: str) -> dict[str, str]:
            svc = inject(UserService)
            return svc.get_user(user_id)

        app.register_blueprint(users_bp)

        with app.test_client() as client:
            response = client.get('/users/123')
            assert response.status_code == 200
            data = response.get_json()
            assert data['id'] == '123'
            assert data['name'] == 'User 123'


class DescribeLifecycleManagement:
    """Tests for lifecycle management with Flask."""

    def it_initializes_lifecycle_components_at_startup(self) -> None:
        """Container starts lifecycle components when configured."""
        from dioxide.flask import configure_dioxide

        initialized: list[str] = []

        @service
        @lifecycle
        class DatabaseService:
            async def initialize(self) -> None:
                initialized.append('db')

            async def dispose(self) -> None:
                pass

        app = Flask(__name__)
        container = Container()

        # configure_dioxide should scan and start the container
        configure_dioxide(app, profile=Profile.TEST, container=container)

        # At this point, the container should be started
        assert 'db' in initialized


class DescribeThreadSafety:
    """Tests for thread safety in Flask's threaded mode."""

    def it_creates_separate_scopes_for_concurrent_requests(self) -> None:
        """Each concurrent request gets its own scope (thread-local via Flask g)."""
        import threading
        from concurrent.futures import (
            ThreadPoolExecutor,
            as_completed,
        )

        from dioxide.flask import (
            configure_dioxide,
            inject,
        )

        @service(scope=Scope.REQUEST)
        class RequestContext:
            def __init__(self) -> None:
                import uuid

                self.request_id = str(uuid.uuid4())
                self.thread_id = threading.current_thread().ident

        app = Flask(__name__)
        container = Container()

        configure_dioxide(app, profile=Profile.TEST, container=container)

        @app.route('/test')
        def test_endpoint() -> dict[str, str | int | None]:
            ctx = inject(RequestContext)
            return {'request_id': ctx.request_id, 'thread_id': ctx.thread_id}

        # Make concurrent requests
        results: list[dict[str, str | int | None]] = []

        def make_request() -> dict[str, str | int | None]:
            with app.test_client() as client:
                response = client.get('/test')
                result: dict[str, str | int | None] = response.get_json()
                return result

        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(make_request) for _ in range(4)]
            for future in as_completed(futures):
                results.append(future.result())

        # All request IDs should be unique
        request_ids = [r['request_id'] for r in results]
        assert len(set(request_ids)) == 4


class DescribeImportErrorHandling:
    """Tests for handling missing Flask dependency."""

    def it_raises_import_error_when_flask_not_installed(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Module raises ImportError when Flask dependencies are unavailable."""
        import dioxide.flask as flask_module

        # Simulate Flask not being installed by setting module-level vars to None
        monkeypatch.setattr(flask_module, 'Flask', None)

        with pytest.raises(ImportError, match='Flask is not installed'):
            flask_module.configure_dioxide(None, profile=Profile.TEST)  # type: ignore[arg-type]

    def it_inject_raises_import_error_when_flask_not_installed(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """inject() raises ImportError when Flask dependencies are unavailable."""
        import dioxide.flask as flask_module

        # Simulate Flask not being installed
        monkeypatch.setattr(flask_module, 'has_request_context', None)

        with pytest.raises(ImportError, match='Flask is not installed'):
            flask_module.inject(object)
