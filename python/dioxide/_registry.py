"""Internal registry for component and adapter tracking.

This module provides the global registries used by @service and @adapter decorators
for automatic discovery during container.scan().

INTERNAL API - Do not import directly. Use Container.scan() for component discovery.
"""

from __future__ import annotations

from typing import (
    TYPE_CHECKING,
    Any,
)

if TYPE_CHECKING:
    from dioxide.adapter import _adapter_registry  # noqa: F401

# Global registry for @component/@service decorated classes
_component_registry: set[type[Any]] = set()


def _get_registered_components() -> set[type[Any]]:
    """Get all registered component classes.

    Internal function used by Container.scan() to discover @service
    decorated classes. Returns a copy of the registry to prevent
    external modification.

    Returns:
        Set of all classes that have been decorated with @service.

    Note:
        This is an internal API primarily for testing. Users should
        rely on Container.scan() for component discovery.
    """
    return _component_registry.copy()


def _clear_registry() -> None:
    """Clear the component and adapter registries.

    Internal function used in test cleanup to reset the global registry
    state between tests. Should not be used in production code.

    Note:
        This is an internal testing API. Clearing the registry does not
        affect already-configured Container instances.
    """
    # Import here to avoid circular imports
    from dioxide.adapter import _adapter_registry  # noqa: PLC0415

    _component_registry.clear()
    _adapter_registry.clear()


# Attribute name for storing profiles on decorated classes
PROFILE_ATTRIBUTE = '__dioxide_profiles__'

__all__ = ['PROFILE_ATTRIBUTE', '_clear_registry', '_component_registry', '_get_registered_components']
