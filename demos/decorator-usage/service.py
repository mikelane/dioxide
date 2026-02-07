"""Core business logic — uses @service because it never changes."""

from dioxide import service

from ports import AuditLogPort, NotificationPort


@service
class OrderProcessor:
    """Process an order: notify the user and log it."""

    def __init__(
        self, notifier: NotificationPort, audit: AuditLogPort
    ) -> None:
        self._notifier = notifier
        self._audit = audit

    def place_order(self, user: str, item: str) -> None:
        self._notifier.notify(user, f"Order confirmed: {item}")
        self._audit.record(f"{user} ordered {item}")
