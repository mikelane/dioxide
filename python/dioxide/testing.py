"""Testing utilities for dioxide.

This module provides helpers for writing tests with dioxide, making it easy
to create isolated test containers with fresh state.

Example:
    Using the fresh_container context manager::

        from dioxide.testing import fresh_container
        from dioxide import Profile


        async def test_user_registration():
            async with fresh_container(profile=Profile.TEST) as container:
                service = container.resolve(UserService)
                await service.register('alice@example.com', 'Alice')

                email = container.resolve(EmailPort)
                assert len(email.sent_emails) == 1

    Using with pytest fixtures::

        import pytest
        from dioxide.testing import fresh_container
        from dioxide import Profile


        @pytest.fixture
        async def container():
            async with fresh_container(profile=Profile.TEST) as c:
                yield c


        async def test_something(container):
            service = container.resolve(MyService)
            # ... test with fresh, isolated container
"""

from __future__ import annotations

from collections.abc import AsyncIterator
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
