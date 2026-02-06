"""Two adapters for scan stats counting."""

from typing import Protocol

from dioxide import (
    Profile,
    adapter,
)


class NotificationPort(Protocol):
    def notify(self, message: str) -> None: ...


class StoragePort(Protocol):
    def store(self, key: str, value: str) -> None: ...


@adapter.for_(NotificationPort, profile=Profile.PRODUCTION)
class EmailNotifier:
    def notify(self, message: str) -> None:
        pass


@adapter.for_(StoragePort, profile=Profile.PRODUCTION)
class DatabaseStorage:
    def store(self, key: str, value: str) -> None:
        pass
