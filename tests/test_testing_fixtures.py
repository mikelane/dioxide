"""Tests for pytest fixtures in dioxide.testing.

These tests verify that the pytest fixtures provided by dioxide.testing work correctly
when used via the pytest plugin system (pytest_plugins = ["dioxide.testing"]).
"""

from __future__ import annotations

from typing import Protocol

import pytest

from dioxide import (
    Container,
    Profile,
    adapter,
    lifecycle,
    service,
)

# Load dioxide.testing as a pytest plugin to access its fixtures
pytest_plugins = ['dioxide.testing']


class DescribeDioxideContainerFixture:
    """Tests for the dioxide_container pytest fixture."""

    @pytest.mark.asyncio
    async def it_provides_fresh_container_per_test(
        self,
        dioxide_container: Container,
    ) -> None:
        """The dioxide_container fixture provides a fresh container for each test."""

        # Arrange
        @service
        class TestService:
            pass

        # Act
        dioxide_container.scan(profile=Profile.TEST)
        instance = dioxide_container.resolve(TestService)

        # Assert
        assert instance is not None
        assert isinstance(instance, TestService)

    @pytest.mark.asyncio
    async def it_uses_test_profile_by_default(
        self,
        dioxide_container: Container,
    ) -> None:
        """The container is pre-configured with Profile.TEST."""

        # Arrange
        class StoragePort(Protocol):
            def storage_type(self) -> str: ...

        @adapter.for_(StoragePort, profile=Profile.TEST)
        class TestStorage:
            def storage_type(self) -> str:
                return 'test'

        @adapter.for_(StoragePort, profile=Profile.PRODUCTION)
        class ProdStorage:
            def storage_type(self) -> str:
                return 'production'

        # Act
        dioxide_container.scan(profile=Profile.TEST)
        storage = dioxide_container.resolve(StoragePort)

        # Assert
        assert storage.storage_type() == 'test'

    @pytest.mark.asyncio
    async def it_manages_lifecycle_automatically(
        self,
        dioxide_container: Container,
    ) -> None:
        """The container manages lifecycle components correctly."""
        # Arrange
        init_called = False

        @service
        @lifecycle
        class LifecycleService:
            async def initialize(self) -> None:
                nonlocal init_called
                init_called = True

            async def dispose(self) -> None:
                pass

        # Act
        dioxide_container.scan(profile=Profile.TEST)
        await dioxide_container.start()
        dioxide_container.resolve(LifecycleService)

        # Assert
        assert init_called is True


class DescribeFreshContainerFixture:
    """Tests for the fresh_container pytest fixture (alias for dioxide_container)."""

    @pytest.mark.asyncio
    async def it_provides_isolated_container(
        self,
        fresh_container_fixture: Container,
    ) -> None:
        """The fresh_container fixture provides an isolated container."""

        # Arrange
        @service
        class IsolatedService:
            def __init__(self) -> None:
                self.data: list[str] = []

        # Act
        fresh_container_fixture.scan(profile=Profile.TEST)
        svc = fresh_container_fixture.resolve(IsolatedService)
        svc.data.append('test')

        # Assert
        assert svc.data == ['test']


class DescribeDioxideContainerSessionFixture:
    """Tests for the dioxide_container_session fixture (session-scoped)."""

    @pytest.mark.asyncio
    async def it_provides_shared_container_across_tests(
        self,
        dioxide_container_session: Container,
    ) -> None:
        """The session fixture provides a shared container."""
        # This test just verifies the fixture exists and works
        assert dioxide_container_session is not None

    @pytest.mark.asyncio
    async def it_can_resolve_services(
        self,
        dioxide_container_session: Container,
    ) -> None:
        """The session container can resolve services."""

        # Arrange
        @service
        class SessionService:
            pass

        # Act
        dioxide_container_session.scan(profile=Profile.TEST)
        instance = dioxide_container_session.resolve(SessionService)

        # Assert
        assert instance is not None


class DescribeAsyncFixtures:
    """Tests for async fixture support."""

    @pytest.mark.asyncio
    async def it_supports_async_tests(
        self,
        dioxide_container: Container,
    ) -> None:
        """The fixtures work correctly in async tests."""

        # Arrange
        @service
        class AsyncService:
            async def do_work(self) -> str:
                return 'done'

        # Act
        dioxide_container.scan(profile=Profile.TEST)
        svc = dioxide_container.resolve(AsyncService)
        result = await svc.do_work()

        # Assert
        assert result == 'done'


class DescribePytestPluginSystem:
    """Tests for pytest plugin integration."""

    def it_can_be_loaded_via_pytest_plugins(self) -> None:
        """The dioxide.testing module can be loaded via pytest_plugins."""
        # This test verifies that pytest_plugins = ["dioxide.testing"]
        # properly exposes the fixtures
        import dioxide.testing as testing_module

        # Check that the module has the expected pytest fixture functions
        assert hasattr(testing_module, 'dioxide_container')
        assert hasattr(testing_module, 'fresh_container_fixture')
        assert hasattr(testing_module, 'dioxide_container_session')
