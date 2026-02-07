"""Pytest configuration for external API tests."""

from decimal import Decimal

import pytest
from dioxide import Container, Profile

import app.adapters as _adapters  # noqa: F401 — register adapters
from app.domain import Order, OrderItem
from app.domain.ports import OrderRepositoryPort, PaymentGatewayPort


@pytest.fixture
def container() -> Container:
    """Create test container."""
    c = Container(profile=Profile.TEST)
    return c


@pytest.fixture
def gateway(container: Container) -> PaymentGatewayPort:
    """Get the fake payment gateway."""
    return container.resolve(PaymentGatewayPort)


@pytest.fixture
def orders(container: Container) -> OrderRepositoryPort:
    """Get the fake order repository."""
    return container.resolve(OrderRepositoryPort)


@pytest.fixture
def sample_order() -> Order:
    """Create a sample order for testing."""
    return Order(
        id="test-order-001",
        customer_id="test-customer-001",
        items=[
            OrderItem(product_id="p1", name="Widget", quantity=2, unit_price=Decimal("10.00")),
            OrderItem(product_id="p2", name="Gadget", quantity=1, unit_price=Decimal("25.00")),
        ],
        card_token="tok_test_card",
    )
