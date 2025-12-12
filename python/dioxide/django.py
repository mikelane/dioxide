"""Django integration for dioxide dependency injection.

This module provides seamless integration between dioxide's dependency injection
container and Django applications. It enables:

- **Single function setup**: ``configure_dioxide(profile=...)``
- **Request scoping**: Automatic ``ScopedContainer`` per HTTP request via middleware
- **Clean injection**: ``inject(Type)`` resolves from current request scope
- **Lifecycle management**: Container start/stop tied to Django configuration

Quick Start:
    Set up dioxide in your Django settings.py or apps.py::

        # In settings.py or your AppConfig.ready()
        from dioxide import Profile
        from dioxide.django import configure_dioxide

        configure_dioxide(profile=Profile.PRODUCTION)

    Add the middleware to settings.py::

        MIDDLEWARE = [
            ...
            'dioxide.django.DioxideMiddleware',
            ...
        ]

    Use in views::

        from dioxide.django import inject


        def my_view(request):
            service = inject(UserService)
            return JsonResponse(service.get_data())

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


        # In views:
        def my_view(request):
            ctx = inject(RequestContext)
            # ctx.request_id is unique per request
            # but shared if resolved multiple times within same request
            return JsonResponse({'request_id': ctx.request_id})

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
    Django uses threading by default. The integration stores the scoped container
    in thread-local storage, ensuring each request gets its own scope even in
    threaded mode.

See Also:
    - :func:`configure_dioxide` - The main setup function
    - :class:`DioxideMiddleware` - Request scoping middleware
    - :func:`inject` - Dependency injection helper for views
    - :class:`dioxide.container.Container` - The DI container
    - :class:`dioxide.container.ScopedContainer` - Request-scoped container
"""

from __future__ import annotations

import asyncio
import threading
from typing import (
    TYPE_CHECKING,
    Any,
    TypeVar,
)

# Import Django dependencies at runtime
# These are optional - if not installed, configure_dioxide() raises ImportError
Django: Any = None
try:
    import django

    Django = django
except ImportError:
    pass

if TYPE_CHECKING:
    from collections.abc import Callable

    from django.http import (
        HttpRequest,
        HttpResponse,
    )

    from dioxide.container import (
        Container,
        ScopedContainer,
    )
    from dioxide.profile_enum import Profile

T = TypeVar('T')

# Thread-local storage for request scope
_request_scope = threading.local()

# Module-level container reference (set by configure_dioxide)
_container: Container | None = None


def configure_dioxide(
    profile: Profile | str | None = None,
    container: Container | None = None,
    packages: list[str] | None = None,
) -> None:
    """Configure dioxide dependency injection for a Django application.

    This function sets up the integration between dioxide and Django:

    1. Scans for components in specified packages (or all registered)
    2. Starts the container (initializing @lifecycle components)
    3. Stores the container reference for later access by middleware

    Call this in your Django settings.py, apps.py ready(), or conftest.py.

    Args:
        profile: Profile to scan with (e.g., ``Profile.PRODUCTION``). Accepts
            either a Profile enum value or a string profile name.
        container: Optional Container instance. If not provided, uses the
            global ``dioxide.container`` singleton.
        packages: Optional list of packages to scan for components. If not
            provided, scans all registered components.

    Raises:
        ImportError: If Django is not installed.

    Example:
        Basic setup in settings.py::

            from dioxide import Profile
            from dioxide.django import configure_dioxide

            configure_dioxide(profile=Profile.PRODUCTION)

        In apps.py ready() method::

            from django.apps import AppConfig
            from dioxide import Profile
            from dioxide.django import configure_dioxide


            class MyAppConfig(AppConfig):
                name = 'myapp'

                def ready(self):
                    configure_dioxide(profile=Profile.PRODUCTION)

        With custom container::

            from dioxide import Container, Profile
            from dioxide.django import configure_dioxide

            my_container = Container()
            configure_dioxide(profile=Profile.TEST, container=my_container)

        With package scanning::

            configure_dioxide(
                profile=Profile.PRODUCTION,
                packages=['myapp.services', 'myapp.adapters'],
            )

    See Also:
        - :class:`DioxideMiddleware` - Must be added to MIDDLEWARE
        - :func:`inject` - How to inject dependencies in views
        - :class:`dioxide.container.ScopedContainer` - How scoping works
    """
    global _container

    if Django is None:
        raise ImportError('Django is not installed. Install it with: pip install dioxide[django]')

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
    # Use asyncio.run() since Django is synchronous
    asyncio.run(di_container.start())

    # Store container reference for middleware
    _container = di_container


