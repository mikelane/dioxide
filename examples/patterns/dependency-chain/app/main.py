"""Entry point demonstrating multi-service dependency chain.

This example shows how dioxide resolves a complex dependency graph:

    OrderController
        -> OrderService
            -> OrderRepositoryPort (-> PostgresOrderRepository)
            -> ProductRepositoryPort (-> PostgresProductRepository)
            -> CachePort (-> RedisCache)
            -> EventPublisherPort (-> KafkaEventPublisher)

All dependencies are resolved automatically based on type hints and profile.
"""

import asyncio

from dioxide import Container, Profile

from . import adapters as _adapters  # noqa: F401 — register adapters for autoscan
from .domain import OrderController


async def main() -> None:
    """Run the dependency chain example."""
    print("=" * 70)
    print("Multi-Service Dependency Chain Example")
    print("=" * 70)
    print()

    print("Creating container and scanning with PRODUCTION profile...")
    print()

    container = Container(profile=Profile.PRODUCTION)

    print()
    print("-" * 70)
    print("Resolving OrderController (triggers full dependency chain)")
    print("-" * 70)
    print()

    controller = container.resolve(OrderController)

    print()
    print("-" * 70)
    print("Creating an order")
    print("-" * 70)
    print()

    result = await controller.create_order(
        customer_id="customer-001",
        items=[
            {"product_id": "prod-001", "quantity": 2},
            {"product_id": "prod-002", "quantity": 1},
        ],
    )

    print()
    print("-" * 70)
    print("Order created successfully!")
    print("-" * 70)
    print()
    print(f"Order ID: {result['id']}")
    print(f"Customer: {result['customer_id']}")
    print(f"Total: ${result['total']:.2f}")
    print(f"Items: {len(result['items'])}")
    for item in result["items"]:
        print(f"  - {item['product_name']}: {item['quantity']} x ${item['unit_price']:.2f} = ${item['total']:.2f}")

    print()
    print("-" * 70)
    print("Retrieving order (should hit cache)")
    print("-" * 70)
    print()

    retrieved = await controller.get_order(result["id"])
    print(f"Retrieved order: {retrieved['id']}")

    print()
    print("=" * 70)
    print("Example complete!")
    print()
    print("Key Takeaways:")
    print("1. Complex dependency graphs resolved automatically")
    print("2. Each service gets its dependencies injected via constructor")
    print("3. Profile determines which adapters are used")
    print("4. Changing profile swaps entire infrastructure layer")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
