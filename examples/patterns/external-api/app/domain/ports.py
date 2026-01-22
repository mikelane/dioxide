"""Port definitions for external API example."""

from decimal import Decimal
from typing import Protocol

from .models import Order, PaymentResult, RefundResult


class PaymentGatewayPort(Protocol):
    """Port for payment gateway operations.

    This port abstracts the payment gateway (e.g., Stripe, PayPal).
    In production, it connects to the real API.
    In tests, it uses a fake with error injection capabilities.
    """

    async def charge(
        self,
        amount: Decimal,
        currency: str,
        card_token: str,
        idempotency_key: str | None = None,
    ) -> PaymentResult:
        """Process a payment charge.

        Args:
            amount: Amount to charge
            currency: ISO currency code (e.g., "USD")
            card_token: Tokenized card data
            idempotency_key: Key to prevent duplicate charges

        Returns:
            PaymentResult with status and payment ID

        Raises:
            CardDeclinedError: Card was declined
            ValidationError: Invalid payment data
            NetworkError: Network failure
            TransientError: Temporary failure, retry may succeed
            AuthenticationError: API key invalid
        """
        ...

    async def refund(
        self,
        payment_id: str,
        amount: Decimal | None = None,
        reason: str | None = None,
    ) -> RefundResult:
        """Process a refund.

        Args:
            payment_id: Original payment ID
            amount: Amount to refund (None = full refund)
            reason: Reason for refund

        Returns:
            RefundResult with status

        Raises:
            PaymentError: If refund fails
        """
        ...


class OrderRepositoryPort(Protocol):
    """Port for order persistence."""

    async def get_by_id(self, order_id: str) -> Order | None:
        """Get an order by ID."""
        ...

    async def save(self, order: Order) -> None:
        """Save an order."""
        ...
