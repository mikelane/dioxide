"""Domain services (use cases) for order management.

Services contain pure business logic and depend only on ports (interfaces),
not concrete implementations. This makes them testable and portable.
"""

import uuid
from typing import Any

from dioxide import service

from .models import Order, OrderItem
from .ports import CachePort, EventPublisherPort, OrderRepositoryPort, ProductRepositoryPort


@service
class OrderService:
    """Core business logic for order management.

    This service demonstrates a complex dependency chain:
    - OrderRepositoryPort for order persistence
    - ProductRepositoryPort for product catalog
    - CachePort for caching frequent queries
    - EventPublisherPort for domain events

    All dependencies are injected automatically by dioxide based on type hints.
    """

    def __init__(
        self,
        orders: OrderRepositoryPort,
        products: ProductRepositoryPort,
        cache: CachePort,
        events: EventPublisherPort,
    ) -> None:
        """Initialize with port dependencies.

        Args:
            orders: Repository for order persistence
            products: Repository for product catalog
            cache: Cache for frequently accessed data
            events: Publisher for domain events
        """
        self.orders = orders
        self.products = products
        self.cache = cache
        self.events = events

    async def create_order(
        self,
        customer_id: str,
        items: list[dict[str, Any]],
    ) -> Order:
        """Create a new order.

        Business logic:
        1. Validate all products exist and have sufficient stock
        2. Create the order with calculated prices
        3. Decrease stock for each product
        4. Cache the order for quick retrieval
        5. Publish OrderCreated event

        Args:
            customer_id: Customer placing the order
            items: List of items with product_id and quantity

        Returns:
            Created order

        Raises:
            ValueError: If product not found or insufficient stock
        """
        order_items: list[OrderItem] = []

        for item in items:
            product = await self.products.get_by_id(item["product_id"])
            if product is None:
                raise ValueError(f"Product {item['product_id']} not found")

            if product.stock < item["quantity"]:
                raise ValueError(f"Insufficient stock for {product.name}")

            order_items.append(
                OrderItem(
                    product_id=product.id,
                    product_name=product.name,
                    quantity=item["quantity"],
                    unit_price=product.price,
                )
            )

        order = Order(
            id=str(uuid.uuid4()),
            customer_id=customer_id,
            items=order_items,
        )

        await self.orders.save(order)

        for item in items:
            await self.products.update_stock(item["product_id"], -item["quantity"])

        await self.cache.set(f"order:{order.id}", order.to_dict())

        await self.events.publish(
            "OrderCreated",
            {
                "order_id": order.id,
                "customer_id": customer_id,
                "total": order.total,
            },
        )

        return order

    async def get_order(self, order_id: str) -> Order | None:
        """Get an order by ID with caching.

        First checks cache, then falls back to repository.

        Args:
            order_id: Order ID to retrieve

        Returns:
            Order if found, None otherwise
        """
        cached = await self.cache.get(f"order:{order_id}")
        if cached is not None:
            return cached

        order = await self.orders.get_by_id(order_id)
        if order is not None:
            await self.cache.set(f"order:{order_id}", order.to_dict())

        return order

    async def get_customer_orders(self, customer_id: str) -> list[Order]:
        """Get all orders for a customer.

        Args:
            customer_id: Customer ID

        Returns:
            List of orders
        """
        return await self.orders.list_by_customer(customer_id)


@service
class OrderController:
    """HTTP controller layer for order operations.

    This demonstrates another level in the dependency chain:
    OrderController -> OrderService -> Multiple Adapters

    In a real application, this would be a FastAPI router or similar.
    """

    def __init__(self, order_service: OrderService) -> None:
        """Initialize with service dependency.

        Args:
            order_service: Business logic service
        """
        self.order_service = order_service

    async def create_order(
        self,
        customer_id: str,
        items: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Handle create order request.

        Args:
            customer_id: Customer placing the order
            items: List of items with product_id and quantity

        Returns:
            Order data as dictionary
        """
        order = await self.order_service.create_order(customer_id, items)
        return order.to_dict()

    async def get_order(self, order_id: str) -> dict[str, Any] | None:
        """Handle get order request.

        Args:
            order_id: Order ID to retrieve

        Returns:
            Order data as dictionary or None
        """
        order = await self.order_service.get_order(order_id)
        if order is None:
            return None
        if isinstance(order, dict):
            return order
        return order.to_dict()

    async def get_customer_orders(self, customer_id: str) -> list[dict[str, Any]]:
        """Handle list customer orders request.

        Args:
            customer_id: Customer ID

        Returns:
            List of order dictionaries
        """
        orders = await self.order_service.get_customer_orders(customer_id)
        return [o.to_dict() for o in orders]
