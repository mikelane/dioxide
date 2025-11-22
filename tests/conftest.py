"""Pytest configuration and shared fixtures for dioxide tests."""

import sys

import pytest

from dioxide import _clear_registry


@pytest.fixture(autouse=True)
def clear_registry() -> None:
    """Clear the component registry before each test to ensure test isolation.

    This autouse fixture automatically runs before every test function,
    preventing test pollution by clearing all registered components.

    Also clears test fixture modules from sys.modules to ensure decorators
    re-execute when modules are imported again.
    """
    _clear_registry()

    # Clear test fixture modules from sys.modules to force decorator re-execution
    fixture_modules = [key for key in sys.modules if key.startswith('tests.fixtures')]
    for module_name in fixture_modules:
        del sys.modules[module_name]
