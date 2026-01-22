"""Custom exceptions for payment operations.

These exceptions represent different failure modes that can occur
when interacting with external payment APIs.
"""


class PaymentError(Exception):
    """Base class for payment-related errors."""

    pass


class CardDeclinedError(PaymentError):
    """Raised when a card is declined."""

    pass


class ValidationError(PaymentError):
    """Raised for invalid payment data."""

    pass


class NetworkError(PaymentError):
    """Raised for network-level failures."""

    pass


class TransientError(PaymentError):
    """Raised for temporary failures that may succeed on retry."""

    pass


class AuthenticationError(PaymentError):
    """Raised when API authentication fails."""

    pass


class RateLimitError(TransientError):
    """Raised when rate limits are exceeded."""

    pass
