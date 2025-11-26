"""Tests for dioxide.testing module.

The testing module provides helpers for writing tests with dioxide,
making it easy to create isolated test containers with fresh state.
"""

from __future__ import annotations

from typing import Protocol

import pytest

from dioxide import (
    Profile,
    adapter,
    lifecycle,
    service,
)
from dioxide.testing import fresh_container


class DescribeFreshContainer:
    """Tests for fresh_container context manager."""

    @pytest.mark.asyncio
    async def it_creates_isolated_container(self) -> None:
        """Each fresh_container call creates a new isolated container."""

        # Arrange
        @service
        class IsolatedService:
            pass

        # Act - create two containers
        async with fresh_container() as container1:
            instance1 = container1.resolve(IsolatedService)

        async with fresh_container() as container2:
            instance2 = container2.resolve(IsolatedService)

        # Assert - different instances from different containers
        assert instance1 is not instance2

    @pytest.mark.asyncio
    async def it_scans_with_provided_profile(self) -> None:
        """Container scans with the specified profile."""

        # Arrange
        class EmailPort(Protocol):
            def get_name(self) -> str: ...

        @adapter.for_(EmailPort, profile=Profile.TEST)
        class TestEmailAdapter:
            def get_name(self) -> str:
                return 'test'

        @adapter.for_(EmailPort, profile=Profile.PRODUCTION)
        class ProdEmailAdapter:
            def get_name(self) -> str:
                return 'production'

        # Act & Assert - TEST profile gets test adapter
        async with fresh_container(profile=Profile.TEST) as container:
            email = container.resolve(EmailPort)
            assert email.get_name() == 'test'

    @pytest.mark.asyncio
    async def it_manages_lifecycle_automatically(self) -> None:
        """Container start/stop called automatically."""
        # Arrange - track lifecycle calls
        init_called = False
        dispose_called = False

        @service
        @lifecycle
        class LifecycleService:
            async def initialize(self) -> None:
                nonlocal init_called
                init_called = True

            async def dispose(self) -> None:
                nonlocal dispose_called
                dispose_called = True

        # Act
        async with fresh_container() as container:
            container.resolve(LifecycleService)
            # initialize should be called before we get here
            assert init_called is True
            assert dispose_called is False

        # Assert - dispose called after exiting context
        assert dispose_called is True

    @pytest.mark.asyncio
    async def it_provides_complete_isolation_between_calls(self) -> None:
        """State from one fresh_container does not leak to another."""

        # Arrange
        @service
        class StatefulService:
            def __init__(self) -> None:
                self.data: list[str] = []

        # Act - modify state in first container
        async with fresh_container() as container1:
            svc1 = container1.resolve(StatefulService)
            svc1.data.append('first')
            assert svc1.data == ['first']

        # Assert - second container has fresh state
        async with fresh_container() as container2:
            svc2 = container2.resolve(StatefulService)
            assert svc2.data == []  # Clean state, no leakage

    @pytest.mark.asyncio
    async def it_works_without_profile(self) -> None:
        """Can create container without specifying profile."""

        # Arrange
        @service
        class UnprofiledService:
            pass

        # Act & Assert - should work without profile
        async with fresh_container() as container:
            instance = container.resolve(UnprofiledService)
            assert instance is not None
            assert isinstance(instance, UnprofiledService)

    @pytest.mark.asyncio
    async def it_accepts_string_profile(self) -> None:
        """Can use string profile instead of Profile enum."""

        # Arrange
        class CachePort(Protocol):
            def cache_type(self) -> str: ...

        @adapter.for_(CachePort, profile='test')
        class TestCacheAdapter:
            def cache_type(self) -> str:
                return 'in-memory'

        # Act & Assert
        async with fresh_container(profile='test') as container:
            cache = container.resolve(CachePort)
            assert cache.cache_type() == 'in-memory'

    @pytest.mark.asyncio
    async def it_accepts_package_parameter(self) -> None:
        """Can specify package to scan."""

        # Arrange
        @service
        class PackagedService:
            pass

        # Act & Assert - should work with package parameter
        # Note: package parameter is passed to scan(), but since we're not
        # actually in a package hierarchy in tests, we just verify it doesn't error
        async with fresh_container(package=None) as container:
            instance = container.resolve(PackagedService)
            assert instance is not None
