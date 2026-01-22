"""Port definitions using ABC (injector style).

injector typically uses ABC-based interfaces for dependency binding.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Order:
    """Order domain model."""

    id: str
    customer_id: str
    items: list[str]
    total: float
    status: str
    created_at: datetime


class OrderRepository(ABC):
    """Abstract base class for order persistence."""

    @abstractmethod
    async def get(self, order_id: str) -> Order | None:
        """Get an order by ID."""
        pass

    @abstractmethod
    async def save(self, order: Order) -> Order:
        """Save an order."""
        pass

    @abstractmethod
    async def find_by_customer(self, customer_id: str) -> list[Order]:
        """Find all orders for a customer."""
        pass


class NotificationService(ABC):
    """Abstract base class for notifications."""

    @abstractmethod
    async def send(self, recipient: str, message: str) -> bool:
        """Send a notification."""
        pass


class PaymentGateway(ABC):
    """Abstract base class for payment processing."""

    @abstractmethod
    async def charge(self, customer_id: str, amount: float) -> dict:
        """Charge a customer."""
        pass

    @abstractmethod
    async def refund(self, transaction_id: str, amount: float) -> dict:
        """Refund a transaction."""
        pass
