"""Demonstration of circular dependency detection in dioxide.

This file shows what happens when you have a circular dependency.
dioxide detects the cycle at container initialization and raises a clear error.

Run this file to see the error message:
    python problem.py

Expected output:
    CircularDependencyError showing the cycle path
"""

from typing import Protocol

from dioxide import Container, Profile, adapter, service


# =============================================================================
# The Problem: Two services that depend on each other
# =============================================================================


class OrderServicePort(Protocol):
    """Port for order operations."""

    async def create_order(self, customer_id: str, items: list) -> dict:
        ...

    async def get_order(self, order_id: str) -> dict:
        ...


class NotificationServicePort(Protocol):
    """Port for notification operations."""

    async def notify_order_created(self, order: dict) -> None:
        ...

    async def notify_order_status_change(self, order_id: str, new_status: str) -> None:
        ...


# The circular dependency:
# OrderService needs NotificationService to send notifications
# NotificationService needs OrderService to get order details


@adapter.for_(OrderServicePort, profile=Profile.PRODUCTION)
class OrderService:
    """Order service that sends notifications on order creation.

    Problem: Depends on NotificationService.
    """

    def __init__(self, notifications: NotificationServicePort) -> None:
        self.notifications = notifications
        self._orders: dict[str, dict] = {}
        self._next_id = 1

    async def create_order(self, customer_id: str, items: list) -> dict:
        """Create order and notify customer."""
        order = {
            "id": f"order-{self._next_id}",
            "customer_id": customer_id,
            "items": items,
            "status": "created",
        }
        self._next_id += 1
        self._orders[order["id"]] = order

        # This creates the dependency on NotificationService
        await self.notifications.notify_order_created(order)

        return order

    async def get_order(self, order_id: str) -> dict:
        """Get order details."""
        return self._orders.get(order_id, {})


@adapter.for_(NotificationServicePort, profile=Profile.PRODUCTION)
class NotificationService:
    """Notification service that needs order details.

    Problem: Depends on OrderService to get order details for notifications.
    """

    def __init__(self, orders: OrderServicePort) -> None:
        # This creates the circular dependency!
        self.orders = orders

    async def notify_order_created(self, order: dict) -> None:
        """Send notification for new order."""
        print(f"[Email] New order {order['id']} created")

    async def notify_order_status_change(self, order_id: str, new_status: str) -> None:
        """Send notification for status change.

        This method needs to look up order details (customer email, etc.)
        which is why NotificationService depends on OrderService.
        """
        order = await self.orders.get_order(order_id)
        print(f"[Email] Order {order_id} status changed to {new_status}")
        print(f"        Customer: {order.get('customer_id', 'unknown')}")


# =============================================================================
# Demonstration
# =============================================================================


def main() -> None:
    """Demonstrate circular dependency detection."""
    print("=" * 70)
    print("Circular Dependency Detection Example")
    print("=" * 70)
    print()
    print("Attempting to scan container with circular dependency...")
    print()
    print("Dependency chain:")
    print("  OrderService -> NotificationServicePort")
    print("  NotificationService -> OrderServicePort")
    print("  OrderServicePort -> OrderService (cycle!)")
    print()

    container = Container()

    try:
        # This will fail because of the circular dependency
        container.scan(profile=Profile.PRODUCTION)

        # If we get here (shouldn't), try to resolve
        container.resolve(OrderServicePort)

    except Exception as e:
        print("-" * 70)
        print("dioxide detected the circular dependency!")
        print("-" * 70)
        print()
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {e}")
        print()
        print("-" * 70)
        print("What to do:")
        print("-" * 70)
        print()
        print("1. Extract shared data access to a repository")
        print("   OrderService -> OrderRepository <- NotificationService")
        print()
        print("2. Use event-based communication")
        print("   OrderService -> EventBus <- NotificationService")
        print()
        print("3. Pass data instead of service references")
        print("   Controller orchestrates both services")
        print()
        print("See solution.py for the fixed version!")


if __name__ == "__main__":
    main()
