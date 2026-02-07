"""Run with TEST profile — fast in-memory fakes."""

import adapters_test  # noqa: F401 — registers test fakes

from dioxide import Container
from dioxide.profile_enum import Profile
from ports import AuditLogPort, NotificationPort
from service import OrderProcessor

container = Container(profile=Profile.TEST)
processor = container.resolve(OrderProcessor)
processor.place_order("alice", "Rust in Action")

notifier = container.resolve(NotificationPort)
audit = container.resolve(AuditLogPort)
print(f"  Sent:   {notifier.sent}")
print(f"  Logged: {audit.events}")
