"""Pytest configuration for caching tests."""

import pytest
from dioxide import Container, Profile

import app.adapters as _adapters  # noqa: F401 — register adapters
from app.domain import User, UserRepositoryPort
from app.domain.ports import CachePort


@pytest.fixture
def container() -> Container:
    """Create test container."""
    c = Container(profile=Profile.TEST)
    return c


@pytest.fixture
def repository(container: Container) -> UserRepositoryPort:
    """Get the fake user repository."""
    return container.resolve(UserRepositoryPort)


@pytest.fixture
def cache(container: Container) -> CachePort:
    """Get the fake cache."""
    return container.resolve(CachePort)


@pytest.fixture
def seeded_repository(repository: UserRepositoryPort) -> UserRepositoryPort:
    """Repository with test data."""
    repository.seed(
        User(id="user-1", name="Alice", email="alice@example.com"),
        User(id="user-2", name="Bob", email="bob@example.com"),
    )
    return repository
