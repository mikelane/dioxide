"""Tests using injector's module-based testing pattern.

With injector, testing requires:
1. Creating an Injector with the TestModule
2. Getting the service from the injector
3. Getting fakes to inspect state
"""

import pytest
from injector import Injector

from app.modules import TestModule
from app.ports import NotificationService, OrderRepository, PaymentGateway
from app.services import OrderService


@pytest.fixture
def injector() -> Injector:
    """Create injector with test module."""
    return Injector([TestModule()])


class DescribeOrderService:
    """Tests for OrderService."""

    class DescribeCreateOrder:
        """Tests for create_order method."""

        async def it_creates_order_and_sends_notification(
            self, injector: Injector
        ) -> None:
            service = injector.get(OrderService)
            fake_notifications = injector.get(NotificationService)

            order = await service.create_order(
                customer_id="cust_123",
                items=["Widget"],
                total=49.99,
            )

            assert order.customer_id == "cust_123"
            assert order.items == ["Widget"]
            assert order.total == 49.99
            assert order.status == "confirmed"

            assert len(fake_notifications.notifications) == 1
            assert "cust_123" in fake_notifications.notifications[0]["recipient"]

        async def it_processes_payment(self, injector: Injector) -> None:
            service = injector.get(OrderService)
            fake_payments = injector.get(PaymentGateway)

            await service.create_order(
                customer_id="cust_456",
                items=["Gadget"],
                total=29.99,
            )

            assert len(fake_payments.charges) == 1
            assert fake_payments.charges[0]["amount"] == 29.99
            assert fake_payments.charges[0]["customer_id"] == "cust_456"

    class DescribeGetOrder:
        """Tests for get_order method."""

        async def it_returns_saved_order(self, injector: Injector) -> None:
            service = injector.get(OrderService)

            created = await service.create_order(
                customer_id="cust_789",
                items=["Thing"],
                total=19.99,
            )
            fetched = await service.get_order(created.id)

            assert fetched is not None
            assert fetched.id == created.id

        async def it_returns_none_for_nonexistent_order(
            self, injector: Injector
        ) -> None:
            service = injector.get(OrderService)

            result = await service.get_order("nonexistent")

            assert result is None

    class DescribeCancelOrder:
        """Tests for cancel_order method."""

        async def it_cancels_order_and_refunds(self, injector: Injector) -> None:
            service = injector.get(OrderService)
            fake_payments = injector.get(PaymentGateway)
            fake_notifications = injector.get(NotificationService)

            order = await service.create_order(
                customer_id="cust_cancel",
                items=["Item"],
                total=59.99,
            )

            cancelled = await service.cancel_order(order.id)

            assert cancelled is not None
            assert cancelled.status == "cancelled"
            assert len(fake_payments.refunds) == 1
            assert fake_payments.refunds[0]["amount"] == 59.99

            cancel_notification = fake_notifications.notifications[-1]
            assert "cancelled" in cancel_notification["message"]

        async def it_returns_none_for_nonexistent_order(
            self, injector: Injector
        ) -> None:
            service = injector.get(OrderService)

            result = await service.cancel_order("nonexistent")

            assert result is None
