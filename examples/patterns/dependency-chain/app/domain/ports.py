"""Port definitions (interfaces) for the order management system.

Ports define the contracts between the domain layer and infrastructure.
They are implemented by adapters for different environments.
"""

from typing import Any, Protocol

from .models import Order, Product


class OrderRepositoryPort(Protocol):
    """Port for order persistence operations."""

    async def save(self, order: Order) -> None:
        """Save an order to the repository."""
        ...

    async def get_by_id(self, order_id: str) -> Order | None:
        """Retrieve an order by ID."""
        ...

    async def list_by_customer(self, customer_id: str) -> list[Order]:
        """List all orders for a customer."""
        ...


class ProductRepositoryPort(Protocol):
    """Port for product catalog operations."""

    async def get_by_id(self, product_id: str) -> Product | None:
        """Retrieve a product by ID."""
        ...

    async def update_stock(self, product_id: str, quantity_delta: int) -> None:
        """Update product stock (negative for decrease)."""
        ...


class CachePort(Protocol):
    """Port for caching operations."""

    async def get(self, key: str) -> Any | None:
        """Get a value from cache."""
        ...

    async def set(self, key: str, value: Any, ttl_seconds: int = 300) -> None:
        """Set a value in cache with TTL."""
        ...

    async def delete(self, key: str) -> None:
        """Delete a value from cache."""
        ...


class EventPublisherPort(Protocol):
    """Port for publishing domain events."""

    async def publish(self, event_type: str, payload: dict[str, Any]) -> None:
        """Publish an event to the event bus."""
        ...
