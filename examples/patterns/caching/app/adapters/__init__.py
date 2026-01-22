"""Adapters for the caching example."""

from .caching import CachingUserRepository
from .fakes import FakeCache, FakeUserRepository
from .postgres import PostgresUserRepository
from .redis import RedisCache

__all__ = [
    "PostgresUserRepository",
    "CachingUserRepository",
    "RedisCache",
    "FakeUserRepository",
    "FakeCache",
]
