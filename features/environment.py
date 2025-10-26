"""Behave environment configuration for dioxide BDD tests."""

from typing import Any

from behave.runner import Context


def before_all(context: Context) -> None:
    """
    Execute before all tests.

    Set up any global test configuration needed across all scenarios.
    """
    # Verify dioxide is importable
    try:
        import dioxide  # noqa: F401

        context.dioxide_available = True
    except ImportError:
        context.dioxide_available = False
        print('WARNING: dioxide not available - tests will fail')


def before_scenario(context: Context, scenario: Any) -> None:
    """
    Execute before each scenario.

    Clean up context to ensure test isolation.
    """
    # Clear any previous test data - only initialize attributes that are used across scenarios
    context.container = None
    context.containers = {}
    context.exception = None
    context.result = None
    context.thread_errors = []


def after_scenario(context: Context, scenario: Any) -> None:
    """
    Execute after each scenario.

    Clean up resources and verify test state.
    """
    # Clean up any containers - no need to delete, they'll be reset in before_scenario
    pass


def after_all(context: Context) -> None:
    """
    Execute after all tests.

    Final cleanup and reporting.
    """
    pass
