"""FastAPI integration for dioxide dependency injection.

This module provides seamless integration between dioxide's dependency injection
container and FastAPI applications. It enables:

- **Single middleware setup**: ``app.add_middleware(DioxideMiddleware, profile=...)``
- **Request scoping**: Automatic ``ScopedContainer`` per HTTP request
- **Clean injection**: ``Inject(Type)`` wrapper for FastAPI's ``Depends()``
- **Lifecycle management**: Container start/stop with FastAPI lifespan

Quick Start:
    Set up dioxide in your FastAPI app::

        from fastapi import FastAPI
        from dioxide import Profile
        from dioxide.fastapi import DioxideMiddleware, Inject

        app = FastAPI()
        app.add_middleware(DioxideMiddleware, profile=Profile.PRODUCTION)


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
    The middleware handles container lifecycle automatically::

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
    - :class:`DioxideMiddleware` - The main integration middleware
    - :func:`Inject` - Dependency injection helper for route handlers
    - :class:`dioxide.container.Container` - The DI container
    - :class:`dioxide.container.ScopedContainer` - Request-scoped container
"""

from __future__ import annotations

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
    from dioxide.container import Container
    from dioxide.profile_enum import Profile

T = TypeVar('T')

# Key for storing scope in ASGI state
_SCOPE_KEY = 'dioxide_scope'
_CONTAINER_KEY = 'dioxide_container'


