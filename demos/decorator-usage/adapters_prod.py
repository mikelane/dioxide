"""Production adapters — real integrations, swapped per profile."""

from dioxide import adapter
from dioxide.profile_enum import Profile

from ports import AuditLogPort, NotificationPort


@adapter.for_(NotificationPort, profile=Profile.PRODUCTION)
class SlackNotifier:
    def notify(self, user: str, message: str) -> None:
        print(f"  [Slack] @{user}: {message}")


@adapter.for_(AuditLogPort, profile=Profile.PRODUCTION)
class PostgresAuditLog:
    def record(self, event: str) -> None:
        print(f"  [Postgres] INSERT INTO audit_log: {event}")
