"""Demo: correct wiring resolves instantly."""

from typing import Protocol

from dioxide import Container, Profile, adapter, service


class NotificationPort(Protocol):
    def send(self, to: str, message: str) -> None: ...


@adapter.for_(NotificationPort, profile=Profile.PRODUCTION)
class SlackNotifier:
    def send(self, to: str, message: str) -> None:
        print(f"  Slack -> {to}: {message}")


@service
class OrderService:
    def __init__(self, notifications: NotificationPort):
        self.notifications = notifications

    def place_order(self, item: str) -> str:
        self.notifications.send("warehouse", f"Ship {item}")
        return f"Order placed: {item}"


container = Container()
container.scan(profile=Profile.PRODUCTION)

print("Resolving OrderService...")
order_svc = container.resolve(OrderService)
print(f"  OK: {type(order_svc).__name__}")
result = order_svc.place_order("widget")
print(f"  {result}")
