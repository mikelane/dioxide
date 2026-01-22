"""Payment service with retry and error handling."""

import asyncio
import uuid

from dioxide import service

from .errors import CardDeclinedError, PaymentError, TransientError, ValidationError
from .models import Order, OrderStatus, PaymentResult, PaymentStatus
from .ports import OrderRepositoryPort, PaymentGatewayPort


@service
class PaymentService:
    """Service for processing order payments.

    Features:
    - Automatic retry for transient failures
    - Proper error handling and order status updates
    - Idempotency key generation for safe retries
    """

    def __init__(
        self,
        gateway: PaymentGatewayPort,
        orders: OrderRepositoryPort,
    ) -> None:
        """Initialize with dependencies."""
        self.gateway = gateway
        self.orders = orders

    async def process_order_payment(
        self,
        order: Order,
        max_retries: int = 3,
    ) -> Order:
        """Process payment for an order with automatic retry.

        Args:
            order: Order to process payment for
            max_retries: Maximum retry attempts for transient failures

        Returns:
            Updated order with payment status
        """
        if not order.card_token:
            order.status = OrderStatus.PAYMENT_FAILED
            order.error_message = "No card token provided"
            await self.orders.save(order)
            return order

        idempotency_key = f"order-{order.id}-{uuid.uuid4()}"

        for attempt in range(max_retries):
            try:
                result = await self.gateway.charge(
                    amount=order.total,
                    currency="USD",
                    card_token=order.card_token,
                    idempotency_key=idempotency_key,
                )

                if result.succeeded:
                    order.status = OrderStatus.PAID
                    order.payment_id = result.id
                    order.error_message = None
                else:
                    order.status = OrderStatus.PAYMENT_FAILED
                    order.error_message = result.error_message

                await self.orders.save(order)
                return order

            except CardDeclinedError as e:
                order.status = OrderStatus.PAYMENT_FAILED
                order.error_message = f"Card declined: {e}"
                await self.orders.save(order)
                return order

            except ValidationError as e:
                order.status = OrderStatus.PAYMENT_FAILED
                order.error_message = f"Validation error: {e}"
                await self.orders.save(order)
                return order

            except TransientError:
                if attempt == max_retries - 1:
                    order.status = OrderStatus.PAYMENT_FAILED
                    order.error_message = "Payment service temporarily unavailable"
                    await self.orders.save(order)
                    return order
                await asyncio.sleep(2**attempt)

            except PaymentError as e:
                order.status = OrderStatus.PAYMENT_FAILED
                order.error_message = str(e)
                await self.orders.save(order)
                return order

        return order

    async def process_refund(
        self,
        order: Order,
        amount: str | None = None,
    ) -> Order:
        """Process a refund for an order.

        Args:
            order: Order to refund
            amount: Amount to refund (None = full refund)

        Returns:
            Updated order with refund status
        """
        if order.status != OrderStatus.PAID or not order.payment_id:
            order.error_message = "Cannot refund: order not paid"
            return order

        try:
            from decimal import Decimal

            refund_amount = Decimal(amount) if amount else None
            result = await self.gateway.refund(
                payment_id=order.payment_id,
                amount=refund_amount,
            )

            if result.succeeded:
                order.status = OrderStatus.REFUNDED
                order.error_message = None
            else:
                order.error_message = f"Refund failed: {result.error_message}"

            await self.orders.save(order)
            return order

        except PaymentError as e:
            order.error_message = f"Refund failed: {e}"
            await self.orders.save(order)
            return order
