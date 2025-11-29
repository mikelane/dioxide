"""Tests for Container(profile=...) constructor parameter.

This feature allows auto-scanning with a profile at construction time,
enabling the more intuitive API pattern:

    async with Container(profile=Profile.PRODUCTION) as container:
        service = container.resolve(UserService)

Instead of the more verbose:

    container = Container()
    container.scan(profile=Profile.PRODUCTION)
    async with container:
        service = container.resolve(UserService)
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


class DescribeContainerProfileParameter:
    """Tests for Container(profile=...) constructor parameter."""

    def it_auto_scans_when_profile_provided(self) -> None:
        """Container(profile=...) automatically scans with that profile."""

        # Arrange
        class EmailPort(Protocol):
            def send(self) -> None: ...

        @adapter.for_(EmailPort, profile=Profile.TEST)
        class FakeEmailAdapter:
            def send(self) -> None:
                pass

        # Act - create container with profile
        container = Container(profile=Profile.TEST)

        # Assert - adapter should be resolvable without explicit scan()
        email = container.resolve(EmailPort)
        assert isinstance(email, FakeEmailAdapter)

    def it_accepts_profile_enum(self) -> None:
        """Container(profile=Profile.TEST) works with Profile enum."""

        # Arrange
        class CachePort(Protocol):
            def get(self, key: str) -> str | None: ...

        @adapter.for_(CachePort, profile=Profile.PRODUCTION)
        class RedisCacheAdapter:
            def get(self, key: str) -> str | None:
                return None

        # Act
        container = Container(profile=Profile.PRODUCTION)

        # Assert
        cache = container.resolve(CachePort)
        assert isinstance(cache, RedisCacheAdapter)

    def it_accepts_string_profile(self) -> None:
        """Container(profile='test') works with string profiles."""

        # Arrange
        class DatabasePort(Protocol):
            def query(self, sql: str) -> list[dict[str, object]]: ...

        @adapter.for_(DatabasePort, profile='staging')
        class StagingDatabaseAdapter:
            def query(self, sql: str) -> list[dict[str, object]]:
                return []

        # Act
        container = Container(profile='staging')

        # Assert
        db = container.resolve(DatabasePort)
        assert isinstance(db, StagingDatabaseAdapter)

    def it_does_not_scan_when_no_profile(self) -> None:
        """Container() without profile does not auto-scan."""

        # Arrange
        @service
        class UnscannedService:
            pass

        # Act - create container WITHOUT profile
        container = Container()

        # Assert - container should be empty (no auto-scan)
        assert container.is_empty()

    def it_maintains_backward_compatibility_with_allowed_packages(self) -> None:
        """Container(allowed_packages=...) still works alongside profile."""

        # Arrange
        class NotificationPort(Protocol):
            def notify(self, msg: str) -> None: ...

        @adapter.for_(NotificationPort, profile=Profile.TEST)
        class FakeNotificationAdapter:
            def notify(self, msg: str) -> None:
                pass

        # Act - create with both parameters
        container = Container(allowed_packages=['dioxide', 'tests'], profile=Profile.TEST)

        # Assert - should work
        notification = container.resolve(NotificationPort)
        assert isinstance(notification, FakeNotificationAdapter)

    @pytest.mark.asyncio
    async def it_works_with_async_context_manager(self) -> None:
        """async with Container(profile=...) as c: works correctly."""
        # Arrange
        initialized = []
        disposed = []

        class StoragePort(Protocol):
            def store(self, data: str) -> None: ...

        @adapter.for_(StoragePort, profile=Profile.TEST)
        @lifecycle
        class FakeStorageAdapter:
            async def initialize(self) -> None:
                initialized.append('storage')

            async def dispose(self) -> None:
                disposed.append('storage')

            def store(self, data: str) -> None:
                pass

        # Act
        async with Container(profile=Profile.TEST) as container:
            storage = container.resolve(StoragePort)
            assert isinstance(storage, FakeStorageAdapter)
            assert 'storage' in initialized

        # Assert
        assert 'storage' in disposed

    def it_registers_services_with_profile(self) -> None:
        """Services decorated with @service are registered when profile provided."""

        # Arrange
        @service
        class UserService:
            def get_user(self, user_id: int) -> dict[str, int]:
                return {'id': user_id}

        # Act
        container = Container(profile=Profile.PRODUCTION)

        # Assert - service should be resolvable
        user_service = container.resolve(UserService)
        assert isinstance(user_service, UserService)
        assert user_service.get_user(42) == {'id': 42}

    def it_injects_dependencies_when_profile_provided(self) -> None:
        """Dependency injection works with profile at construction."""

        # Arrange
        class LogPort(Protocol):
            def log(self, msg: str) -> None: ...

        @adapter.for_(LogPort, profile=Profile.TEST)
        class FakeLogAdapter:
            def __init__(self) -> None:
                self.logs: list[str] = []

            def log(self, msg: str) -> None:
                self.logs.append(msg)

        @service
        class ApplicationService:
            def __init__(self, logger: LogPort) -> None:
                self.logger = logger

            def run(self) -> None:
                self.logger.log('running')

        # Act
        container = Container(profile=Profile.TEST)
        app = container.resolve(ApplicationService)

        # Assert
        app.run()
        log_adapter = container.resolve(LogPort)
        assert isinstance(log_adapter, FakeLogAdapter)
        assert 'running' in log_adapter.logs


class DescribeContainerProfileParameterEdgeCases:
    """Edge cases for Container(profile=...) parameter."""

    def it_allows_explicit_scan_after_profile_construction(self) -> None:
        """Container(profile=...) followed by scan() works (no-op for same profile)."""

        # Arrange
        class QueuePort(Protocol):
            def push(self, item: str) -> None: ...

        @adapter.for_(QueuePort, profile=Profile.DEVELOPMENT)
        class DevQueueAdapter:
            def push(self, item: str) -> None:
                pass

        # Act - create with profile, then scan again
        container = Container(profile=Profile.DEVELOPMENT)
        # Second scan should not raise (idempotent behavior for already-registered types)
        container.scan(profile=Profile.DEVELOPMENT)

        # Assert
        queue = container.resolve(QueuePort)
        assert isinstance(queue, DevQueueAdapter)

    def it_respects_profile_filtering(self) -> None:
        """Only adapters matching the profile are registered."""

        # Arrange
        class MetricsPort(Protocol):
            def record(self, name: str, value: float) -> None: ...

        @adapter.for_(MetricsPort, profile=Profile.PRODUCTION)
        class DatadogMetricsAdapter:
            def record(self, name: str, value: float) -> None:
                pass

        @adapter.for_(MetricsPort, profile=Profile.TEST)
        class FakeMetricsAdapter:
            def record(self, name: str, value: float) -> None:
                pass

        # Act - create with TEST profile
        container = Container(profile=Profile.TEST)

        # Assert - should get FakeMetricsAdapter, not DatadogMetricsAdapter
        metrics = container.resolve(MetricsPort)
        assert isinstance(metrics, FakeMetricsAdapter)
        assert not isinstance(metrics, DatadogMetricsAdapter)
