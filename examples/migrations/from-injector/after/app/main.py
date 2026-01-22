"""Application entry point using dioxide.

Notice there's no modules.py file - dioxide uses decorators and scanning
instead of Module classes with Binder configuration.
"""

import asyncio

from dioxide import Container, Profile

from app.services import OrderService


async def main() -> None:
    """Run the application."""
    container = Container()
    container.scan("app", profile=Profile.PRODUCTION)

    service = container.resolve(OrderService)

    print("Creating order...")
    order = await service.create_order(
        customer_id="cust_123",
        items=["Widget", "Gadget"],
        total=99.99,
    )
    print(f"Created order: {order}")

    print("\nFetching order...")
    fetched = await service.get_order(order.id)
    print(f"Fetched order: {fetched}")

    print("\nGetting customer orders...")
    orders = await service.get_customer_orders("cust_123")
    print(f"Customer has {len(orders)} order(s)")

    print("\nCancelling order...")
    cancelled = await service.cancel_order(order.id)
    print(f"Cancelled order: {cancelled}")


if __name__ == "__main__":
    asyncio.run(main())
