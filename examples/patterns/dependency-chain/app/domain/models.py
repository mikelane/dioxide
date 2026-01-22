"""Domain models for the order management system.

These are pure data classes with no dependencies on infrastructure.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class Product:
    """A product that can be ordered."""

    id: str
    name: str
    price: float
    stock: int = 100


@dataclass
class OrderItem:
    """A line item in an order."""

    product_id: str
    product_name: str
    quantity: int
    unit_price: float

    @property
    def total(self) -> float:
        """Calculate item total."""
        return self.quantity * self.unit_price


@dataclass
class Order:
    """An order placed by a customer."""

    id: str
    customer_id: str
    items: list[OrderItem]
    status: str = "pending"
    created_at: datetime = field(default_factory=datetime.now)

    @property
    def total(self) -> float:
        """Calculate order total."""
        return sum(item.total for item in self.items)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "customer_id": self.customer_id,
            "items": [
                {
                    "product_id": item.product_id,
                    "product_name": item.product_name,
                    "quantity": item.quantity,
                    "unit_price": item.unit_price,
                    "total": item.total,
                }
                for item in self.items
            ],
            "total": self.total,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
        }