class DioxideMiddleware:
    """Django middleware that creates a ScopedContainer per request.

    This middleware handles request scoping for dioxide:

    1. Creates a ``ScopedContainer`` before the view runs
    2. Stores it in thread-local storage for ``inject()`` to access
    3. Disposes the scope after the response is returned

    Usage in settings.py::

        MIDDLEWARE = [
            ...
            'dioxide.django.DioxideMiddleware',
            ...
        ]

    Note:
        The middleware must be placed after any middleware that might need
        dioxide services, as it creates the scope on request entry.

    See Also:
        - :func:`configure_dioxide` - Must be called first
        - :func:`inject` - How to inject dependencies in views
        - :class:`dioxide.container.ScopedContainer` - The scoped container
    """

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        """Initialize the middleware.

        Args:
            get_response: The next middleware or view in the chain.
        """
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        """Process a request with dioxide scoping.

        Creates a scoped container for the request, stores it in thread-local
        storage, calls the view, and ensures cleanup on completion.

        Args:
            request: The Django HttpRequest object.

        Returns:
            The HttpResponse from the view.
        """
        if _container is None:
            raise RuntimeError(
                'dioxide container not configured. '
                'Did you call configure_dioxide() during Django startup? '
                'Example: configure_dioxide(profile=Profile.PRODUCTION)'
            )

        # Create scope and store in thread-local storage
        scope_ctx = _container.create_scope()

        # Enter the context manager synchronously
        scope = asyncio.run(scope_ctx.__aenter__())
        _request_scope.scope = scope

        try:
            response = self.get_response(request)
            return response
        finally:
            # Exit the scope context manager (disposes REQUEST-scoped lifecycle components)
            try:
                asyncio.run(scope_ctx.__aexit__(None, None, None))
            except Exception:
                pass  # Best effort cleanup
            finally:
                # Clear thread-local storage
                _request_scope.scope = None


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
        ImportError: If Django is not installed

    Example:
        Basic usage::

            from dioxide.django import inject


            def my_view(request):
                service = inject(UserService)
                return JsonResponse(service.get_data())

        Multiple dependencies::

            def dashboard_view(request):
                users = inject(UserService)
                analytics = inject(AnalyticsService)
                return JsonResponse(
                    {
                        'users': users.count(),
                        'visits': analytics.total_visits(),
                    }
                )

        Request-scoped dependencies::

            from dioxide import service, Scope


            @service(scope=Scope.REQUEST)
            class RequestContext:
                def __init__(self):
                    self.request_id = str(uuid.uuid4())


            def my_view(request):
                ctx = inject(RequestContext)
                # ctx is unique per request
                return JsonResponse({'request_id': ctx.request_id})

    Note:
        Unlike FastAPI's ``Inject()`` which returns a Depends wrapper,
        Django's ``inject()`` directly returns the resolved instance.
        This is because Django doesn't have a dependency injection system
        like FastAPI's Depends.

    See Also:
        - :func:`configure_dioxide` - Must be called first
        - :class:`DioxideMiddleware` - Must be added to MIDDLEWARE
        - :class:`dioxide.container.ScopedContainer` - How scoping works
    """
    if Django is None:
        raise ImportError('Django is not installed. Install it with: pip install dioxide[django]')

    # Get the scoped container from thread-local storage
    scope: ScopedContainer | None = getattr(_request_scope, 'scope', None)
    if scope is None:
        raise RuntimeError(
            'inject() called outside of request context. This function can only be used inside Django views. '
            'Did you add DioxideMiddleware to your MIDDLEWARE setting?'
        )

    return scope.resolve(component_type)


__all__ = [
    'DioxideMiddleware',
    'configure_dioxide',
    'inject',
]
