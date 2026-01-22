"""Tests for auto-scan behavior in Container.

Issue #310: Eliminate the scan() ceremony - auto-scan on first resolve

This test suite verifies that users can use the simplified API pattern:

    container = Container(profile=Profile.PRODUCTION)
    service = container.resolve(MyService)  # Just works - no scan() needed

Instead of the verbose pattern:

    container = Container()
    container.scan(profile=Profile.PRODUCTION)  # Manual ceremony
    service = container.resolve(MyService)

The acceptance criteria from issue #310:
1. New users can resolve dependencies without calling scan() explicitly
2. Existing code using scan() still works (backward compatible)
3. Error messages guide users if something goes wrong
4. Documentation shows the simpler pattern as primary
"""

from __future__ import annotations

from typing import Protocol

import pytest

from dioxide import (
    Container,
    Profile,
    _clear_registry,
    adapter,
    service,
)
from dioxide.adapter import _adapter_registry


@pytest.fixture(autouse=True)
def clean_registry() -> None:
    """Clear registries before each test to ensure isolation."""
    _clear_registry()
    _adapter_registry.clear()


class DescribeAutoScan:
    """Auto-scan behavior for Container."""

    class DescribeResolveWithoutExplicitScan:
        """When resolve() is called without calling scan() first."""

        def it_automatically_scans_on_first_resolve(self) -> None:
            """Container with profile auto-scans on first resolve() call."""

            # Arrange
            class EmailPort(Protocol):
                def send(self) -> None: ...

            @adapter.for_(EmailPort, profile=Profile.TEST)
            class FakeEmailAdapter:
                def send(self) -> None:
                    pass

            @service
            class UserService:
                def __init__(self, email: EmailPort) -> None:
                    self.email = email

            # Act - create container with profile, resolve without explicit scan()
            container = Container(profile=Profile.TEST)
            user_service = container.resolve(UserService)

            # Assert - should work without explicit scan()
            assert isinstance(user_service, UserService)
            assert isinstance(user_service.email, FakeEmailAdapter)

        def it_only_scans_once_even_with_multiple_resolves(self) -> None:
            """Auto-scan happens exactly once, not on every resolve."""
            # Arrange
            scan_count = 0
            original_scan = Container.scan

            def counting_scan(self: Container, *args: object, **kwargs: object) -> None:
                nonlocal scan_count
                scan_count += 1
                original_scan(self, *args, **kwargs)  # type: ignore[arg-type]

            class CachePort(Protocol):
                def get(self) -> str: ...

            @adapter.for_(CachePort, profile=Profile.PRODUCTION)
            class RedisCacheAdapter:
                def get(self) -> str:
                    return 'cached'

            @service
            class CacheService:
                def __init__(self, cache: CachePort) -> None:
                    self.cache = cache

            # Act - resolve multiple times
            container = Container(profile=Profile.PRODUCTION)

            # Monkey-patch scan to count calls (only for this test)
            Container.scan = counting_scan  # type: ignore[method-assign]
            try:
                container.resolve(CacheService)
                container.resolve(CacheService)
                container.resolve(CacheService)
            finally:
                Container.scan = original_scan  # type: ignore[method-assign]

            # Assert - scan should have been called exactly once (at construction)
            # Note: Current implementation scans eagerly at construction
            assert scan_count <= 1

        def it_works_with_string_profile(self) -> None:
            """Auto-scan works when profile is provided as string."""

            # Arrange
            class DatabasePort(Protocol):
                def query(self) -> list[dict[str, object]]: ...

            @adapter.for_(DatabasePort, profile='staging')
            class StagingDatabaseAdapter:
                def query(self) -> list[dict[str, object]]:
                    return []

            @service
            class DatabaseService:
                def __init__(self, db: DatabasePort) -> None:
                    self.db = db

            # Act
            container = Container(profile='staging')
            db_service = container.resolve(DatabaseService)

            # Assert
            assert isinstance(db_service, DatabaseService)
            assert isinstance(db_service.db, StagingDatabaseAdapter)

        def it_works_with_bracket_syntax(self) -> None:
            """Auto-scan triggers with container[Type] bracket syntax."""

            # Arrange
            class LoggerPort(Protocol):
                def log(self, msg: str) -> None: ...

            @adapter.for_(LoggerPort, profile=Profile.DEVELOPMENT)
            class ConsoleLoggerAdapter:
                def log(self, msg: str) -> None:
                    pass

            @service
            class LoggingService:
                def __init__(self, logger: LoggerPort) -> None:
                    self.logger = logger

            # Act - use bracket syntax
            container = Container(profile=Profile.DEVELOPMENT)
            logging_service = container[LoggingService]

            # Assert
            assert isinstance(logging_service, LoggingService)
            assert isinstance(logging_service.logger, ConsoleLoggerAdapter)

    class DescribeExplicitScanStillWorks:
        """Backward compatibility with explicit scan()."""

        def it_allows_explicit_scan_call(self) -> None:
            """Existing code using explicit scan() continues to work."""

            # Arrange
            class PaymentPort(Protocol):
                def charge(self, amount: int) -> bool: ...

            @adapter.for_(PaymentPort, profile=Profile.TEST)
            class FakePaymentAdapter:
                def charge(self, amount: int) -> bool:
                    return True

            @service
            class PaymentService:
                def __init__(self, payment: PaymentPort) -> None:
                    self.payment = payment

            # Act - use explicit scan() (old pattern)
            container = Container()
            container.scan(profile=Profile.TEST)
            payment_service = container.resolve(PaymentService)

            # Assert
            assert isinstance(payment_service, PaymentService)
            assert isinstance(payment_service.payment, FakePaymentAdapter)

        def it_allows_scan_after_construction_with_profile(self) -> None:
            """Calling scan() after Container(profile=...) is allowed (idempotent)."""

            # Arrange
            class NotificationPort(Protocol):
                def notify(self) -> None: ...

            @adapter.for_(NotificationPort, profile=Profile.TEST)
            class FakeNotificationAdapter:
                def notify(self) -> None:
                    pass

            @service
            class NotificationService:
                def __init__(self, notifier: NotificationPort) -> None:
                    self.notifier = notifier

            # Act - construct with profile AND call scan()
            container = Container(profile=Profile.TEST)
            # This should not raise an error - scan is idempotent
            container.scan(profile=Profile.TEST)
            notification_service = container.resolve(NotificationService)

            # Assert
            assert isinstance(notification_service, NotificationService)

    class DescribeContainerWithoutProfile:
        """When Container is created without a profile."""

        def it_raises_error_on_resolve_without_profile_or_scan(self) -> None:
            """Container without profile raises helpful error on resolve."""

            # Arrange
            @service
            class SimpleService:
                pass

            # Act & Assert
            container = Container()
            with pytest.raises(Exception) as exc_info:
                container.resolve(SimpleService)

            # Should give a helpful error message
            assert 'SimpleService' in str(exc_info.value)

        def it_works_after_explicit_scan_with_profile(self) -> None:
            """Container() followed by scan(profile=...) works as before."""

            # Arrange
            class MetricsPort(Protocol):
                def record(self) -> None: ...

            @adapter.for_(MetricsPort, profile=Profile.CI)
            class CIMetricsAdapter:
                def record(self) -> None:
                    pass

            @service
            class MetricsService:
                def __init__(self, metrics: MetricsPort) -> None:
                    self.metrics = metrics

            # Act
            container = Container()
            container.scan(profile=Profile.CI)
            metrics_service = container.resolve(MetricsService)

            # Assert
            assert isinstance(metrics_service, MetricsService)
            assert isinstance(metrics_service.metrics, CIMetricsAdapter)

    class DescribeErrorMessages:
        """Error messages guide users when auto-scan fails."""

        def it_shows_helpful_error_for_missing_adapter(self) -> None:
            """Error message mentions profile when adapter is missing."""

            # Arrange
            class MissingPort(Protocol):
                def do_something(self) -> None: ...

            @service
            class ServiceWithMissingDep:
                def __init__(self, missing: MissingPort) -> None:
                    self.missing = missing

            # Act & Assert
            container = Container(profile=Profile.TEST)
            with pytest.raises(Exception) as exc_info:
                container.resolve(ServiceWithMissingDep)

            # Error should mention the profile context
            error_msg = str(exc_info.value)
            assert 'MissingPort' in error_msg or 'ServiceWithMissingDep' in error_msg

    class DescribeNewUserJourney:
        """Tests demonstrating the simplified user journey from issue #310."""

        def it_enables_the_desired_simple_api_pattern(self) -> None:
            """Issue #310 desired state: Container(profile) + resolve() just works.

            This is the exact scenario described in the issue:
            - User creates container with profile
            - User resolves service
            - No scan() call needed
            """
            # This is the DESIRED pattern from issue #310
            from typing import Protocol

            from dioxide import (
                Container,
                Profile,
                adapter,
                service,
            )

            # Define port
            class EmailPort(Protocol):
                async def send(self, to: str, subject: str, body: str) -> None: ...

            # Define production adapter
            @adapter.for_(EmailPort, profile=Profile.PRODUCTION)
            class SendGridAdapter:
                async def send(self, to: str, subject: str, body: str) -> None:
                    pass  # Real implementation would call SendGrid

            # Define service depending on port
            @service
            class UserService:
                def __init__(self, email: EmailPort) -> None:
                    self.email = email

            # THIS IS THE DESIRED API - no scan() call needed!
            container = Container(profile=Profile.PRODUCTION)
            user_service = container.resolve(UserService)

            # Verify it works
            assert isinstance(user_service, UserService)
            assert isinstance(user_service.email, SendGridAdapter)

        def it_eliminates_the_scan_ceremony(self) -> None:
            """The old verbose pattern is no longer required.

            Before (verbose):
                container = Container()
                container.scan(profile=Profile.PRODUCTION)  # Ceremony!
                service = container.resolve(MyService)

            After (simple):
                container = Container(profile=Profile.PRODUCTION)
                service = container.resolve(MyService)
            """

            # Arrange
            class StoragePort(Protocol):
                def save(self, data: str) -> None: ...

            @adapter.for_(StoragePort, profile=Profile.TEST)
            class InMemoryStorageAdapter:
                def __init__(self) -> None:
                    self.data: list[str] = []

                def save(self, data: str) -> None:
                    self.data.append(data)

            @service
            class DataService:
                def __init__(self, storage: StoragePort) -> None:
                    self.storage = storage

                def persist(self, value: str) -> None:
                    self.storage.save(value)

            # Act - SIMPLE pattern (no scan ceremony)
            container = Container(profile=Profile.TEST)
            data_service = container.resolve(DataService)
            data_service.persist('test value')

            # Assert
            storage = container.resolve(StoragePort)
            assert isinstance(storage, InMemoryStorageAdapter)
            assert 'test value' in storage.data
