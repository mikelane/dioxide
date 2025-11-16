"""Pytest configuration and shared fixtures for dioxide tests."""

import pytest

from dioxide import _clear_registry


@pytest.fixture(autouse=True)
def clear_registry() -> None:
    """Clear the component registry before each test to ensure test isolation.

    This autouse fixture automatically runs before every test function,
    preventing test pollution by clearing all registered components.
    """
    _clear_registry()
