"""Testing utilities for dioxide.

This module provides helpers for writing tests with dioxide, making it easy
to create isolated test containers with fresh state.

Instance containers (created via ``Container()`` or ``fresh_container()``) are the
**recommended pattern for testing**. Each container instance has its own singleton
cache, ensuring complete test isolation without state leakage.

For guidance on when to use instance containers vs the global container, see
the Container Patterns guide: :doc:`/docs/user_guide/container_patterns`

Pytest Plugin Usage:
    Add the following to your ``conftest.py`` to enable dioxide pytest fixtures::

        pytest_plugins = ['dioxide.testing']

    This makes the following fixtures available:

    - ``dioxide_container``: Fresh container per test (function-scoped)
    - ``fresh_container_fixture``: Alias for dioxide_container
    - ``dioxide_container_session``: Shared container across tests (session-scoped)

Example using fixtures (recommended)::

    # conftest.py
    pytest_plugins = ['dioxide.testing']


    # test_my_service.py
    async def test_something(dioxide_container):
        dioxide_container.scan(profile=Profile.TEST)
        service = dioxide_container.resolve(MyService)
        # ... test with fresh, isolated container

Example using fresh_container context manager::

    from dioxide.testing import fresh_container
    from dioxide import Profile


    async def test_user_registration():
        async with fresh_container(profile=Profile.TEST) as container:
            service = container.resolve(UserService)
            await service.register('alice@example.com', 'Alice')

            email = container.resolve(EmailPort)
            assert len(email.sent_emails) == 1
"""

from __future__ import annotations

from collections.abc import (
    AsyncIterator,
    Iterator,
)
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

from dioxide.container import Container

if TYPE_CHECKING:
    from dioxide.profile_enum import Profile


@asynccontextmanager
async def fresh_container(
    profile: Profile | str | None = None,
    package: str | None = None,
) -> AsyncIterator[Container]:
    """Create a fresh, isolated container for testing.

    This context manager creates a new Container instance, scans for components,
    manages lifecycle (start/stop), and ensures complete isolation between tests.

    This function does NOT require pytest to be installed.

    Args:
        profile: Profile to scan with (e.g., Profile.TEST). If None, scans all profiles.
        package: Optional package to scan. If None, scans all registered components.

    Yields:
        A fresh Container instance with lifecycle management.

    Example:
        async with fresh_container(profile=Profile.TEST) as container:
            service = container.resolve(UserService)
            # ... test with isolated container
        # Container automatically cleaned up
    """
    container = Container()
    container.scan(package=package, profile=profile)
    async with container:
        yield container


# Pytest fixtures are only defined when pytest is available.
# When pytest_plugins = ['dioxide.testing'] is used, pytest will import this module
# and the fixtures will be available. When pytest is not installed, the fixtures
# simply won't be defined (but fresh_container still works).
#
# We use a function to lazily define fixtures to avoid issues with type checking.


def _define_pytest_fixtures() -> bool:
    """Define pytest fixtures if pytest is available.

    Returns:
        True if fixtures were defined, False otherwise.
    """
    try:
        import pytest  # noqa: PLC0415
    except ImportError:
        return False

    # Define the fixtures in the module's global namespace
    global dioxide_container, fresh_container_fixture, dioxide_container_session

    @pytest.fixture
    def dioxide_container() -> Iterator[Container]:
        """Provide a fresh, isolated Container for each test.

        This fixture creates a new Container instance for each test function,
        ensuring complete isolation between tests. The container is NOT
        pre-scanned - you should call ``container.scan(profile=...)`` in your
        test to register components with the desired profile.

        Yields:
            A fresh Container instance.

        Example::

            async def test_user_service(dioxide_container):
                dioxide_container.scan(profile=Profile.TEST)
                service = dioxide_container.resolve(UserService)
                result = await service.register_user('Alice', 'alice@example.com')
                assert result['name'] == 'Alice'
        """
        yield Container()

    @pytest.fixture
    def fresh_container_fixture() -> Iterator[Container]:
        """Alternative fixture with name matching the context manager.

        This fixture behaves like ``dioxide_container``, providing a fresh
        Container for each test. The name matches the ``fresh_container``
        context manager for consistency.

        Yields:
            A fresh Container instance.

        Example::

            async def test_isolated(fresh_container_fixture):
                fresh_container_fixture.scan(profile=Profile.TEST)
                # Guaranteed fresh container, no state leakage
                pass
        """
        yield Container()

    @pytest.fixture(scope='session')
    def dioxide_container_session() -> Iterator[Container]:
        """Provide a shared Container for the entire test session.

        This session-scoped fixture creates a single Container instance that is
        shared across all tests in the session. Use this for performance when
        tests can safely share container state.

        WARNING: Session-scoped containers share state between tests. Only use
        this when you understand the implications and tests are designed to
        handle shared state.

        Yields:
            A shared Container instance for the session.

        Example::

            # In conftest.py - scan once at session start
            @pytest.fixture(scope='session', autouse=True)
            def setup_session_container(dioxide_container_session):
                dioxide_container_session.scan(profile=Profile.TEST)


            # In tests - just use the pre-scanned container
            async def test_shared_container(dioxide_container_session):
                service = dioxide_container_session.resolve(SharedService)
                # ... use shared container
        """
        yield Container()

    return True


# Define fixtures at module load time if pytest is available
_PYTEST_AVAILABLE = _define_pytest_fixtures()