class DioxideMiddleware:
    """ASGI middleware that integrates dioxide with FastAPI.

    This middleware handles both:

    1. **Lifecycle management**: Container ``start()``/``stop()`` via ASGI lifespan
    2. **Request scoping**: Creates ``ScopedContainer`` per HTTP request

    The middleware intercepts ASGI events:

    - ``lifespan``: Scans components and starts/stops the container
    - ``http``: Creates a scoped container for each request

    Usage:
        Basic setup with profile::

            from fastapi import FastAPI
            from dioxide import Profile
            from dioxide.fastapi import DioxideMiddleware

            app = FastAPI()
            app.add_middleware(DioxideMiddleware, profile=Profile.PRODUCTION)

        With custom container::

            from dioxide import Container, Profile
            from dioxide.fastapi import DioxideMiddleware

            my_container = Container()
            app = FastAPI()
            app.add_middleware(
                DioxideMiddleware,
                container=my_container,
                profile=Profile.TEST,
            )

        With package scanning::

            app.add_middleware(
                DioxideMiddleware,
                profile=Profile.PRODUCTION,
                packages=['myapp.services', 'myapp.adapters'],
            )

    Args:
        app: The ASGI application to wrap
        profile: Profile to scan with (e.g., ``Profile.PRODUCTION``)
        container: Optional Container instance. If not provided, uses
            the global ``dioxide.container`` singleton.
        packages: Optional list of packages to scan for components.

    See Also:
        - :func:`Inject` - How to inject dependencies in routes
        - :class:`dioxide.container.ScopedContainer` - The scoped container
    """

    def __init__(
        self,
        app: Any,
        profile: Profile | str | None = None,
        container: Container | None = None,
        packages: list[str] | None = None,
    ) -> None:
        """Initialize the middleware.

        Args:
            app: The ASGI application to wrap
            profile: Profile to scan with (e.g., ``Profile.PRODUCTION``)
            container: Optional Container instance. If not provided, uses
                the global ``dioxide.container`` singleton.
            packages: Optional list of packages to scan for components.
        """
        from dioxide.container import container as global_container

        self.app = app
        self.profile = profile
        self.container = container if container is not None else global_container
        self.packages = packages
        self._started = False

    async def __call__(self, scope: dict[str, Any], receive: Any, send: Any) -> None:
        """Process an ASGI request.

        Handles three ASGI scope types:

        - ``lifespan``: Manages container startup/shutdown
        - ``http``: Creates ScopedContainer per request
        - Other types: Passes through unchanged

        Args:
            scope: ASGI scope dictionary
            receive: ASGI receive callable
            send: ASGI send callable
        """
        if scope['type'] == 'lifespan':
            await self._handle_lifespan(scope, receive, send)
        elif scope['type'] == 'http':
            await self._handle_http(scope, receive, send)
        else:
            # Pass through other request types (websocket, etc.)
            await self.app(scope, receive, send)

    async def _handle_lifespan(self, scope: dict[str, Any], receive: Any, send: Any) -> None:
        """Handle ASGI lifespan events for container startup/shutdown.

        This wraps the lifespan handling to:
        1. Initialize dioxide container BEFORE the wrapped app starts
        2. Stop dioxide container AFTER the wrapped app stops
        3. Properly forward lifespan events to the wrapped app
        """
        startup_complete = False
        shutdown_complete = False

        async def wrapped_receive() -> dict[str, Any]:
            """Intercept lifespan messages to hook in container lifecycle."""
            nonlocal startup_complete
            message = await receive()

            if message['type'] == 'lifespan.startup':
                # Scan and start container BEFORE forwarding to wrapped app
                try:
                    if self.packages:
                        for package in self.packages:
                            self.container.scan(package=package, profile=self.profile)
                    else:
                        self.container.scan(profile=self.profile)

                    await self.container.start()
                    self._started = True

                    # Store container in app state
                    if 'state' not in scope:
                        scope['state'] = {}
                    scope['state'][_CONTAINER_KEY] = self.container

                except Exception:
                    # Re-raise to let the error propagate through send wrapper
                    raise

            return message

        async def wrapped_send(message: dict[str, Any]) -> None:
            """Intercept lifespan responses to hook in container cleanup."""
            nonlocal startup_complete, shutdown_complete

            if message['type'] == 'lifespan.startup.complete':
                startup_complete = True
                await send(message)

            elif message['type'] == 'lifespan.startup.failed':
                # If startup failed, stop container if it was started
                if self._started:
                    try:
                        await self.container.stop()
                    except Exception:
                        pass
                await send(message)

            elif message['type'] == 'lifespan.shutdown.complete':
                # Stop container AFTER wrapped app has shut down
                shutdown_complete = True
                if self._started:
                    try:
                        await self.container.stop()
                    except Exception:
                        pass  # Best effort cleanup
                await send(message)

            else:
                await send(message)

        # Forward to wrapped app with our intercepting receive/send
        try:
            await self.app(scope, wrapped_receive, wrapped_send)
        except Exception as exc:
            # If startup scanning/initialization failed, send failure
            if not startup_complete:
                await send({'type': 'lifespan.startup.failed', 'message': str(exc)})
            raise

    async def _handle_http(self, scope: dict[str, Any], receive: Any, send: Any) -> None:
        """Handle HTTP requests with per-request scoping."""
        # Ensure 'state' dict exists in ASGI scope
        if 'state' not in scope:
            scope['state'] = {}

        # Store container reference for Inject() to find
        scope['state'][_CONTAINER_KEY] = self.container

        # Create a scoped container for this request
        async with self.container.create_scope() as scoped_container:
            # Store scope in ASGI scope for access by dependencies
            scope['state'][_SCOPE_KEY] = scoped_container

            await self.app(scope, receive, send)


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
        RuntimeError: If called without ``DioxideMiddleware`` being configured

    Note:
        The function name is capitalized (``Inject``) to match the convention
        of FastAPI's ``Depends``, ``Query``, ``Body``, etc.

    See Also:
        - :class:`DioxideMiddleware` - Must be added first
        - :class:`dioxide.container.ScopedContainer` - How scoping works
    """
    if Request is None or Depends is None:
        raise ImportError('FastAPI is not installed. Install it with: pip install dioxide[fastapi]')

    # Use Request type directly (verified not None above) for FastAPI DI to work
    def _resolver(request: Request) -> T:
        """Resolve component from the dioxide scope."""
        # Get the scoped container from request state
        if not hasattr(request.state, _SCOPE_KEY):
            raise RuntimeError(
                'No dioxide scope found for this request. '
                'Did you add DioxideMiddleware to your FastAPI app? '
                'Example: app.add_middleware(DioxideMiddleware, profile=Profile.PRODUCTION)'
            )

        scope = getattr(request.state, _SCOPE_KEY)
        return scope.resolve(component_type)

    return Depends(_resolver)


__all__ = [
    'DioxideMiddleware',
    'Inject',
]
