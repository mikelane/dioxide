"""Decorator for marking classes as DI components."""

from typing import (
    Any,
    TypeVar,
)

from rivet_di.scope import (
    Scope,
)

T = TypeVar('T')


def component(
    scope: Scope = Scope.SINGLETON,
) -> Any:
    """
    Mark a class as a dependency injection component.

    Args:
        scope: Lifecycle scope (SINGLETON or FACTORY)

    Returns:
        Decorated class with DI metadata

    Example:
        >>> @component(scope=Scope.SINGLETON)
        ... class DatabaseConnection:
        ...     pass
    """

    def decorator(cls: type[T]) -> type[T]:
        # Store DI metadata on the class
        cls.__rivet_scope__ = scope  # type: ignore[attr-defined]
        return cls

    return decorator
