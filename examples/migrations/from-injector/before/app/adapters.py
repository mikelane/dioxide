"""Adapter implementations for injector example."""

from datetime import datetime, UTC

from app.ports import NotificationService, Order, OrderRepository, PaymentGateway


class PostgresOrderRepository(OrderRepository):
    """PostgreSQL implementation of OrderRepository."""

    def __init__(self) -> None:
        self._orders: dict[str, Order] = {}

    async def get(self, order_id: str) -> Order | None:
        return self._orders.get(order_id)

    async def save(self, order: Order) -> Order:
        self._orders[order.id] = order
        return order

    async def find_by_customer(self, customer_id: str) -> list[Order]:
        return [o for o in self._orders.values() if o.customer_id == customer_id]


class EmailNotificationService(NotificationService):
    """Email-based notification service."""

    async def send(self, recipient: str, message: str) -> bool:
        print(f"[Email] Sending to {recipient}: {message}")
        return True


class StripePaymentGateway(PaymentGateway):
    """Stripe implementation of PaymentGateway."""

    async def charge(self, customer_id: str, amount: float) -> dict:
        print(f"[Stripe] Charging {customer_id} ${amount:.2f}")
        return {
            "transaction_id": f"txn_{customer_id}_{int(amount * 100)}",
            "status": "succeeded",
            "amount": amount,
        }

    async def refund(self, transaction_id: str, amount: float) -> dict:
        print(f"[Stripe] Refunding {transaction_id} ${amount:.2f}")
        return {
            "refund_id": f"ref_{transaction_id}",
            "status": "succeeded",
            "amount": amount,
        }


class FakeOrderRepository(OrderRepository):
    """In-memory fake for testing."""

    def __init__(self) -> None:
        self._orders: dict[str, Order] = {}
        self._next_id = 1

    async def get(self, order_id: str) -> Order | None:
        return self._orders.get(order_id)

    async def save(self, order: Order) -> Order:
        if not order.id:
            order = Order(
                id=str(self._next_id),
                customer_id=order.customer_id,
                items=order.items,
                total=order.total,
                status=order.status,
                created_at=order.created_at,
            )
            self._next_id += 1
        self._orders[order.id] = order
        return order

    async def find_by_customer(self, customer_id: str) -> list[Order]:
        return [o for o in self._orders.values() if o.customer_id == customer_id]

    def seed(self, *orders: Order) -> None:
        """Seed with test data."""
        for order in orders:
            self._orders[order.id] = order


class FakeNotificationService(NotificationService):
    """In-memory fake for testing."""

    def __init__(self) -> None:
        self.notifications: list[dict] = []

    async def send(self, recipient: str, message: str) -> bool:
        self.notifications.append({"recipient": recipient, "message": message})
        return True


class FakePaymentGateway(PaymentGateway):
    """In-memory fake for testing."""

    def __init__(self) -> None:
        self.charges: list[dict] = []
        self.refunds: list[dict] = []
        self.should_fail = False

    async def charge(self, customer_id: str, amount: float) -> dict:
        if self.should_fail:
            raise RuntimeError("Payment failed")

        charge = {
            "transaction_id": f"fake_txn_{len(self.charges) + 1}",
            "status": "succeeded",
            "amount": amount,
            "customer_id": customer_id,
        }
        self.charges.append(charge)
        return charge

    async def refund(self, transaction_id: str, amount: float) -> dict:
        refund = {
            "refund_id": f"fake_ref_{len(self.refunds) + 1}",
            "status": "succeeded",
            "amount": amount,
            "transaction_id": transaction_id,
        }
        self.refunds.append(refund)
        return refund

    def fail_next_charge(self) -> None:
        """Configure next charge to fail."""
        self.should_fail = True
