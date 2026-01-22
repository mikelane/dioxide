"""Tests for PaymentService demonstrating error injection.

These tests show how to use FakePaymentGateway to test various
error scenarios without making real API calls.
"""

from decimal import Decimal

from dioxide import Container

from app.domain import (
    CardDeclinedError,
    NetworkError,
    Order,
    OrderItem,
    OrderStatus,
    PaymentService,
    RateLimitError,
    TransientError,
    ValidationError,
)
from app.domain.ports import OrderRepositoryPort, PaymentGatewayPort


class DescribePaymentService:
    """Tests for successful payment scenarios."""

    async def it_processes_payment_successfully(
        self,
        container: Container,
        orders: OrderRepositoryPort,
        sample_order: Order,
    ) -> None:
        """PaymentService processes payment and updates order status."""
        await orders.save(sample_order)
        service = container.resolve(PaymentService)

        result = await service.process_order_payment(sample_order)

        assert result.status == OrderStatus.PAID
        assert result.payment_id is not None
        assert result.error_message is None

    async def it_records_payment_id_on_order(
        self,
        container: Container,
        orders: OrderRepositoryPort,
        gateway: PaymentGatewayPort,
        sample_order: Order,
    ) -> None:
        """PaymentService stores payment ID on order."""
        await orders.save(sample_order)
        service = container.resolve(PaymentService)

        result = await service.process_order_payment(sample_order)

        assert result.payment_id is not None
        assert result.payment_id.startswith("fake_pay_")

    async def it_charges_correct_amount(
        self,
        container: Container,
        orders: OrderRepositoryPort,
        gateway: PaymentGatewayPort,
        sample_order: Order,
    ) -> None:
        """PaymentService charges the order total."""
        await orders.save(sample_order)
        service = container.resolve(PaymentService)

        await service.process_order_payment(sample_order)

        assert gateway.was_charged(sample_order.total)


class DescribeErrorInjection:
    """Tests demonstrating error injection capabilities."""

    async def it_handles_card_declined(
        self,
        container: Container,
        orders: OrderRepositoryPort,
        gateway: PaymentGatewayPort,
        sample_order: Order,
    ) -> None:
        """PaymentService handles card declined gracefully."""
        gateway.configure_to_fail(CardDeclinedError("Insufficient funds"))
        await orders.save(sample_order)
        service = container.resolve(PaymentService)

        result = await service.process_order_payment(sample_order)

        assert result.status == OrderStatus.PAYMENT_FAILED
        assert "declined" in result.error_message.lower()

    async def it_handles_validation_error(
        self,
        container: Container,
        orders: OrderRepositoryPort,
        gateway: PaymentGatewayPort,
        sample_order: Order,
    ) -> None:
        """PaymentService handles validation errors."""
        gateway.configure_to_fail(ValidationError("Invalid card number"))
        await orders.save(sample_order)
        service = container.resolve(PaymentService)

        result = await service.process_order_payment(sample_order)

        assert result.status == OrderStatus.PAYMENT_FAILED
        assert "validation" in result.error_message.lower()

    async def it_handles_network_error(
        self,
        container: Container,
        orders: OrderRepositoryPort,
        gateway: PaymentGatewayPort,
        sample_order: Order,
    ) -> None:
        """PaymentService handles network errors."""
        gateway.configure_to_fail(NetworkError("Connection refused"))
        await orders.save(sample_order)
        service = container.resolve(PaymentService)

        result = await service.process_order_payment(sample_order)

        assert result.status == OrderStatus.PAYMENT_FAILED


