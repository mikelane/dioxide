"""Ports: the contracts your business logic depends on."""

from typing import Protocol


class NotificationPort(Protocol):
    """Send a notification to a user."""

    def notify(self, user: str, message: str) -> None: ...


class AuditLogPort(Protocol):
    """Record an event for compliance."""

    def record(self, event: str) -> None: ...
