"""Tests for Container class."""

import pytest

from rivet_di import (
    Container,
    Scope,
    component,
)


@component(scope=Scope.SINGLETON)
class SingletonService:
    """Test singleton service."""

    pass


@component(scope=Scope.FACTORY)
class FactoryService:
    """Test factory service."""

    pass


class UnregisteredService:
    """Service without @component decorator."""

    pass


def test_container_initialization() -> None:
    """Container initializes successfully."""
    container = Container()
    assert container is not None


def test_register_component() -> None:
    """Container registers a component successfully."""
    container = Container()
    container.register(SingletonService)


def test_register_non_component_raises() -> None:
    """Registering a non-component class raises ValueError."""
    container = Container()
    with pytest.raises(ValueError, match='must be decorated with @component'):
        container.register(UnregisteredService)


def test_resolve_unregistered_raises() -> None:
    """Resolving an unregistered type raises ValueError."""
    container = Container()
    with pytest.raises(ValueError, match='is not registered'):
        container.resolve(SingletonService)
