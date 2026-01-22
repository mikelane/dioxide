"""Domain models for payment operations."""

from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum


class PaymentStatus(str, Enum):
    """Status of a payment."""

    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    REFUNDED = "refunded"


class RefundStatus(str, Enum):
    """Status of a refund."""

    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


@dataclass
class PaymentResult:
    """Result of a payment operation."""

    id: str
    status: PaymentStatus
    amount: Decimal
    currency: str
    error_message: str | None = None

    @property
    def succeeded(self) -> bool:
        """Check if payment succeeded."""
        return self.status == PaymentStatus.SUCCEEDED


@dataclass
class RefundResult:
    """Result of a refund operation."""

    id: str
    payment_id: str
    status: RefundStatus
    amount: Decimal
    error_message: str | None = None

    @property
    def succeeded(self) -> bool:
        """Check if refund succeeded."""
        return self.status == RefundStatus.SUCCEEDED


@dataclass
class OrderItem:
    """An item in an order."""

    product_id: str
    name: str
    quantity: int
    unit_price: Decimal

    @property
    def total(self) -> Decimal:
        """Calculate item total."""
        return Decimal(self.quantity) * self.unit_price


class OrderStatus(str, Enum):
    """Status of an order."""

    PENDING = "pending"
    PAID = "paid"
    PAYMENT_FAILED = "payment_failed"
    REFUNDED = "refunded"


@dataclass
class Order:
    """An order that needs payment."""

    id: str
    customer_id: str
    items: list[OrderItem]
    status: OrderStatus = OrderStatus.PENDING
    payment_id: str | None = None
    card_token: str = ""
    error_message: str | None = None

    @property
    def total(self) -> Decimal:
        """Calculate order total."""
        return sum((item.total for item in self.items), Decimal("0"))
