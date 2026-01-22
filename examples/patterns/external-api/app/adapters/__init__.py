"""Adapters for external API example."""

from .fakes import FakeOrderRepository, FakePaymentGateway
from .stripe import StripeAdapter

__all__ = [
    "StripeAdapter",
    "FakePaymentGateway",
    "FakeOrderRepository",
]
