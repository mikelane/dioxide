"""Stripe adapter for production payment processing."""

import uuid
from decimal import Decimal

from dioxide import Profile, adapter

from ..domain.models import PaymentResult, PaymentStatus, RefundResult, RefundStatus
from ..domain.ports import PaymentGatewayPort


@adapter.for_(PaymentGatewayPort, profile=Profile.PRODUCTION)
class StripeAdapter:
    """Production payment gateway using Stripe API.

    In a real implementation, this would use the stripe-python SDK.
    This example simulates the behavior for demonstration.
    """

    def __init__(self) -> None:
        """Initialize Stripe adapter."""
        print("  [Stripe] Adapter initialized")

    async def charge(
        self,
        amount: Decimal,
        currency: str,
        card_token: str,
        idempotency_key: str | None = None,
    ) -> PaymentResult:
        """Process a charge via Stripe API.

        In a real implementation:
        ```python
        charge = await stripe.Charge.create(
            amount=int(amount * 100),  # Stripe uses cents
            currency=currency.lower(),
            source=card_token,
            idempotency_key=idempotency_key,
        )
        ```
        """
        print(f"  [Stripe] Processing charge: ${amount} {currency}")
        print(f"           Card token: {card_token[:10]}...")
        print(f"           Idempotency key: {idempotency_key}")

        payment_id = f"ch_{uuid.uuid4().hex[:24]}"
        print(f"  [Stripe] Charge successful: {payment_id}")

        return PaymentResult(
            id=payment_id,
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
        """Process a refund via Stripe API.

        In a real implementation:
        ```python
        refund = await stripe.Refund.create(
            charge=payment_id,
            amount=int(amount * 100) if amount else None,
            reason=reason,
        )
        ```
        """
        print(f"  [Stripe] Processing refund for: {payment_id}")
        print(f"           Amount: {'full' if amount is None else f'${amount}'}")

        refund_id = f"re_{uuid.uuid4().hex[:24]}"
        print(f"  [Stripe] Refund successful: {refund_id}")

        return RefundResult(
            id=refund_id,
            payment_id=payment_id,
            status=RefundStatus.SUCCEEDED,
            amount=amount or Decimal("0"),
        )
