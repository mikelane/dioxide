"""Fake adapters with error injection for testing.

These fakes allow tests to control the behavior of external services,
including simulating various failure modes.
"""

import uuid
from decimal import Decimal

from dioxide import Profile, adapter

from ..domain.errors import PaymentError
from ..domain.models import (
    Order,
    PaymentResult,
    PaymentStatus,
    RefundResult,
    RefundStatus,
)
from ..domain.ports import OrderRepositoryPort, PaymentGatewayPort


@adapter.for_(PaymentGatewayPort, profile=Profile.TEST)
class FakePaymentGateway:
    """Fake payment gateway with error injection capabilities.

    This fake allows tests to:
    - Simulate successful payments
    - Inject specific errors
    - Fail after N calls (for retry testing)
    - Record all calls for verification
    """

    def __init__(self) -> None:
        """Initialize with default successful behavior."""
        self.should_fail: bool = False
        self.fail_with: Exception | None = None
        self.fail_after_n_calls: int | None = None
        self.should_refund_fail: bool = False
        self.refund_fail_with: Exception | None = None

        self.charge_calls: list[dict] = []
        self.refund_calls: list[dict] = []
        self.call_count: int = 0

    async def charge(
        self,
        amount: Decimal,
        currency: str,
        card_token: str,
        idempotency_key: str | None = None,
    ) -> PaymentResult:
        """Process a fake charge.

        Behavior controlled by:
        - should_fail: Always fail with fail_with exception
        - fail_after_n_calls: Fail after N successful calls
        """
        self.call_count += 1
        self.charge_calls.append(
            {
                "amount": amount,
                "currency": currency,
                "card_token": card_token,
                "idempotency_key": idempotency_key,
            }
        )

        if self.should_fail and self.fail_with:
            raise self.fail_with

        if self.fail_after_n_calls is not None:
            if self.call_count <= self.fail_after_n_calls:
                raise self.fail_with or PaymentError("Simulated transient failure")

        return PaymentResult(
            id=f"fake_pay_{uuid.uuid4().hex[:8]}",
            status=PaymentStatus.SUCCEEDED,
            amount=amount,
            currency=currency,
        )

    async def refund(
        self,
        payment_id: str,
        amount: Decimal | None = None,
        reason: str | None = None,
    ) -> RefundResult:
        """Process a fake refund."""
        self.refund_calls.append(
            {
                "payment_id": payment_id,
                "amount": amount,
                "reason": reason,
            }
        )

        if self.should_refund_fail and self.refund_fail_with:
            raise self.refund_fail_with

        return RefundResult(
            id=f"fake_ref_{uuid.uuid4().hex[:8]}",
            payment_id=payment_id,
            status=RefundStatus.SUCCEEDED,
            amount=amount or Decimal("0"),
        )

    def reset(self) -> None:
        """Reset fake to default state."""
        self.should_fail = False
        self.fail_with = None
        self.fail_after_n_calls = None
        self.should_refund_fail = False
        self.refund_fail_with = None
        self.charge_calls.clear()
        self.refund_calls.clear()
        self.call_count = 0

    def configure_to_fail(self, error: Exception) -> None:
        """Configure to always fail with given error."""
        self.should_fail = True
        self.fail_with = error

    def configure_transient_failure(self, fail_count: int, error: Exception) -> None:
        """Configure to fail N times then succeed."""
        self.fail_after_n_calls = fail_count
        self.fail_with = error

    def was_charged(self, amount: Decimal | None = None) -> bool:
        """Check if a charge was made."""
        if amount is None:
            return len(self.charge_calls) > 0
        return any(c["amount"] == amount for c in self.charge_calls)


@adapter.for_(OrderRepositoryPort, profile=Profile.TEST)
class FakeOrderRepository:
    """Fake order repository for testing."""

    def __init__(self) -> None:
        """Initialize with empty storage."""
        self.orders: dict[str, Order] = {}

    async def get_by_id(self, order_id: str) -> Order | None:
        """Get order from in-memory storage."""
        return self.orders.get(order_id)

    async def save(self, order: Order) -> None:
        """Save order to in-memory storage."""
        self.orders[order.id] = order

    def seed(self, *orders: Order) -> None:
        """Seed with test orders."""
        for order in orders:
            self.orders[order.id] = order

    def clear(self) -> None:
        """Clear all orders."""
        self.orders.clear()
