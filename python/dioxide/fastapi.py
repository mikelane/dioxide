"""FastAPI integration for dioxide dependency injection.

This module provides seamless integration between dioxide's dependency injection
container and FastAPI applications. It enables:

- **One-line setup**: ``configure_dioxide(app, profile=Profile.PRODUCTION)``
- **Request scoping**: Automatic ``ScopedContainer`` per HTTP request
- **Clean injection**: ``Inject(Type)`` wrapper for FastAPI's ``Depends()``
- **Lifecycle management**: Container start/stop with FastAPI lifespan

Quick Start:
    Set up dioxide in your FastAPI app::

        from fastapi import FastAPI
        from dioxide import Profile
        from dioxide.fastapi import configure_dioxide, Inject

        app = FastAPI()
        configure_dioxide(app, profile=Profile.PRODUCTION)


        @app.get('/users/me')
        async def get_me(ctx: RequestContext = Inject(RequestContext)):
            return {'request_id': str(ctx.request_id)}


        @app.get('/users')
        async def list_users(service: UserService = Inject(UserService)):
            return await service.list_all()

Request Scoping:
    The middleware creates a ``ScopedContainer`` for each HTTP request.
    This enables REQUEST-scoped components to be shared within a single
    request but fresh for each new request::

        from dioxide import service, Scope


        @service(scope=Scope.REQUEST)
        class RequestContext:
            def __init__(self):
                import uuid

                self.request_id = str(uuid.uuid4())


        # In route handlers:
        @app.get('/test')
        async def test(ctx: RequestContext = Inject(RequestContext)):
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


        # When FastAPI starts: container.start() initializes adapters
        # When FastAPI stops: container.stop() disposes adapters

See Also:
    - :func:`configure_dioxide` - One-line setup for FastAPI apps
    - :class:`DiOxideScopeMiddleware` - Request scoping middleware
    - :func:`Inject` - Dependency injection helper for route handlers
    - :class:`dioxide.container.Container` - The DI container
    - :class:`dioxide.container.ScopedContainer` - Request-scoped container
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import (
    TYPE_CHECKING,
    Any,
    TypeVar,
)

# Import FastAPI dependencies at runtime
# These are optional - if not installed, Inject() raises ImportError
Depends: Any = None
Request: Any = None
try:
    from fastapi import (
        Depends,
        Request,
    )
except ImportError:
    pass

if TYPE_CHECKING:
    from fastapi import FastAPI

    from dioxide.container import Container
    from dioxide.profile_enum import Profile

T = TypeVar('T')


class DiOxideScopeMiddleware:
    """ASGI middleware that creates a ScopedContainer per request.

    This middleware wraps each HTTP request in a scope context, providing:

    - Fresh ``ScopedContainer`` for each request
    - REQUEST-scoped component caching within the request
    - Automatic disposal of REQUEST-scoped lifecycle components

    The scope is stored in ``request.state.dioxide_scope`` for access
    in route handlers and dependencies.

    Usage:
        This middleware is automatically added by ``configure_dioxide()``.
        You typically don't need to add it manually::

            from fastapi import FastAPI
            from dioxide.fastapi import configure_dioxide

            app = FastAPI()
            configure_dioxide(app, profile=Profile.PRODUCTION)
            # Middleware is added automatically

    Manual usage (if needed)::

            from fastapi import FastAPI
            from dioxide.fastapi import DiOxideScopeMiddleware
            from dioxide import container

            app = FastAPI()
            app.add_middleware(DiOxideScopeMiddleware, container=container)

    Attributes:
        app: The ASGI application
        container: The dioxide Container to create scopes from

    See Also:
        - :func:`configure_dioxide` - Recommended setup function
        - :class:`dioxide.container.ScopedContainer` - The scoped container
    """

    def __init__(self, app: Any, container: Container) -> None:
        """Initialize the middleware.

        Args:
            app: The ASGI application to wrap
            container: The dioxide Container to create scopes from
        """
        self.app = app
        self.container = container

    async def __call__(self, scope: dict[str, Any], receive: Any, send: Any) -> None:
        """Process an ASGI request.

        For HTTP requests, creates a ScopedContainer and stores it in
        the request state. For other request types (websocket, lifespan),
        passes through without modification.

        Args:
            scope: ASGI scope dictionary
            receive: ASGI receive callable
            send: ASGI send callable
        """
        if scope['type'] != 'http':
            # Pass through non-HTTP requests (websocket, lifespan, etc.)
            await self.app(scope, receive, send)
            return

        # Ensure 'state' dict exists in ASGI scope
        if 'state' not in scope:
            scope['state'] = {}

        # Create a scoped container for this request
        async with self.container.create_scope() as scoped_container:
            # Store scope in ASGI scope for access by dependencies
            scope['state']['dioxide_scope'] = scoped_container

            await self.app(scope, receive, send)


def configure_dioxide(
    app: FastAPI,
    profile: Profile | str | None = None,
    container: Container | None = None,
    packages: list[str] | None = None,
) -> None:
    """Configure dioxide integration for a FastAPI application.

    This is the main entry point for integrating dioxide with FastAPI.
    It sets up:

    1. **Lifespan management**: Container ``start()``/``stop()`` with FastAPI
    2. **Request middleware**: Creates ``ScopedContainer`` per HTTP request
    3. **Container scanning**: Discovers and registers components

    Args:
        app: The FastAPI application to configure
        profile: Profile to scan with (e.g., ``Profile.PRODUCTION``).
            Determines which adapters are activated.
        container: Optional Container instance. If not provided, uses
            the global ``dioxide.container`` singleton.
        packages: Optional list of packages to scan for components.
            If not provided, scans all registered components.

    Example:
        Basic setup::

            from fastapi import FastAPI
            from dioxide import Profile
            from dioxide.fastapi import configure_dioxide

            app = FastAPI()
            configure_dioxide(app, profile=Profile.PRODUCTION)

        With custom container::

            from dioxide import Container, Profile
            from dioxide.fastapi import configure_dioxide

            container = Container()
            app = FastAPI()
            configure_dioxide(app, container=container, profile=Profile.TEST)

        With package scanning::

            configure_dioxide(
                app,
                profile=Profile.PRODUCTION,
                packages=['myapp.services', 'myapp.adapters'],
            )

    Note:
        This function must be called before any routes that use ``Inject()``.
        It modifies the app's lifespan and adds middleware.

    See Also:
        - :func:`Inject` - How to inject dependencies in routes
        - :class:`DiOxideScopeMiddleware` - The middleware that's added
    """
    from dioxide.container import container as global_container

    # Use global container if not provided
    target_container = container if container is not None else global_container

    # Store container in app state for access by Inject()
    app.state.dioxide_container = target_container

    # Store profile for later scanning
    app.state.dioxide_profile = profile
    app.state.dioxide_packages = packages

    # Create lifespan context manager that wraps any existing lifespan
    original_lifespan = app.router.lifespan_context

    @asynccontextmanager
    async def dioxide_lifespan(app: FastAPI) -> AsyncIterator[dict[str, Any]]:
        """Lifespan that manages dioxide container lifecycle."""
        # Scan for components with the specified profile
        if packages:
            for package in packages:
                target_container.scan(package=package, profile=profile)
        else:
            target_container.scan(profile=profile)

        # Start container (initializes @lifecycle components)
        async with target_container:
            # If there was an original lifespan, run it too
            if original_lifespan is not None:
                async with original_lifespan(app) as state:
                    yield dict(state) if state else {}
            else:
                yield {}

    # Set the new lifespan
    app.router.lifespan_context = dioxide_lifespan

    # Add middleware for request scoping
    app.add_middleware(DiOxideScopeMiddleware, container=target_container)


def Inject(component_type: type[T]) -> Any:  # noqa: N802
    """Create a FastAPI dependency that resolves from dioxide container.

    This function wraps FastAPI's ``Depends()`` to resolve dependencies
    from the dioxide container. It automatically uses the correct scope:

    - **SINGLETON**: Resolved from parent container (shared)
    - **REQUEST**: Resolved from request scope (fresh per request)
    - **FACTORY**: New instance each resolution

    Args:
        component_type: The type to resolve from the container

    Returns:
        A FastAPI ``Depends()`` object that resolves the component

    Example:
        Basic usage::

            from dioxide.fastapi import Inject


            @app.get('/users')
            async def list_users(service: UserService = Inject(UserService)):
                return await service.list_all()

        Multiple dependencies::

            @app.get('/dashboard')
            async def dashboard(
                users: UserService = Inject(UserService),
                analytics: AnalyticsService = Inject(AnalyticsService),
            ):
                return {
                    'users': await users.count(),
                    'visits': await analytics.total_visits(),
                }

        Request-scoped dependencies::

            from dioxide import service, Scope


            @service(scope=Scope.REQUEST)
            class RequestContext:
                def __init__(self):
                    self.request_id = str(uuid.uuid4())


            @app.get('/test')
            async def test(ctx: RequestContext = Inject(RequestContext)):
                # ctx is unique per request
                return {'request_id': ctx.request_id}

    Raises:
        RuntimeError: If called without ``configure_dioxide()`` being called first

    Note:
        The function name is capitalized (``Inject``) to match the convention
        of FastAPI's ``Depends``, ``Query``, ``Body``, etc.

    See Also:
        - :func:`configure_dioxide` - Must be called first
        - :class:`dioxide.container.ScopedContainer` - How scoping works
    """
    if Request is None or Depends is None:
        raise ImportError('FastAPI is not installed. Install it with: pip install dioxide[fastapi]')

    def _resolver(request: Any) -> T:
        """Resolve component from the dioxide scope."""
        # Check if dioxide is configured
        if not hasattr(request.app.state, 'dioxide_container'):
            raise RuntimeError(
                'dioxide is not configured for this FastAPI app. '
                'Call configure_dioxide(app, profile=...) before using Inject().'
            )

        # Get the scoped container from request state
        if not hasattr(request.state, 'dioxide_scope'):
            raise RuntimeError(
                'No dioxide scope found for this request. Ensure DiOxideScopeMiddleware is properly configured.'
            )

        scope = request.state.dioxide_scope
        return scope.resolve(component_type)

    return Depends(_resolver)


__all__ = [
    'DiOxideScopeMiddleware',
    'Inject',
    'configure_dioxide',
]
