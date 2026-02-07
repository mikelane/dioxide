"""Demo: dioxide catches missing bindings at startup."""

from typing import Protocol

from dioxide import Container, Profile, adapter, service


class NotificationPort(Protocol):
    def send(self, to: str, message: str) -> None: ...


@service
class OrderService:
    def __init__(self, notifications: NotificationPort):
        self.notifications = notifications

    def place_order(self, item: str) -> str:
        self.notifications.send("warehouse", f"Ship {item}")
        return f"Order placed: {item}"


# Forgot to register an adapter for NotificationPort!
# In other frameworks, this silently passes until runtime.
# dioxide catches it immediately:

container = Container()
container.scan(profile=Profile.PRODUCTION)

print("Resolving OrderService...")
order_svc = container.resolve(OrderService)
