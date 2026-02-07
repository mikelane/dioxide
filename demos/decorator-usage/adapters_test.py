"""Test adapters — fast in-memory fakes, same interface."""

from dioxide import adapter
from dioxide.profile_enum import Profile

from ports import AuditLogPort, NotificationPort


@adapter.for_(NotificationPort, profile=Profile.TEST)
class FakeNotifier:
    def __init__(self) -> None:
        self.sent: list[tuple[str, str]] = []

    def notify(self, user: str, message: str) -> None:
        self.sent.append((user, message))


@adapter.for_(AuditLogPort, profile=Profile.TEST)
class FakeAuditLog:
    def __init__(self) -> None:
        self.events: list[str] = []

    def record(self, event: str) -> None:
        self.events.append(event)
