"""Business logic services using dioxide @service decorator.

The @service decorator replaces injector's @inject decorator.
No module configuration needed - dependencies resolved from type hints.
"""

from datetime import datetime, UTC
from uuid import uuid4

from dioxide import service

from app.ports import NotificationPort, Order, OrderRepositoryPort, PaymentGatewayPort


@service
class OrderService:
    """Order management service.

    With dioxide, the @service decorator marks this as injectable.
    Dependencies are inferred from the constructor's type hints.

    No @inject decorator needed - just use type hints.
    """

    def __init__(
        self,
        repository: OrderRepositoryPort,
        notifications: NotificationPort,
        payments: PaymentGatewayPort,
    ) -> None:
        self._repository = repository
        self._notifications = notifications
        self._payments = payments

    async def create_order(
        self,
        customer_id: str,
        items: list[str],
        total: float,
    ) -> Order:
        """Create a new order and process payment."""
        payment_result = await self._payments.charge(customer_id, total)

        order = Order(
            id=str(uuid4()),
            customer_id=customer_id,
            items=items,
            total=total,
            status="confirmed",
            created_at=datetime.now(UTC),
        )
        order = await self._repository.save(order)

        await self._notifications.send(
            recipient=customer_id,
            message=f"Order {order.id} confirmed for ${total:.2f}",
        )

        return order

    async def get_order(self, order_id: str) -> Order | None:
        """Get an order by ID."""
        return await self._repository.get(order_id)

    async def get_customer_orders(self, customer_id: str) -> list[Order]:
        """Get all orders for a customer."""
        return await self._repository.find_by_customer(customer_id)

    async def cancel_order(self, order_id: str) -> Order | None:
        """Cancel an order and process refund."""
        order = await self._repository.get(order_id)
        if not order:
            return None

        if order.status == "cancelled":
            return order

        await self._payments.refund(f"txn_{order.id}", order.total)

        cancelled_order = Order(
            id=order.id,
            customer_id=order.customer_id,
            items=order.items,
            total=order.total,
            status="cancelled",
            created_at=order.created_at,
        )
        await self._repository.save(cancelled_order)

        await self._notifications.send(
            recipient=order.customer_id,
            message=f"Order {order.id} has been cancelled. Refund of ${order.total:.2f} initiated.",
        )

        return cancelled_order
