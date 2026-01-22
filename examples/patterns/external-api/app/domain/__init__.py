"""Domain layer for external API example."""

from .errors import (
    AuthenticationError,
    CardDeclinedError,
    NetworkError,
    PaymentError,
    RateLimitError,
    TransientError,
    ValidationError,
)
from .models import Order, OrderItem, OrderStatus, PaymentResult, RefundResult
from .ports import OrderRepositoryPort, PaymentGatewayPort
from .services import PaymentService

__all__ = [
    "PaymentResult",
    "RefundResult",
    "Order",
    "OrderItem",
    "OrderStatus",
    "PaymentGatewayPort",
    "OrderRepositoryPort",
    "PaymentService",
    "PaymentError",
    "CardDeclinedError",
    "ValidationError",
    "NetworkError",
    "TransientError",
    "AuthenticationError",
    "RateLimitError",
]
