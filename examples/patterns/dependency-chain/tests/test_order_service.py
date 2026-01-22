"""Tests for the order service demonstrating dependency chain testing.

These tests show how to test a service with multiple dependencies using fakes.
No mocking frameworks needed - just real implementations with in-memory storage.
"""

import pytest
from dioxide import Container

from app.domain import OrderController, OrderService
from app.domain.models import Product
from app.domain.ports import CachePort, EventPublisherPort, OrderRepositoryPort, ProductRepositoryPort


class DescribeOrderService:
    """Tests for OrderService business logic."""

    async def it_creates_an_order_with_multiple_items(
        self,
        container: Container,
        seeded_products: ProductRepositoryPort,
        orders: OrderRepositoryPort,
        events: EventPublisherPort,
    ) -> None:
        """OrderService creates order and publishes event."""
        service = container.resolve(OrderService)

        order = await service.create_order(
            customer_id="c1",
            items=[
                {"product_id": "p1", "quantity": 2},
                {"product_id": "p2", "quantity": 1},
            ],
        )

        assert order.customer_id == "c1"
        assert len(order.items) == 2
        assert order.total == 45.00

        assert order.id in orders.orders
        assert events.was_published("OrderCreated")

    async def it_validates_product_exists(
        self,
        container: Container,
        seeded_products: ProductRepositoryPort,
    ) -> None:
        """OrderService raises ValueError for invalid product."""
        service = container.resolve(OrderService)

        with pytest.raises(ValueError, match="not found"):
            await service.create_order(
                customer_id="c1",
                items=[{"product_id": "invalid", "quantity": 1}],
            )

    async def it_validates_sufficient_stock(
        self,
        container: Container,
        seeded_products: ProductRepositoryPort,
    ) -> None:
        """OrderService raises ValueError for insufficient stock."""
        service = container.resolve(OrderService)

        with pytest.raises(ValueError, match="Insufficient stock"):
            await service.create_order(
                customer_id="c1",
                items=[{"product_id": "p1", "quantity": 1000}],
            )

    async def it_decreases_stock_after_order(
        self,
        container: Container,
        seeded_products: ProductRepositoryPort,
    ) -> None:
        """OrderService decreases product stock after order."""
        service = container.resolve(OrderService)
        product_before = await seeded_products.get_by_id("p1")
        initial_stock = product_before.stock

        await service.create_order(
            customer_id="c1",
            items=[{"product_id": "p1", "quantity": 5}],
        )

        product_after = await seeded_products.get_by_id("p1")
        assert product_after.stock == initial_stock - 5

    async def it_caches_order_after_creation(
        self,
        container: Container,
        seeded_products: ProductRepositoryPort,
        cache: CachePort,
    ) -> None:
        """OrderService caches order after creation."""
        service = container.resolve(OrderService)

        order = await service.create_order(
            customer_id="c1",
            items=[{"product_id": "p1", "quantity": 1}],
        )

        assert cache.was_cached(f"order:{order.id}")

    async def it_retrieves_order_from_cache_on_second_call(
        self,
        container: Container,
        seeded_products: ProductRepositoryPort,
        cache: CachePort,
    ) -> None:
        """OrderService uses cache for order retrieval."""
        service = container.resolve(OrderService)

        order = await service.create_order(
            customer_id="c1",
            items=[{"product_id": "p1", "quantity": 1}],
        )

        cache.get_calls.clear()

        await service.get_order(order.id)

        assert f"order:{order.id}" in cache.get_calls


class DescribeOrderController:
    """Tests for OrderController API layer."""

    async def it_creates_order_through_full_chain(
        self,
        container: Container,
        seeded_products: ProductRepositoryPort,
        orders: OrderRepositoryPort,
        events: EventPublisherPort,
    ) -> None:
        """OrderController creates order through service and adapters."""
        controller = container.resolve(OrderController)

        result = await controller.create_order(
            customer_id="c1",
            items=[{"product_id": "p1", "quantity": 3}],
        )

        assert result["customer_id"] == "c1"
        assert len(result["items"]) == 1
        assert result["total"] == 30.00

        assert len(orders.orders) == 1

        order_events = events.get_events_of_type("OrderCreated")
        assert len(order_events) == 1
        assert order_events[0]["payload"]["customer_id"] == "c1"

    async def it_retrieves_order(
        self,
        container: Container,
        seeded_products: ProductRepositoryPort,
    ) -> None:
        """OrderController retrieves order by ID."""
        controller = container.resolve(OrderController)

        created = await controller.create_order(
            customer_id="c1",
            items=[{"product_id": "p1", "quantity": 1}],
        )

        result = await controller.get_order(created["id"])

        assert result is not None
        assert result["id"] == created["id"]

    async def it_returns_none_for_nonexistent_order(
        self,
        container: Container,
    ) -> None:
        """OrderController returns None for unknown order ID."""
        controller = container.resolve(OrderController)

        result = await controller.get_order("nonexistent")

        assert result is None

    async def it_lists_customer_orders(
        self,
        container: Container,
        seeded_products: ProductRepositoryPort,
    ) -> None:
        """OrderController lists all orders for a customer."""
        controller = container.resolve(OrderController)

        await controller.create_order(
            customer_id="c1",
            items=[{"product_id": "p1", "quantity": 1}],
        )
        await controller.create_order(
            customer_id="c1",
            items=[{"product_id": "p2", "quantity": 1}],
        )
        await controller.create_order(
            customer_id="c2",
            items=[{"product_id": "p1", "quantity": 1}],
        )

        c1_orders = await controller.get_customer_orders("c1")
        c2_orders = await controller.get_customer_orders("c2")

        assert len(c1_orders) == 2
        assert len(c2_orders) == 1


class DescribeDependencyResolution:
    """Tests demonstrating dependency chain resolution."""

    def it_resolves_service_with_all_dependencies(
        self,
        container: Container,
    ) -> None:
        """Container resolves OrderService with all port implementations."""
        service = container.resolve(OrderService)

        assert service.orders is not None
        assert service.products is not None
        assert service.cache is not None
        assert service.events is not None

    def it_resolves_controller_with_service_dependency(
        self,
        container: Container,
    ) -> None:
        """Container resolves OrderController with OrderService."""
        controller = container.resolve(OrderController)

        assert controller.order_service is not None
        assert controller.order_service.orders is not None

    def it_uses_test_fakes_in_test_profile(
        self,
        container: Container,
    ) -> None:
        """Container uses fake adapters in TEST profile."""
        orders = container.resolve(OrderRepositoryPort)
        products = container.resolve(ProductRepositoryPort)
        cache = container.resolve(CachePort)
        events = container.resolve(EventPublisherPort)

        assert hasattr(orders, "orders")
        assert hasattr(products, "seed")
        assert hasattr(cache, "get_calls")
        assert hasattr(events, "published")


class DescribeTestIsolation:
    """Tests demonstrating test isolation with fakes."""

    async def it_provides_clean_state_per_test(
        self,
        container: Container,
        seeded_products: ProductRepositoryPort,
        orders: OrderRepositoryPort,
    ) -> None:
        """Each test starts with clean adapter state."""
        assert len(orders.orders) == 0

        controller = container.resolve(OrderController)
        await controller.create_order(
            customer_id="c1",
            items=[{"product_id": "p1", "quantity": 1}],
        )

        assert len(orders.orders) == 1

    async def it_also_provides_clean_state(
        self,
        container: Container,
        seeded_products: ProductRepositoryPort,
        orders: OrderRepositoryPort,
    ) -> None:
        """Fresh container fixture ensures isolation between tests."""
        assert len(orders.orders) == 0
