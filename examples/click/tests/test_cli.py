"""Tests for the Click CLI application.

These tests demonstrate how to test a Click CLI that uses dioxide
for dependency injection. Tests use the TEST profile to get fast
fake adapters.
"""

from __future__ import annotations

import pytest
from click.testing import CliRunner

from dioxide import (
    Container,
    Profile,
    _clear_registry,
)
from dioxide.click import (
    configure_dioxide,
    with_scope,
)


@pytest.fixture(autouse=True)
def clear_registry() -> None:
    """Clear the global registry before each test."""
    _clear_registry()


class DescribeHealthCommand:
    """Tests for the health check command."""

    def it_shows_healthy_status(self) -> None:
        """Health command returns healthy status."""
        import click

        @click.command()
        def health() -> None:
            click.echo("Status: healthy")

        runner = CliRunner()
        result = runner.invoke(health)

        assert result.exit_code == 0
        assert "healthy" in result.output


class DescribeUserCommands:
    """Tests for user management commands."""

    def it_creates_a_user_successfully(self) -> None:
        """Create user command creates user and sends welcome email."""
        import click

        from dioxide import service

        class EmailPort:
            def send_welcome_email(self, to: str, name: str) -> None: ...

        class DatabasePort:
            def create_user(self, name: str, email: str) -> dict: ...

        from dioxide import adapter

        @adapter.for_(DatabasePort, profile=Profile.TEST)
        class FakeDB:
            def __init__(self) -> None:
                self.users: list[dict] = []

            def create_user(self, name: str, email: str) -> dict:
                user = {"id": "1", "name": name, "email": email}
                self.users.append(user)
                return user

        @adapter.for_(EmailPort, profile=Profile.TEST)
        class FakeEmail:
            def __init__(self) -> None:
                self.sent: list[dict] = []

            def send_welcome_email(self, to: str, name: str) -> None:
                self.sent.append({"to": to, "name": name})

        @service
        class UserService:
            def __init__(self, db: DatabasePort, email: EmailPort) -> None:
                self.db = db
                self.email = email

            def register_user(self, name: str, email: str) -> dict:
                user = self.db.create_user(name, email)
                self.email.send_welcome_email(email, name)
                return user

        container = configure_dioxide(profile=Profile.TEST)

        @click.command()
        @with_scope(container)
        @click.argument("name")
        @click.argument("email")
        def create(scope, name: str, email: str) -> None:
            svc = scope.resolve(UserService)
            user = svc.register_user(name, email)
            click.echo(f"Created user {user['id']}: {user['name']}")

        runner = CliRunner()
        result = runner.invoke(create, ["Alice Smith", "alice@example.com"])

        assert result.exit_code == 0
        assert "Created user 1: Alice Smith" in result.output

    def it_handles_user_not_found(self) -> None:
        """Get user command returns error when user not found."""
        import sys

        import click

        from dioxide import adapter, service

        class DatabasePort:
            def get_user(self, user_id: str) -> dict | None: ...

        @adapter.for_(DatabasePort, profile=Profile.TEST)
        class FakeDB:
            def get_user(self, user_id: str) -> dict | None:
                return None

        @service
        class UserService:
            def __init__(self, db: DatabasePort) -> None:
                self.db = db

            def get_user(self, user_id: str) -> dict | None:
                return self.db.get_user(user_id)

        container = configure_dioxide(profile=Profile.TEST)

        @click.command()
        @with_scope(container)
        @click.argument("user_id")
        def get(scope, user_id: str) -> None:
            svc = scope.resolve(UserService)
            user = svc.get_user(user_id)
            if user is None:
                click.echo(f"Error: User {user_id} not found", err=True)
                sys.exit(1)
            click.echo(f"User: {user['name']}")

        runner = CliRunner()
        result = runner.invoke(get, ["999"])

        assert result.exit_code == 1
        assert "User 999 not found" in result.output

    def it_lists_all_users(self) -> None:
        """List users command shows all users."""
        import click

        from dioxide import adapter, service

        class DatabasePort:
            def list_users(self) -> list[dict]: ...

        @adapter.for_(DatabasePort, profile=Profile.TEST)
        class FakeDB:
            def list_users(self) -> list[dict]:
                return [
                    {"id": "1", "name": "Alice", "email": "alice@example.com"},
                    {"id": "2", "name": "Bob", "email": "bob@example.com"},
                ]

        @service
        class UserService:
            def __init__(self, db: DatabasePort) -> None:
                self.db = db

            def list_users(self) -> list[dict]:
                return self.db.list_users()

        container = configure_dioxide(profile=Profile.TEST)

        @click.command()
        @with_scope(container)
        def list_cmd(scope) -> None:
            svc = scope.resolve(UserService)
            users = svc.list_users()
            for user in users:
                click.echo(f"{user['id']}: {user['name']}")

        runner = CliRunner()
        result = runner.invoke(list_cmd)

        assert result.exit_code == 0
        assert "1: Alice" in result.output
        assert "2: Bob" in result.output


class DescribeScopeIsolation:
    """Tests for scope isolation between commands."""

    def it_creates_fresh_scope_per_command(self) -> None:
        """Each command invocation gets a fresh scope."""
        import click

        from dioxide import Scope, service

        scope_ids: list[str] = []

        @service(scope=Scope.REQUEST)
        class RequestContext:
            def __init__(self) -> None:
                import uuid

                self.request_id = str(uuid.uuid4())

        container = configure_dioxide(profile=Profile.TEST)

        @click.command()
        @with_scope(container)
        def cmd(scope) -> None:
            ctx = scope.resolve(RequestContext)
            scope_ids.append(ctx.request_id)

        runner = CliRunner()
        runner.invoke(cmd)
        runner.invoke(cmd)

        assert len(scope_ids) == 2
        assert scope_ids[0] != scope_ids[1]


class DescribeClickGroups:
    """Tests for Click group support."""

    def it_works_with_click_groups(self) -> None:
        """Commands in groups work with with_scope."""
        import click

        from dioxide import service

        @service
        class ConfigService:
            def get_setting(self, key: str) -> str:
                return f"value-for-{key}"

        container = configure_dioxide(profile=Profile.TEST)

        @click.group()
        def cli() -> None:
            pass

        @cli.command()
        @with_scope(container)
        @click.argument("key")
        def get(scope, key: str) -> None:
            svc = scope.resolve(ConfigService)
            click.echo(svc.get_setting(key))

        runner = CliRunner()
        result = runner.invoke(cli, ["get", "database_url"])

        assert result.exit_code == 0
        assert "value-for-database_url" in result.output
