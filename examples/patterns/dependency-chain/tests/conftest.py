"""Pytest configuration and fixtures for dependency chain tests."""

import pytest
from dioxide import Container, Profile

from app.domain.models import Product
from app.domain.ports import CachePort, EventPublisherPort, OrderRepositoryPort, ProductRepositoryPort


@pytest.fixture
def container() -> Container:
    """Create a test container with TEST profile.

    This activates all fake adapters automatically.
    """
    c = Container()
    c.scan("app", profile=Profile.TEST)
    return c


@pytest.fixture
def orders(container: Container) -> OrderRepositoryPort:
    """Get the fake order repository."""
    return container.resolve(OrderRepositoryPort)


@pytest.fixture
def products(container: Container) -> ProductRepositoryPort:
    """Get the fake product repository."""
    return container.resolve(ProductRepositoryPort)


@pytest.fixture
def cache(container: Container) -> CachePort:
    """Get the fake cache."""
    return container.resolve(CachePort)


@pytest.fixture
def events(container: Container) -> EventPublisherPort:
    """Get the fake event publisher."""
    return container.resolve(EventPublisherPort)


@pytest.fixture
def seeded_products(products: ProductRepositoryPort) -> ProductRepositoryPort:
    """Seed the product repository with test data."""
    products.seed(
        Product(id="p1", name="Widget", price=10.00, stock=100),
        Product(id="p2", name="Gadget", price=25.00, stock=50),
        Product(id="p3", name="Gizmo", price=5.00, stock=200),
    )
    return products
