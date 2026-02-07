"""Run with TEST profile — fast in-memory fakes."""

from dioxide import Container
from dioxide.profile_enum import Profile

container = Container()
container.scan("service")
container.scan("adapters_test", profile=Profile.TEST)

from ports import AuditLogPort, NotificationPort
from service import OrderProcessor

processor = container.resolve(OrderProcessor)
processor.place_order("alice", "Rust in Action")

notifier = container.resolve(NotificationPort)
audit = container.resolve(AuditLogPort)
print(f"  Sent:   {notifier.sent}")
print(f"  Logged: {audit.events}")
