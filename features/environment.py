"""Behave environment configuration for rivet-di BDD tests."""

from typing import (
    Any,
)

from behave.runner import (
    Context,
)


def before_all(context: Context) -> None:
    """
    Execute before all tests.

    Set up any global test configuration needed across all scenarios.
    """
    # Verify rivet-di is importable
    try:
        import rivet_di  # noqa: F401

        context.rivet_di_available = True
    except ImportError:
        context.rivet_di_available = False
        print('WARNING: rivet-di not available - tests will fail')


def before_scenario(context: Context, scenario: Any) -> None:
    """
    Execute before each scenario.

    Clean up context to ensure test isolation.
    """
    # Clear any previous test data
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
    # Clean up any containers
    if hasattr(context, 'container'):
        context.container = None

    if hasattr(context, 'containers'):
        context.containers.clear()


def after_all(context: Context) -> None:
    """
    Execute after all tests.

    Final cleanup and reporting.
    """
    pass
