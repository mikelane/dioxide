"""Flask integration for dioxide dependency injection.

This module provides seamless integration between dioxide's dependency injection
container and Flask applications. It enables:

- **Single function setup**: ``configure_dioxide(app, profile=...)``
- **Request scoping**: Automatic ``ScopedContainer`` per HTTP request via Flask's ``g``
- **Clean injection**: ``inject(Type)`` resolves from current request scope
- **Lifecycle management**: Container start/stop tied to Flask app configuration

Quick Start:
    Set up dioxide in your Flask app::

        from flask import Flask
        from dioxide import Profile
        from dioxide.flask import configure_dioxide, inject

        app = Flask(__name__)
        configure_dioxide(app, profile=Profile.PRODUCTION)


        @app.route('/users/me')
        def get_me():
            ctx = inject(RequestContext)
            return {'request_id': str(ctx.request_id)}


        @app.route('/users')
        def list_users():
            service = inject(UserService)
            return service.list_all()

Request Scoping:
    The integration creates a ``ScopedContainer`` for each HTTP request.
    This enables REQUEST-scoped components to be shared within a single
    request but fresh for each new request::

        from dioxide import service, Scope


        @service(scope=Scope.REQUEST)
        class RequestContext:
            def __init__(self):
                import uuid

                self.request_id = str(uuid.uuid4())


        # In route handlers:
        @app.route('/test')
        def test():
            ctx = inject(RequestContext)
            # ctx.request_id is unique per request
            # but shared if resolved multiple times within same request
            return {'request_id': ctx.request_id}

Lifecycle Management:
    The integration handles container lifecycle automatically::

        from dioxide import adapter, lifecycle, Profile


        @adapter.for_(DatabasePort, profile=Profile.PRODUCTION)
        @lifecycle
        class PostgresAdapter:
            async def initialize(self) -> None:
                self.engine = create_engine(...)
                print('Database connected')

            async def dispose(self) -> None:
                await self.engine.dispose()
                print('Database disconnected')


        # When configure_dioxide is called: container.scan() and start()
        # When request ends: scope.dispose() for REQUEST-scoped components

Thread Safety:
    Flask uses threading by default. The integration stores the scoped container
    in Flask's ``g`` object, which is thread-local, ensuring each request gets
    its own scope even in threaded mode.

See Also:
    - :func:`configure_dioxide` - The main setup function
    - :func:`inject` - Dependency injection helper for route handlers
    - :class:`dioxide.container.Container` - The DI container
    - :class:`dioxide.container.ScopedContainer` - Request-scoped container
"""

from __future__ import annotations

import asyncio
from typing import (
    TYPE_CHECKING,
    Any,
    TypeVar,
)

# Import Flask dependencies at runtime
# These are optional - if not installed, configure_dioxide() raises ImportError
Flask: Any = None
g: Any = None
has_request_context: Any = None
try:
    from flask import (
        Flask,
        g,
        has_request_context,
    )
except ImportError:
    pass

if TYPE_CHECKING:
    from dioxide.container import Container
    from dioxide.profile_enum import Profile

T = TypeVar('T')

# Key for storing container reference in app config
_CONTAINER_KEY = 'dioxide_container'


