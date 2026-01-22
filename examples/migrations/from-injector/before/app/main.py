"""Application entry point using injector."""

import asyncio

from injector import Injector

from app.modules import ProductionModule
from app.services import OrderService


async def main() -> None:
    """Run the application."""
    injector = Injector([ProductionModule()])

    service = injector.get(OrderService)

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
