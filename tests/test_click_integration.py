"""Tests for Click integration module.

This module tests the dioxide.click integration that provides:
- configure_dioxide(profile=...) - Sets up container scanning for CLI
- with_scope - Decorator that creates scope per command and passes it as first arg
"""

from __future__ import annotations

from typing import Protocol

import pytest

# Skip this entire module if Click is not installed
pytest.importorskip('click')

from click.testing import CliRunner

from dioxide import (
    Container,
    Profile,
    Scope,
    ScopedContainer,
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

    def it_returns_configured_container(self) -> None:
        """configure_dioxide returns a configured Container."""
        from dioxide.click import configure_dioxide

        @service
        class SimpleService:
            def get_value(self) -> str:
                return 'configured'

        container = configure_dioxide(profile=Profile.TEST)

        assert container is not None
        svc = container.resolve(SimpleService)
        assert svc.get_value() == 'configured'

    def it_uses_provided_container(self) -> None:
        """configure_dioxide uses the provided container when specified."""
        from dioxide.click import configure_dioxide

        @service
        class SimpleService:
            def get_value(self) -> str:
                return 'custom'

        custom_container = Container()
        result = configure_dioxide(profile=Profile.TEST, container=custom_container)

        assert result is custom_container

    def it_scans_specified_packages(self) -> None:
        """configure_dioxide can scan specific packages."""
        from dioxide.click import configure_dioxide

        container = configure_dioxide(
            profile=Profile.TEST,
            packages=['dioxide'],
        )

        assert container is not None


class DescribeWithScopeDecorator:
    """Tests for with_scope decorator."""

    def it_passes_scope_as_first_argument(self) -> None:
        """with_scope decorator passes ScopedContainer as first arg to command."""
        import click

        from dioxide.click import (
            configure_dioxide,
            with_scope,
        )

        @service
        class GreetingService:
            def greet(self, name: str) -> str:
                return f'Hello, {name}!'

        container = configure_dioxide(profile=Profile.TEST)

        @click.command()
        @with_scope(container)
        def greet_cmd(scope: ScopedContainer, name: str) -> None:
            svc = scope.resolve(GreetingService)
            click.echo(svc.greet(name))

        # Add the name argument
        greet_cmd = click.argument('name')(greet_cmd)

        runner = CliRunner()
        result = runner.invoke(greet_cmd, ['World'])

        assert result.exit_code == 0
        assert 'Hello, World!' in result.output

    def it_creates_fresh_scope_per_command_invocation(self) -> None:
        """with_scope creates a new scope for each command invocation."""
        import click

        from dioxide.click import (
            configure_dioxide,
            with_scope,
        )

        scope_ids: list[str] = []

        @service(scope=Scope.REQUEST)
        class RequestContext:
            def __init__(self) -> None:
                import uuid

                self.request_id = str(uuid.uuid4())

        container = configure_dioxide(profile=Profile.TEST)

        @click.command()
        @with_scope(container)
        def cmd(scope: ScopedContainer) -> None:
            ctx = scope.resolve(RequestContext)
            scope_ids.append(ctx.request_id)
            click.echo(f'Request ID: {ctx.request_id}')

        runner = CliRunner()

        # Invoke twice
        runner.invoke(cmd)
        runner.invoke(cmd)

        assert len(scope_ids) == 2
        assert scope_ids[0] != scope_ids[1]

    def it_shares_request_scoped_within_same_command(self) -> None:
        """with_scope returns same REQUEST-scoped instance within a single command."""
        import click

        from dioxide.click import (
            configure_dioxide,
            with_scope,
        )

        @service(scope=Scope.REQUEST)
        class RequestContext:
            def __init__(self) -> None:
                import uuid

                self.request_id = str(uuid.uuid4())

        container = configure_dioxide(profile=Profile.TEST)

        @click.command()
        @with_scope(container)
        def cmd(scope: ScopedContainer) -> None:
            ctx1 = scope.resolve(RequestContext)
            ctx2 = scope.resolve(RequestContext)
            if ctx1 is ctx2:
                click.echo('same_instance=True')
            else:
                click.echo('same_instance=False')

        runner = CliRunner()
        result = runner.invoke(cmd)

        assert result.exit_code == 0
        assert 'same_instance=True' in result.output


class DescribeClickGroupSupport:
    """Tests for Click group support."""

    def it_works_with_click_groups(self) -> None:
        """with_scope works with Click groups."""
        import click

        from dioxide.click import (
            configure_dioxide,
            with_scope,
        )

        @service
        class UserService:
            def get_user(self, user_id: str) -> str:
                return f'User {user_id}'

        container = configure_dioxide(profile=Profile.TEST)

        @click.group()
        def cli() -> None:
            pass

        @cli.command()
        @with_scope(container)
        @click.argument('user_id')
        def get_user(scope: ScopedContainer, user_id: str) -> None:
            svc = scope.resolve(UserService)
            click.echo(svc.get_user(user_id))

        runner = CliRunner()
        result = runner.invoke(cli, ['get-user', '123'])

        assert result.exit_code == 0
        assert 'User 123' in result.output

    def it_works_with_nested_groups(self) -> None:
        """with_scope works with nested Click groups."""
        import click

        from dioxide.click import (
            configure_dioxide,
            with_scope,
        )

        @service
        class ConfigService:
            def get_setting(self, key: str) -> str:
                return f'value-for-{key}'

        container = configure_dioxide(profile=Profile.TEST)

        @click.group()
        def cli() -> None:
            pass

        @cli.group()
        def config() -> None:
            pass

        @config.command('get')
        @with_scope(container)
        @click.argument('key')
        def config_get(scope: ScopedContainer, key: str) -> None:
            svc = scope.resolve(ConfigService)
            click.echo(svc.get_setting(key))

        runner = CliRunner()
        result = runner.invoke(cli, ['config', 'get', 'database_url'])

        assert result.exit_code == 0
        assert 'value-for-database_url' in result.output


class DescribeAdapterResolution:
    """Tests for resolving adapters via ports."""

    def it_resolves_adapter_for_port(self) -> None:
        """with_scope resolves the correct adapter for a port."""
        import click

        from dioxide.click import (
            configure_dioxide,
            with_scope,
        )

        class EmailPort(Protocol):
            def send(self, to: str) -> str: ...

        @adapter.for_(EmailPort, profile=Profile.TEST)
        class FakeEmailAdapter:
            def send(self, to: str) -> str:
                return f'sent to {to}'

        container = configure_dioxide(profile=Profile.TEST)

        @click.command()
        @with_scope(container)
        @click.argument('to')
        def send_email(scope: ScopedContainer, to: str) -> None:
            email = scope.resolve(EmailPort)
            result = email.send(to)
            click.echo(result)

        runner = CliRunner()
        result = runner.invoke(send_email, ['test@example.com'])

        assert result.exit_code == 0
        assert 'sent to test@example.com' in result.output


class DescribeLifecycleManagement:
    """Tests for lifecycle management with Click."""

    def it_disposes_lifecycle_components_after_command(self) -> None:
        """Lifecycle components are disposed after command completes."""
        import click

        from dioxide.click import (
            configure_dioxide,
            with_scope,
        )

        disposed: list[str] = []

        @service(scope=Scope.REQUEST)
        @lifecycle
        class ResourceService:
            async def initialize(self) -> None:
                pass

            async def dispose(self) -> None:
                disposed.append('resource')

        container = configure_dioxide(profile=Profile.TEST)

        @click.command()
        @with_scope(container)
        def cmd(scope: ScopedContainer) -> None:
            svc = scope.resolve(ResourceService)
            click.echo(f'Resource: {svc}')

        runner = CliRunner()
        result = runner.invoke(cmd)

        assert result.exit_code == 0
        assert 'resource' in disposed


class DescribeTyperCompatibility:
    """Tests for Typer compatibility (via Click)."""

    def it_works_with_typer_commands(self) -> None:
        """with_scope works with Typer (which uses Click internally)."""
        pytest.importorskip('typer')
        import typer

        from dioxide.click import (
            configure_dioxide,
            with_scope,
        )

        @service
        class GreetingService:
            def greet(self, name: str) -> str:
                return f'Hello, {name}!'

        container = configure_dioxide(profile=Profile.TEST)

        app = typer.Typer()

        # Create a Click command with with_scope
        import click

        @click.command()
        @with_scope(container)
        @click.argument('name')
        def greet(scope: ScopedContainer, name: str) -> None:
            svc = scope.resolve(GreetingService)
            typer.echo(svc.greet(name))

        # Register with typer
        app.command()(greet)

        runner = CliRunner()
        result = runner.invoke(greet, ['World'])

        assert result.exit_code == 0
        assert 'Hello, World!' in result.output


class DescribeClickOptions:
    """Tests for Click options and arguments."""

    def it_works_with_click_options(self) -> None:
        """with_scope works with Click options."""
        import click

        from dioxide.click import (
            configure_dioxide,
            with_scope,
        )

        @service
        class FormatterService:
            def format_output(self, text: str, uppercase: bool) -> str:
                return text.upper() if uppercase else text

        container = configure_dioxide(profile=Profile.TEST)

        @click.command()
        @with_scope(container)
        @click.option('--uppercase', is_flag=True, help='Output in uppercase')
        @click.argument('text')
        def format_cmd(scope: ScopedContainer, uppercase: bool, text: str) -> None:
            svc = scope.resolve(FormatterService)
            click.echo(svc.format_output(text, uppercase))

        runner = CliRunner()

        # Without flag
        result = runner.invoke(format_cmd, ['hello'])
        assert result.exit_code == 0
        assert 'hello' in result.output

        # With flag
        result = runner.invoke(format_cmd, ['--uppercase', 'hello'])
        assert result.exit_code == 0
        assert 'HELLO' in result.output

    def it_works_with_multiple_arguments(self) -> None:
        """with_scope works with multiple arguments."""
        import click

        from dioxide.click import (
            configure_dioxide,
            with_scope,
        )

        @service
        class MathService:
            def add(self, a: int, b: int) -> int:
                return a + b

        container = configure_dioxide(profile=Profile.TEST)

        @click.command()
        @with_scope(container)
        @click.argument('a', type=int)
        @click.argument('b', type=int)
        def add_cmd(scope: ScopedContainer, a: int, b: int) -> None:
            svc = scope.resolve(MathService)
            click.echo(f'Result: {svc.add(a, b)}')

        runner = CliRunner()
        result = runner.invoke(add_cmd, ['3', '5'])

        assert result.exit_code == 0
        assert 'Result: 8' in result.output


class DescribeErrorHandling:
    """Tests for error handling in Click commands."""

    def it_handles_command_errors_gracefully(self) -> None:
        """Errors in commands are handled without breaking scope disposal."""
        import click

        from dioxide.click import (
            configure_dioxide,
            with_scope,
        )

        disposed: list[str] = []

        @service(scope=Scope.REQUEST)
        @lifecycle
        class ResourceService:
            async def initialize(self) -> None:
                pass

            async def dispose(self) -> None:
                disposed.append('resource')

        container = configure_dioxide(profile=Profile.TEST)

        @click.command()
        @with_scope(container)
        def failing_cmd(scope: ScopedContainer) -> None:
            scope.resolve(ResourceService)
            raise click.ClickException('Something went wrong')

        runner = CliRunner()
        result = runner.invoke(failing_cmd)

        assert result.exit_code == 1
        assert 'Something went wrong' in result.output
        # Scope should still be disposed even after error
        assert 'resource' in disposed


class DescribeImportErrorHandling:
    """Tests for handling missing Click dependency."""

    def it_raises_import_error_when_click_not_installed(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Module raises ImportError when Click dependencies are unavailable."""
        import dioxide.click as click_module

        # Simulate Click not being installed by setting module-level vars to None
        monkeypatch.setattr(click_module, 'click', None)

        with pytest.raises(ImportError, match='Click is not installed'):
            click_module.configure_dioxide(profile=Profile.TEST)