def configure_dioxide(
    app: Flask,
    profile: Profile | str | None = None,
    container: Container | None = None,
    packages: list[str] | None = None,
) -> None:
    """Configure dioxide dependency injection for a Flask application.

    This function sets up the integration between dioxide and Flask:

    1. Scans for components in specified packages (or all registered)
    2. Starts the container (initializing @lifecycle components)
    3. Registers request hooks for per-request scoping
    4. Stores the container in app.config for later access

    Args:
        app: The Flask application instance
        profile: Profile to scan with (e.g., ``Profile.PRODUCTION``). Accepts
            either a Profile enum value or a string profile name.
        container: Optional Container instance. If not provided, uses the
            global ``dioxide.container`` singleton.
        packages: Optional list of packages to scan for components. If not
            provided, scans all registered components.

    Raises:
        ImportError: If Flask is not installed.

    Example:
        Basic setup::

            from flask import Flask
            from dioxide import Profile
            from dioxide.flask import configure_dioxide

            app = Flask(__name__)
            configure_dioxide(app, profile=Profile.PRODUCTION)

        With custom container::

            from dioxide import Container, Profile
            from dioxide.flask import configure_dioxide

            my_container = Container()
            app = Flask(__name__)
            configure_dioxide(app, profile=Profile.TEST, container=my_container)

        With package scanning::

            configure_dioxide(
                app,
                profile=Profile.PRODUCTION,
                packages=['myapp.services', 'myapp.adapters'],
            )

        App factory pattern::

            def create_app():
                app = Flask(__name__)
                configure_dioxide(app, profile=Profile.PRODUCTION)
                return app

    See Also:
        - :func:`inject` - How to inject dependencies in routes
        - :class:`dioxide.container.ScopedContainer` - How scoping works
    """
    if Flask is None:
        raise ImportError('Flask is not installed. Install it with: pip install dioxide[flask]')

    from dioxide.container import container as global_container

    # Use provided container or global singleton
    di_container = container if container is not None else global_container

    # Scan packages and start container
    if packages:
        for package in packages:
            di_container.scan(package=package, profile=profile)
    else:
        di_container.scan(profile=profile)

    # Start container (initializes @lifecycle components)
    # Use asyncio.run() since Flask is synchronous
    asyncio.run(di_container.start())

    # Store container reference in app config
    app.config[_CONTAINER_KEY] = di_container

    # Register request hooks
    @app.before_request  # type: ignore[untyped-decorator,unused-ignore]
    def _create_request_scope() -> None:
        """Create a ScopedContainer for the current request."""
        # Get container from app config
        container_ref: Container = app.config[_CONTAINER_KEY]

        # Create scope and store in Flask's g (thread-local)
        # We need to manually manage the scope lifecycle since Flask is sync
        scope_ctx = container_ref.create_scope()
        # Enter the context manager synchronously
        scope = asyncio.run(scope_ctx.__aenter__())
        g.dioxide_scope = scope
        g._dioxide_scope_ctx = scope_ctx

    @app.teardown_request  # type: ignore[untyped-decorator,unused-ignore]
    def _dispose_request_scope(exception: BaseException | None = None) -> None:
        """Dispose the ScopedContainer after the request completes."""
        # Exit the scope context manager
        scope_ctx = getattr(g, '_dioxide_scope_ctx', None)
        if scope_ctx is not None:
            # Dispose all REQUEST-scoped @lifecycle components
            try:
                asyncio.run(scope_ctx.__aexit__(None, None, None))
            except Exception:
                pass  # Best effort cleanup


def inject(component_type: type[T]) -> T:
    """Resolve a component from the current request's dioxide scope.

    This function retrieves a dependency from the dioxide container for
    the current request. It automatically uses the correct scope:

    - **SINGLETON**: Resolved from parent container (shared)
    - **REQUEST**: Resolved from request scope (fresh per request)
    - **FACTORY**: New instance each resolution

    Args:
        component_type: The type to resolve from the container

    Returns:
        An instance of the requested type

    Raises:
        RuntimeError: If called outside a request context
        RuntimeError: If called without ``configure_dioxide()`` being set up
        ImportError: If Flask is not installed

    Example:
        Basic usage::

            from dioxide.flask import inject


            @app.route('/users')
            def list_users():
                service = inject(UserService)
                return service.list_all()

        Multiple dependencies::

            @app.route('/dashboard')
            def dashboard():
                users = inject(UserService)
                analytics = inject(AnalyticsService)
                return {
                    'users': users.count(),
                    'visits': analytics.total_visits(),
                }

        Request-scoped dependencies::

            from dioxide import service, Scope


            @service(scope=Scope.REQUEST)
            class RequestContext:
                def __init__(self):
                    self.request_id = str(uuid.uuid4())


            @app.route('/test')
            def test():
                ctx = inject(RequestContext)
                # ctx is unique per request
                return {'request_id': ctx.request_id}

    Note:
        Unlike FastAPI's ``Inject()`` which returns a Depends wrapper,
        Flask's ``inject()`` directly returns the resolved instance.
        This is because Flask doesn't have a dependency injection system
        like FastAPI's Depends.

    See Also:
        - :func:`configure_dioxide` - Must be called first
        - :class:`dioxide.container.ScopedContainer` - How scoping works
    """
    if has_request_context is None:
        raise ImportError('Flask is not installed. Install it with: pip install dioxide[flask]')

    # Check if we're in a request context
    if not has_request_context():
        raise RuntimeError(
            'inject() called outside of request context. This function can only be used inside Flask route handlers.'
        )

    # Get the scoped container from Flask's g
    scope = getattr(g, 'dioxide_scope', None)
    if scope is None:
        raise RuntimeError(
            'No dioxide scope found for this request. '
            'Did you call configure_dioxide(app) during app setup? '
            'Example: configure_dioxide(app, profile=Profile.PRODUCTION)'
        )

    return scope.resolve(component_type)


__all__ = [
    'configure_dioxide',
    'inject',
]
