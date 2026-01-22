"""Fake adapters for testing.

Fakes are real implementations that use in-memory storage instead of
external infrastructure. They are fast, deterministic, and allow
tests to verify behavior without mocking.
"""

from typing import Any

from dioxide import Profile, adapter

from ..domain.models import Order, Product
from ..domain.ports import CachePort, EventPublisherPort, OrderRepositoryPort, ProductRepositoryPort


@adapter.for_(OrderRepositoryPort, profile=Profile.TEST)
class FakeOrderRepository:
    """Test order repository using in-memory storage.

    Features:
    - Fast (no I/O)
    - Deterministic (same behavior every time)
    - Inspectable (tests can check internal state)
    """

    def __init__(self) -> None:
        """Initialize with empty storage."""
        self.orders: dict[str, Order] = {}

    async def save(self, order: Order) -> None:
        """Save an order to in-memory storage."""
        self.orders[order.id] = order

    async def get_by_id(self, order_id: str) -> Order | None:
        """Retrieve an order by ID from in-memory storage."""
        return self.orders.get(order_id)

    async def list_by_customer(self, customer_id: str) -> list[Order]:
        """List all orders for a customer from in-memory storage."""
        return [o for o in self.orders.values() if o.customer_id == customer_id]

    def clear(self) -> None:
        """Clear all orders (test helper)."""
        self.orders.clear()


@adapter.for_(ProductRepositoryPort, profile=Profile.TEST)
class FakeProductRepository:
    """Test product repository using in-memory storage.

    Includes seed() method for setting up test data.
    """

    def __init__(self) -> None:
        """Initialize with empty storage."""
        self.products: dict[str, Product] = {}

    async def get_by_id(self, product_id: str) -> Product | None:
        """Retrieve a product by ID from in-memory storage."""
        return self.products.get(product_id)

    async def update_stock(self, product_id: str, quantity_delta: int) -> None:
        """Update product stock in in-memory storage."""
        product = self.products.get(product_id)
        if product:
            product.stock += quantity_delta

    def seed(self, *products: Product) -> None:
        """Seed with test products.

        Args:
            *products: Products to add to the repository
        """
        for product in products:
            self.products[product.id] = product

    def clear(self) -> None:
        """Clear all products (test helper)."""
        self.products.clear()


@adapter.for_(CachePort, profile=Profile.TEST)
class FakeCache:
    """Test cache using in-memory dictionary.

    Allows tests to inspect cache state and verify caching behavior.
    """

    def __init__(self) -> None:
        """Initialize with empty cache."""
        self.cache: dict[str, Any] = {}
        self.get_calls: list[str] = []
        self.set_calls: list[tuple[str, Any, int]] = []

    async def get(self, key: str) -> Any | None:
        """Get a value from in-memory cache."""
        self.get_calls.append(key)
        return self.cache.get(key)

    async def set(self, key: str, value: Any, ttl_seconds: int = 300) -> None:
        """Set a value in in-memory cache."""
        self.cache[key] = value
        self.set_calls.append((key, value, ttl_seconds))

    async def delete(self, key: str) -> None:
        """Delete a value from in-memory cache."""
        if key in self.cache:
            del self.cache[key]

    def clear(self) -> None:
        """Clear cache and call history (test helper)."""
        self.cache.clear()
        self.get_calls.clear()
        self.set_calls.clear()

    def was_cached(self, key: str) -> bool:
        """Check if a key was cached (test helper)."""
        return any(call[0] == key for call in self.set_calls)


@adapter.for_(EventPublisherPort, profile=Profile.TEST)
class FakeEventPublisher:
    """Test event publisher that records published events.

    Allows tests to verify which events were published and with what data.
    """

    def __init__(self) -> None:
        """Initialize with empty event list."""
        self.published: list[dict[str, Any]] = []

    async def publish(self, event_type: str, payload: dict[str, Any]) -> None:
        """Record event instead of publishing."""
        self.published.append({"type": event_type, "payload": payload})

    def clear(self) -> None:
        """Clear all published events (test helper)."""
        self.published.clear()

    def get_events_of_type(self, event_type: str) -> list[dict[str, Any]]:
        """Get all events of a specific type (test helper)."""
        return [e for e in self.published if e["type"] == event_type]

    def was_published(self, event_type: str) -> bool:
        """Check if an event type was published (test helper)."""
        return any(e["type"] == event_type for e in self.published)
