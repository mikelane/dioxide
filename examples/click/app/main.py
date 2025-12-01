"""Click CLI application with dioxide dependency injection.

This module demonstrates how to integrate dioxide's hexagonal architecture
with Click CLI applications using the dioxide.click integration module.

Key patterns demonstrated:
- Single function setup with configure_dioxide()
- Per-command scoping with @with_scope decorator
- Profile-based adapter selection via environment variable
- Clean separation of domain logic from CLI concerns
"""

from __future__ import annotations

import os
import sys

import click

from dioxide import Profile
from dioxide.click import (
    configure_dioxide,
    with_scope,
)

from .domain.ports import (
    DatabasePort,
    EmailPort,
)
from .domain.services import UserService

# Get profile from environment, default to 'development'
profile_name = os.getenv("PROFILE", "development")
profile = Profile(profile_name)

# Configure container - scans for components in the 'app' package
# This returns a Container that we'll use with @with_scope
container = configure_dioxide(profile=profile, packages=["app"])


@click.group()
@click.version_option(version="0.1.0")
def cli() -> None:
    """User management CLI demonstrating dioxide dependency injection.

    This CLI tool uses hexagonal architecture with different adapters
    based on the active profile (set via PROFILE environment variable).

    Examples:

        # Development mode (default)
        python -m app.main users create "Alice" alice@example.com

        # Test mode
        PROFILE=test python -m app.main users create "Alice" alice@example.com
    """
    pass


@cli.group()
def users() -> None:
    """User management commands."""
    pass


@users.command("create")
@with_scope(container)
@click.argument("name")
@click.argument("email")
def create_user(scope, name: str, email: str) -> None:
    """Create a new user and send welcome email.

    This command demonstrates:
    - Dependency injection via scope.resolve(UserService)
    - Service orchestrates domain logic (create + email)
    - Adapters used are determined by active profile

    In production: User saved to PostgreSQL, email sent via SendGrid
    In tests: User saved to in-memory fake, email recorded
    In development: User saved to in-memory, email logged to console

    Arguments:

        NAME: User's full name (e.g., "Alice Smith")

        EMAIL: User's email address (e.g., alice@example.com)
    """
    service = scope.resolve(UserService)
    user = service.register_user(name, email)
    click.echo(f"Created user {user['id']}: {user['name']} <{user['email']}>")


@users.command("get")
@with_scope(container)
@click.argument("user_id")
def get_user(scope, user_id: str) -> None:
    """Get a user by ID.

    Arguments:

        USER_ID: Unique identifier for the user
    """
    service = scope.resolve(UserService)
    user = service.get_user(user_id)

    if user is None:
        click.echo(f"Error: User {user_id} not found", err=True)
        sys.exit(1)

    click.echo(f"User {user['id']}: {user['name']} <{user['email']}>")


@users.command("list")
@with_scope(container)
def list_users(scope) -> None:
    """List all users."""
    service = scope.resolve(UserService)
    users = service.list_all_users()

    if not users:
        click.echo("No users found.")
        return

    click.echo("Users:")
    for user in users:
        click.echo(f"  {user['id']}: {user['name']} <{user['email']}>")


@cli.command()
def health() -> None:
    """Health check - shows status and active profile."""
    click.echo(f"Status: healthy")
    click.echo(f"Profile: {profile.value}")


@cli.command()
@with_scope(container)
def debug(scope) -> None:
    """Debug command - shows container state.

    This command is useful for verifying that the correct adapters
    are loaded for the current profile.
    """
    click.echo(f"Profile: {profile.value}")
    click.echo(f"Container: {container}")

    # Resolve adapters to show what's registered
    try:
        db = scope.resolve(DatabasePort)
        click.echo(f"Database adapter: {db.__class__.__name__}")
    except Exception as e:
        click.echo(f"Database adapter: ERROR - {e}")

    try:
        email = scope.resolve(EmailPort)
        click.echo(f"Email adapter: {email.__class__.__name__}")
    except Exception as e:
        click.echo(f"Email adapter: ERROR - {e}")


def main() -> None:
    """Entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
