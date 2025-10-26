"""Decorator for marking classes as DI components."""

from typing import Any, TypeVar

from dioxide.scope import Scope

T = TypeVar('T')

# Global registry for @component decorated classes
_component_registry: set[type[Any]] = set()


def component(
    cls: type[T] | None = None,
    *,
    scope: Scope = Scope.SINGLETON,
) -> type[T] | Any:
    """
    Mark a class as a dependency injection component.

    Can be used with or without arguments:
        @component
        class Service:
            pass

        @component(scope=Scope.FACTORY)
        class Factory:
            pass

    Args:
        cls: The class being decorated (when used without parentheses)
        scope: Lifecycle scope (SINGLETON or FACTORY), defaults to SINGLETON

    Returns:
        Decorated class with DI metadata
    """

    def decorator(target_cls: type[T]) -> type[T]:
        # Store DI metadata on the class
        target_cls.__dioxide_scope__ = scope  # type: ignore[attr-defined]
        # Add to global registry for auto-discovery
        _component_registry.add(target_cls)
        return target_cls

    # Support both @component and @component()
    if cls is None:
        # Called with arguments: @component(scope=...)
        return decorator
    else:
        # Called without arguments: @component
        return decorator(cls)


def _get_registered_components() -> set[type[Any]]:
    """Internal: Get all registered component classes."""
    return _component_registry.copy()


def _clear_registry() -> None:
    """Internal: Clear the component registry (for testing)."""
    _component_registry.clear()
