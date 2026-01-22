"""Port definitions using Protocol (dioxide style).

Protocol-based interfaces are more Pythonic and work better with type checkers.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


@dataclass
class Order:
    """Order domain model."""

    id: str
    customer_id: str
    items: list[str]
    total: float
    status: str
    created_at: datetime


class OrderRepositoryPort(Protocol):
    """Port for order persistence.

    Protocols define the interface contract without requiring inheritance.
    """

    async def get(self, order_id: str) -> Order | None:
        """Get an order by ID."""
        ...

    async def save(self, order: Order) -> Order:
        """Save an order."""
        ...

    async def find_by_customer(self, customer_id: str) -> list[Order]:
        """Find all orders for a customer."""
        ...


class NotificationPort(Protocol):
    """Port for notifications."""

    async def send(self, recipient: str, message: str) -> bool:
        """Send a notification."""
        ...


class PaymentGatewayPort(Protocol):
    """Port for payment processing."""

    async def charge(self, customer_id: str, amount: float) -> dict:
        """Charge a customer."""
        ...

    async def refund(self, transaction_id: str, amount: float) -> dict:
        """Refund a transaction."""
        ...
