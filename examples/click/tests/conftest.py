"""Pytest configuration and fixtures for Click CLI tests.

This module provides fixtures that set up the test environment with
dioxide's test profile, giving tests access to fast fake adapters.
"""

from __future__ import annotations

import pytest
from click.testing import CliRunner

from dioxide import (
    Container,
    Profile,
    _clear_registry,
)
from dioxide.click import configure_dioxide


@pytest.fixture(autouse=True)
def clear_registry() -> None:
    """Clear the global registry before each test for isolation."""
    _clear_registry()


@pytest.fixture
def runner() -> CliRunner:
    """Create a Click CLI test runner."""
    return CliRunner()


@pytest.fixture
def container() -> Container:
    """Create a test container with TEST profile.

    This fixture creates a fresh container for each test, ensuring
    isolation between tests.
    """
    # Import adapters to register them
    import app.adapters.fakes  # noqa: F401

    # Import services to register them
    import app.domain.services  # noqa: F401

    return configure_dioxide(profile=Profile.TEST)


@pytest.fixture
def db(container: Container) -> "FakeDatabaseAdapter":  # noqa: F821
    """Get the fake database adapter for assertions.

    This fixture resolves the database port and returns the fake
    adapter, allowing tests to verify database state.
    """
    from app.adapters.fakes import FakeDatabaseAdapter
    from app.domain.ports import DatabasePort

    # Create a scope to resolve the adapter
    import asyncio

    async def get_adapter():
        async with container.create_scope() as scope:
            return scope.resolve(DatabasePort)

    adapter = asyncio.run(get_adapter())
    assert isinstance(adapter, FakeDatabaseAdapter)
    return adapter


@pytest.fixture
def email(container: Container) -> "FakeEmailAdapter":  # noqa: F821
    """Get the fake email adapter for assertions.

    This fixture resolves the email port and returns the fake
    adapter, allowing tests to verify emails "sent".
    """
    from app.adapters.fakes import FakeEmailAdapter
    from app.domain.ports import EmailPort

    # Create a scope to resolve the adapter
    import asyncio

    async def get_adapter():
        async with container.create_scope() as scope:
            return scope.resolve(EmailPort)

    adapter = asyncio.run(get_adapter())
    assert isinstance(adapter, FakeEmailAdapter)
    return adapter
