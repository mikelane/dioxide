"""Adapter layer: infrastructure implementations.

This layer contains concrete implementations of domain ports for
different environments (production, test, development).
"""

from .fakes import FakeCache, FakeEventPublisher, FakeOrderRepository, FakeProductRepository
from .kafka import KafkaEventPublisher
from .postgres import PostgresOrderRepository, PostgresProductRepository
from .redis import RedisCache

__all__ = [
    "PostgresOrderRepository",
    "PostgresProductRepository",
    "RedisCache",
    "KafkaEventPublisher",
    "FakeOrderRepository",
    "FakeProductRepository",
    "FakeCache",
    "FakeEventPublisher",
]
