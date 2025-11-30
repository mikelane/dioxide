"""Adapter layer containing port implementations for different profiles."""

# Import adapters to ensure they're registered with dioxide
from . import (
    fakes,
    logging_email,
)

__all__ = [
    "fakes",
    "logging_email",
]
