"""Tests for Container.__repr__() and ScopedContainer.__repr__()."""

from __future__ import annotations

from typing import Protocol

from dioxide import (
    Container,
    Profile,
    ScopedContainer,
    adapter,
    service,
)


class DescribeContainerRepr:
    """Tests for Container.__repr__() output."""

    def it_shows_no_profile_when_unscanned(self) -> None:
        container = Container()

        result = repr(container)

        assert result == 'Container(profile=None, ports=0, services=0)'

    def it_shows_profile_and_zero_counts_when_empty(self) -> None:
        container = Container(profile=Profile.TEST)

        result = repr(container)

        assert result == 'Container(profile=Profile.TEST, ports=0, services=0)'

    def it_counts_adapters_registered_via_scan(self) -> None:
        class NotificationPort(Protocol):
            def notify(self) -> None: ...

        @adapter.for_(NotificationPort, profile=Profile.TEST)
        class FakeNotificationAdapter:
            def notify(self) -> None:
                pass

        container = Container(profile=Profile.TEST)

        result = repr(container)

        assert 'ports=1' in result

    def it_counts_services_registered_via_scan(self) -> None:
        @service
        class GreetingService:
            pass

        container = Container(profile=Profile.TEST)

        result = repr(container)

        assert 'services=1' in result

    def it_shows_combined_adapter_and_service_counts(self) -> None:
        class StoragePort(Protocol):
            def store(self, data: str) -> None: ...

        @adapter.for_(StoragePort, profile=Profile.PRODUCTION)
        class FileStorageAdapter:
            def store(self, data: str) -> None:
                pass

        @service
        class DataProcessor:
            def __init__(self, storage: StoragePort) -> None:
                self.storage = storage

        container = Container(profile=Profile.PRODUCTION)

        result = repr(container)

        assert 'ports=1' in result
        assert 'services=1' in result

    def it_shows_production_profile(self) -> None:
        container = Container(profile=Profile.PRODUCTION)

        result = repr(container)

        assert 'profile=Profile.PRODUCTION' in result

    def it_shows_string_profile_as_profile_instance(self) -> None:
        container = Container()
        container.scan(profile='staging')

        result = repr(container)

        assert 'profile=Profile.STAGING' in result

    def it_shows_profile_all_wildcard(self) -> None:
        container = Container()
        container.scan(profile=Profile.ALL)

        result = repr(container)

        assert 'profile=Profile.ALL' in result


class DescribeScopedContainerRepr:
    """Tests for ScopedContainer.__repr__() output."""

    def it_shows_profile_and_parent_type(self) -> None:
        container = Container(profile=Profile.TEST)
        scoped = ScopedContainer(parent=container, scope_id='test-scope-id')

        result = repr(scoped)

        assert result == 'ScopedContainer(profile=Profile.TEST, parent=Container)'

    def it_shows_no_profile_when_parent_has_none(self) -> None:
        container = Container()
        scoped = ScopedContainer(parent=container, scope_id='test-scope-id')

        result = repr(scoped)

        assert result == 'ScopedContainer(profile=None, parent=Container)'