class DescribeRetryBehavior:
    """Tests for retry logic with transient failures."""

    async def it_retries_transient_failures(
        self,
        container: Container,
        orders: OrderRepositoryPort,
        gateway: PaymentGatewayPort,
        sample_order: Order,
    ) -> None:
        """PaymentService retries on transient failures."""
        gateway.configure_transient_failure(
            fail_count=2,
            error=TransientError("Connection timeout"),
        )
        await orders.save(sample_order)
        service = container.resolve(PaymentService)

        result = await service.process_order_payment(sample_order, max_retries=3)

        assert result.status == OrderStatus.PAID
        assert gateway.call_count == 3

    async def it_fails_after_max_retries(
        self,
        container: Container,
        orders: OrderRepositoryPort,
        gateway: PaymentGatewayPort,
        sample_order: Order,
    ) -> None:
        """PaymentService gives up after max retries."""
        gateway.configure_transient_failure(
            fail_count=5,
            error=TransientError("Connection timeout"),
        )
        await orders.save(sample_order)
        service = container.resolve(PaymentService)

        result = await service.process_order_payment(sample_order, max_retries=3)

        assert result.status == OrderStatus.PAYMENT_FAILED
        assert "unavailable" in result.error_message.lower()
        assert gateway.call_count == 3

    async def it_handles_rate_limiting(
        self,
        container: Container,
        orders: OrderRepositoryPort,
        gateway: PaymentGatewayPort,
        sample_order: Order,
    ) -> None:
        """PaymentService handles rate limit errors with retry."""
        gateway.configure_transient_failure(
            fail_count=1,
            error=RateLimitError("Too many requests"),
        )
        await orders.save(sample_order)
        service = container.resolve(PaymentService)

        result = await service.process_order_payment(sample_order)

        assert result.status == OrderStatus.PAID


class DescribeRefunds:
    """Tests for refund functionality."""

    async def it_processes_refund_for_paid_order(
        self,
        container: Container,
        orders: OrderRepositoryPort,
        gateway: PaymentGatewayPort,
        sample_order: Order,
    ) -> None:
        """PaymentService can refund a paid order."""
        await orders.save(sample_order)
        service = container.resolve(PaymentService)

        paid_order = await service.process_order_payment(sample_order)
        assert paid_order.status == OrderStatus.PAID

        refunded_order = await service.process_refund(paid_order)

        assert refunded_order.status == OrderStatus.REFUNDED
        assert len(gateway.refund_calls) == 1

    async def it_rejects_refund_for_unpaid_order(
        self,
        container: Container,
        orders: OrderRepositoryPort,
        sample_order: Order,
    ) -> None:
        """PaymentService rejects refund for unpaid orders."""
        await orders.save(sample_order)
        service = container.resolve(PaymentService)

        result = await service.process_refund(sample_order)

        assert result.status == OrderStatus.PENDING
        assert "not paid" in result.error_message.lower()


class DescribeMissingCardToken:
    """Tests for orders without card token."""

    async def it_fails_order_without_card_token(
        self,
        container: Container,
        orders: OrderRepositoryPort,
    ) -> None:
        """PaymentService fails orders without card token."""
        order = Order(
            id="no-card-order",
            customer_id="test-customer",
            items=[OrderItem(product_id="p1", name="Widget", quantity=1, unit_price=Decimal("10.00"))],
            card_token="",
        )
        await orders.save(order)
        service = container.resolve(PaymentService)

        result = await service.process_order_payment(order)

        assert result.status == OrderStatus.PAYMENT_FAILED
        assert "card token" in result.error_message.lower()


class DescribeFakeGateway:
    """Tests demonstrating FakePaymentGateway capabilities."""

    async def it_tracks_all_charge_attempts(
        self,
        container: Container,
        orders: OrderRepositoryPort,
        gateway: PaymentGatewayPort,
        sample_order: Order,
    ) -> None:
        """FakePaymentGateway records all charge attempts."""
        await orders.save(sample_order)
        service = container.resolve(PaymentService)

        await service.process_order_payment(sample_order)

        assert len(gateway.charge_calls) == 1
        assert gateway.charge_calls[0]["amount"] == sample_order.total
        assert gateway.charge_calls[0]["card_token"] == sample_order.card_token

    async def it_can_be_reset_between_tests(
        self,
        container: Container,
        gateway: PaymentGatewayPort,
    ) -> None:
        """FakePaymentGateway can be reset for test isolation."""
        gateway.configure_to_fail(CardDeclinedError("Test"))
        assert gateway.should_fail is True

        gateway.reset()

        assert gateway.should_fail is False
        assert gateway.fail_with is None
        assert len(gateway.charge_calls) == 0
