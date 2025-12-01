"""Click integration for dioxide dependency injection.

This module provides seamless integration between dioxide's dependency injection
container and Click CLI applications. It enables:

- **Single function setup**: ``configure_dioxide(profile=...)``
- **Command scoping**: ``@with_scope(container)`` decorator for per-command scopes
- **Clean injection**: Scope passed as first argument to commands
- **Lifecycle management**: Components disposed after command completes

Quick Start:
    Set up dioxide in your Click CLI::

        import click
        from dioxide import Profile
        from dioxide.click import configure_dioxide, with_scope

        container = configure_dioxide(profile=Profile.PRODUCTION)


        @click.command()
        @with_scope(container)
        def greet(scope, name):
            service = scope.resolve(GreetingService)
            click.echo(service.greet(name))


        @click.argument('name')
        def main():
            greet()

Command Scoping:
    The ``with_scope`` decorator creates a ``ScopedContainer`` for each command
    invocation. This enables REQUEST-scoped components to be fresh for each
    command while SINGLETON components remain shared::

        from dioxide import service, Scope


        @service(scope=Scope.REQUEST)
        class CommandContext:
            def __init__(self):
                import uuid

                self.command_id = str(uuid.uuid4())


        @click.command()
        @with_scope(container)
        def my_command(scope):
            ctx = scope.resolve(CommandContext)
            # ctx.command_id is unique per command invocation
            click.echo(f'Command ID: {ctx.command_id}')

Lifecycle Management:
    The integration handles lifecycle disposal automatically::

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


        # When command completes: scope disposes REQUEST-scoped @lifecycle components

Click Groups:
    The integration works with Click groups and nested commands::

        @click.group()
        def cli():
            pass


        @cli.command()
        @with_scope(container)
        @click.argument('user_id')
        def get_user(scope, user_id):
            service = scope.resolve(UserService)
            click.echo(service.get_user(user_id))


        @cli.group()
        def config():
            pass


        @config.command()
        @with_scope(container)
        @click.argument('key')
        def get(scope, key):
            service = scope.resolve(ConfigService)
            click.echo(service.get_value(key))

Typer Compatibility:
    Since Typer is built on Click, this integration works with Typer applications::

        import typer
        import click
        from dioxide.click import configure_dioxide, with_scope

        container = configure_dioxide(profile=Profile.PRODUCTION)
        app = typer.Typer()


        @click.command()
        @with_scope(container)
        @click.argument('name')
        def greet(scope, name):
            service = scope.resolve(GreetingService)
            typer.echo(service.greet(name))


        app.command()(greet)

See Also:
    - :func:`configure_dioxide` - The main setup function
    - :func:`with_scope` - Decorator for per-command scoping
    - :class:`dioxide.container.Container` - The DI container
    - :class:`dioxide.container.ScopedContainer` - Command-scoped container
"""

from __future__ import annotations

import asyncio
import functools
from typing import (
    TYPE_CHECKING,
    Any,
    TypeVar,
)

from dioxide.container import Container as DioxideContainer

# Import Click dependencies at runtime
# These are optional - if not installed, configure_dioxide() raises ImportError
click: Any = None
try:
    import click as click_module

    click = click_module
except ImportError:
    pass

if TYPE_CHECKING:
    from collections.abc import Callable

    from dioxide.container import Container
    from dioxide.profile_enum import Profile

F = TypeVar('F', bound='Callable[..., Any]')


def configure_dioxide(
    profile: Profile | str | None = None,
    container: Container | None = None,
    packages: list[str] | None = None,
) -> Container:
    """Configure dioxide dependency injection for a Click CLI application.

    This function sets up the integration between dioxide and Click:

    1. Creates or uses provided container
    2. Scans for components in specified packages (or all registered)
    3. Returns the configured container for use with ``with_scope``

    Args:
        profile: Profile to scan with (e.g., ``Profile.PRODUCTION``). Accepts
            either a Profile enum value or a string profile name.
        container: Optional Container instance. If not provided, creates a new
            Container instance.
        packages: Optional list of packages to scan for components. If not
            provided, scans all registered components.

    Returns:
        The configured Container instance ready for use with ``with_scope``.

    Raises:
        ImportError: If Click is not installed.

    Example:
        Basic setup::

            from dioxide import Profile
            from dioxide.click import configure_dioxide

            container = configure_dioxide(profile=Profile.PRODUCTION)

        With custom container::

            from dioxide import Container, Profile
            from dioxide.click import configure_dioxide

            my_container = Container()
            container = configure_dioxide(profile=Profile.TEST, container=my_container)

        With package scanning::

            container = configure_dioxide(
                profile=Profile.PRODUCTION,
                packages=['myapp.services', 'myapp.adapters'],
            )

    See Also:
        - :func:`with_scope` - How to inject dependencies in commands
        - :class:`dioxide.container.ScopedContainer` - How scoping works
    """
    if click is None:
        raise ImportError('Click is not installed. Install it with: pip install dioxide[click]')

    # Use provided container or create new one
    di_container = container if container is not None else DioxideContainer()

    # Scan packages
    if packages:
        for package in packages:
            di_container.scan(package=package, profile=profile)
    else:
        di_container.scan(profile=profile)

    # Start container (initializes @lifecycle components)
    # Use asyncio.run() since Click is synchronous
    asyncio.run(di_container.start())

    return di_container


def with_scope(container: Container) -> Callable[[F], F]:
    """Decorator that creates a dioxide scope for each command invocation.

    This decorator wraps a Click command to:
    1. Create a new ScopedContainer before the command runs
    2. Pass the scope as the first argument to the command
    3. Dispose the scope after the command completes (even on error)

    The scope enables REQUEST-scoped components to be cached within a single
    command invocation while remaining fresh across different invocations.

    Args:
        container: The Container instance (from ``configure_dioxide``).

    Returns:
        A decorator that wraps Click commands with scope management.

    Example:
        Basic usage::

            from dioxide.click import configure_dioxide, with_scope

            container = configure_dioxide(profile=Profile.PRODUCTION)


            @click.command()
            @with_scope(container)
            def my_command(scope):
                service = scope.resolve(MyService)
                click.echo(service.do_something())

        With Click arguments and options::

            @click.command()
            @with_scope(container)
            @click.option('--verbose', is_flag=True)
            @click.argument('name')
            def greet(scope, verbose, name):
                service = scope.resolve(GreetingService)
                result = service.greet(name)
                if verbose:
                    click.echo(f'Greeting: {result}')
                else:
                    click.echo(result)

        With Click groups::

            @click.group()
            def cli():
                pass


            @cli.command()
            @with_scope(container)
            @click.argument('user_id')
            def get_user(scope, user_id):
                service = scope.resolve(UserService)
                click.echo(service.get_user(user_id))

    Note:
        The scope is always passed as the FIRST argument to the decorated
        function, before any Click arguments or options. This is because
        decorators are applied bottom-up, and ``with_scope`` needs to inject
        the scope before Click processes its arguments.

    See Also:
        - :func:`configure_dioxide` - Must be called first to get container
        - :class:`dioxide.container.ScopedContainer` - How scoping works
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Run the command within a scope context
            async def run_with_scope() -> Any:
                async with container.create_scope() as scope:
                    # Pass scope as first argument
                    # Scope cleanup handled by async context manager
                    return func(scope, *args, **kwargs)

            # Use asyncio.run to handle the async context manager
            return asyncio.run(run_with_scope())

        return wrapper  # type: ignore[return-value]

    return decorator


__all__ = [
    'configure_dioxide',
    'with_scope',
]
