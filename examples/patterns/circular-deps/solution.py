"""Solution: Breaking circular dependencies with event-based communication.

This file shows how to refactor the circular dependency from problem.py
using an event-based approach.

Before (circular):
    OrderService <-> NotificationService

After (decoupled):
    OrderService -> EventBus <- NotificationService

Run this file to see it working:
    python solution.py
"""

import asyncio
from dataclasses import dataclass, field
from typing import Any, Callable, Protocol

from dioxide import Container, Profile, adapter, service


# =============================================================================
# Domain Events
# =============================================================================


@dataclass
class DomainEvent:
    """Base class for domain events."""

    pass


@dataclass
class OrderCreated(DomainEvent):
    """Event published when an order is created."""

    order_id: str
    customer_id: str
    items: list[dict[str, Any]]
    total: float


@dataclass
class OrderStatusChanged(DomainEvent):
    """Event published when order status changes."""

    order_id: str
    old_status: str
    new_status: str


# =============================================================================
# Ports (Interfaces)
# =============================================================================


class OrderRepositoryPort(Protocol):
    """Port for order data access."""

    async def save(self, order: dict[str, Any]) -> None:
        ...

    async def get_by_id(self, order_id: str) -> dict[str, Any] | None:
        ...


class EventBusPort(Protocol):
    """Port for event publishing and subscription."""

    async def publish(self, event: DomainEvent) -> None:
        ...

    def subscribe(self, event_type: type[DomainEvent], handler: Callable) -> None:
        ...


class EmailPort(Protocol):
    """Port for sending emails."""

    async def send(self, to: str, subject: str, body: str) -> None:
        ...


# =============================================================================
# Services (No circular dependency!)
# =============================================================================


@service
class OrderService:
    """Order service that publishes events instead of calling NotificationService.

    Dependencies:
    - OrderRepositoryPort: For data persistence
    - EventBusPort: For publishing domain events

    Note: No dependency on NotificationService!
    """

    def __init__(
        self,
        repository: OrderRepositoryPort,
        events: EventBusPort,
    ) -> None:
        self.repository = repository
        self.events = events
        self._next_id = 1

    async def create_order(
        self,
        customer_id: str,
        items: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Create order and publish OrderCreated event."""
        total = sum(item.get("price", 0) * item.get("quantity", 1) for item in items)

        order = {
            "id": f"order-{self._next_id}",
            "customer_id": customer_id,
            "items": items,
            "total": total,
            "status": "created",
        }
        self._next_id += 1

        await self.repository.save(order)

        # Publish event instead of calling NotificationService directly
        await self.events.publish(
            OrderCreated(
                order_id=order["id"],
                customer_id=customer_id,
                items=items,
                total=total,
            )
        )

        return order

    async def update_status(self, order_id: str, new_status: str) -> dict[str, Any] | None:
        """Update order status and publish event."""
        order = await self.repository.get_by_id(order_id)
        if order is None:
            return None

        old_status = order["status"]
        order["status"] = new_status
        await self.repository.save(order)

        await self.events.publish(
            OrderStatusChanged(
                order_id=order_id,
                old_status=old_status,
                new_status=new_status,
            )
        )

        return order


@service
class NotificationService:
    """Notification service that subscribes to events.

    Dependencies:
    - EventBusPort: For receiving domain events
    - OrderRepositoryPort: For looking up order details
    - EmailPort: For sending emails

    Note: No dependency on OrderService!
    """

    def __init__(
        self,
        events: EventBusPort,
        repository: OrderRepositoryPort,
        email: EmailPort,
    ) -> None:
        self.repository = repository
        self.email = email

        # Subscribe to events
        events.subscribe(OrderCreated, self._handle_order_created)
        events.subscribe(OrderStatusChanged, self._handle_status_changed)

    async def _handle_order_created(self, event: OrderCreated) -> None:
        """Handle OrderCreated event."""
        await self.email.send(
            to=f"{event.customer_id}@example.com",
            subject=f"Order {event.order_id} Confirmed",
            body=f"Your order of ${event.total:.2f} has been received!",
        )

    async def _handle_status_changed(self, event: OrderStatusChanged) -> None:
        """Handle OrderStatusChanged event."""
        order = await self.repository.get_by_id(event.order_id)
        if order:
            await self.email.send(
                to=f"{order['customer_id']}@example.com",
                subject=f"Order {event.order_id} Status Update",
                body=f"Your order status changed from {event.old_status} to {event.new_status}",
            )


# =============================================================================
# Adapters
# =============================================================================


@adapter.for_(OrderRepositoryPort, profile=Profile.PRODUCTION)
class InMemoryOrderRepository:
    """In-memory order repository for demonstration."""

    def __init__(self) -> None:
        self.orders: dict[str, dict[str, Any]] = {}

    async def save(self, order: dict[str, Any]) -> None:
        self.orders[order["id"]] = order
        print(f"  [Repository] Saved order {order['id']}")

    async def get_by_id(self, order_id: str) -> dict[str, Any] | None:
        return self.orders.get(order_id)


@adapter.for_(EventBusPort, profile=Profile.PRODUCTION)
class SimpleEventBus:
    """Simple in-memory event bus."""

    def __init__(self) -> None:
        self._handlers: dict[type, list[Callable]] = {}

    async def publish(self, event: DomainEvent) -> None:
        print(f"  [EventBus] Publishing {type(event).__name__}")
        handlers = self._handlers.get(type(event), [])
        for handler in handlers:
            await handler(event)

    def subscribe(self, event_type: type[DomainEvent], handler: Callable) -> None:
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
        print(f"  [EventBus] Subscribed {handler.__qualname__} to {event_type.__name__}")


@adapter.for_(EmailPort, profile=Profile.PRODUCTION)
class ConsoleEmail:
    """Email adapter that prints to console."""

    async def send(self, to: str, subject: str, body: str) -> None:
        print(f"  [Email] To: {to}")
        print(f"          Subject: {subject}")
        print(f"          Body: {body}")


# =============================================================================
# Demonstration
# =============================================================================


async def main() -> None:
    """Demonstrate the working solution."""
    print("=" * 70)
    print("Circular Dependency Solution: Event-Based Communication")
    print("=" * 70)
    print()
    print("New architecture:")
    print("  OrderService -> EventBusPort <- NotificationService")
    print("                  (publish)        (subscribe)")
    print()
    print("-" * 70)
    print("Setting up container...")
    print("-" * 70)
    print()

    container = Container(profile=Profile.PRODUCTION)

    print()
    print("-" * 70)
    print("Resolving services...")
    print("-" * 70)
    print()

    # Both services can be resolved without circular dependency!
    order_service = container.resolve(OrderService)
    _notification_service = container.resolve(NotificationService)

    print()
    print("-" * 70)
    print("Creating an order...")
    print("-" * 70)
    print()

    order = await order_service.create_order(
        customer_id="alice",
        items=[
            {"name": "Widget", "price": 29.99, "quantity": 2},
            {"name": "Gadget", "price": 49.99, "quantity": 1},
        ],
    )

    print()
    print("-" * 70)
    print("Updating order status...")
    print("-" * 70)
    print()

    await order_service.update_status(order["id"], "shipped")

    print()
    print("=" * 70)
    print("Success! No circular dependency.")
    print()
    print("Key changes:")
    print("1. OrderService publishes events instead of calling NotificationService")
    print("2. NotificationService subscribes to events instead of depending on OrderService")
    print("3. Both services can access order data through OrderRepositoryPort")
    print("4. EventBusPort decouples the communication")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
