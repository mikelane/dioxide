"""Entry point demonstrating external API integration.

This example shows how to integrate with external APIs (like Stripe)
and how the fake adapter enables error injection testing.
"""

import asyncio
from decimal import Decimal

from dioxide import Container, Profile

from .domain import Order, OrderItem, OrderStatus, PaymentService
from .domain.ports import OrderRepositoryPort


async def main() -> None:
    """Demonstrate external API integration."""
    print("=" * 70)
    print("External API Integration Example")
    print("=" * 70)
    print()
    print("Architecture:")
    print("  PaymentService")
    print("    -> PaymentGatewayPort")
    print("       -> StripeAdapter (production)")
    print("       -> FakePaymentGateway (test, with error injection)")
    print()

    container = Container()
    container.scan("app", profile=Profile.PRODUCTION)

    print("-" * 70)
    print("Initializing services...")
    print("-" * 70)
    print()

    payment_service = container.resolve(PaymentService)
    order_repo = container.resolve(OrderRepositoryPort)

    order = Order(
        id="order-001",
        customer_id="cust-001",
        items=[
            OrderItem(product_id="p1", name="Widget", quantity=2, unit_price=Decimal("29.99")),
            OrderItem(product_id="p2", name="Gadget", quantity=1, unit_price=Decimal("49.99")),
        ],
        card_token="tok_visa_4242",
    )
    await order_repo.save(order)

    print()
    print("-" * 70)
    print(f"Processing payment for order: {order.id}")
    print(f"Total: ${order.total}")
    print("-" * 70)
    print()

    result = await payment_service.process_order_payment(order)

    print()
    print("-" * 70)
    print("Payment result:")
    print("-" * 70)
    print(f"  Status: {result.status.value}")
    print(f"  Payment ID: {result.payment_id}")
    print()

    if result.status == OrderStatus.PAID:
        print("-" * 70)
        print("Processing refund...")
        print("-" * 70)
        print()

        refund_result = await payment_service.process_refund(result)
        print()
        print(f"  Refund status: {refund_result.status.value}")

    print()
    print("=" * 70)
    print("Key Takeaways:")
    print("1. External APIs wrapped in ports for testability")
    print("2. FakePaymentGateway allows error injection in tests")
    print("3. PaymentService handles retries for transient failures")
    print("4. All error scenarios can be tested without real API calls")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
