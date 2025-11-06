"""Decorator for marking classes as DI components.

The @component decorator enables automatic discovery and registration of
classes with the dependency injection container. Decorated classes are
found by Container.scan() and registered with their specified lifecycle
scope (SINGLETON or FACTORY).
"""

from typing import Any, TypeVar, overload

from dioxide.scope import Scope

T = TypeVar('T')

# Global registry for @component decorated classes
_component_registry: set[type[Any]] = set()


@overload
def component(cls: type[T]) -> type[T]: ...


@overload
def component(
    cls: None = None,
    *,
    scope: Scope = Scope.SINGLETON,
) -> Any: ...


def component(
    cls: type[T] | None = None,
    *,
    scope: Scope = Scope.SINGLETON,
) -> type[T] | Any:
    """Mark a class as a dependency injection component.

    This decorator enables automatic discovery and registration with the
    Container. When Container.scan() is called, all @component decorated
    classes are registered with their dependencies automatically resolved
    based on constructor type hints.

    The decorator can be used with or without parentheses:

    Usage:
        Basic usage with default SINGLETON scope:
            >>> from dioxide import component, Container
            >>>
            >>> @component
            ... class Database:
            ...     def connect(self):
            ...         return 'Connected'

        With explicit SINGLETON scope:
            >>> from dioxide import component, Scope
            >>>
            >>> @component(scope=Scope.SINGLETON)
            ... class ConfigService:
            ...     def __init__(self):
            ...         self.settings = {'debug': True}

        With FACTORY scope for per-request instances:
            >>> @component(scope=Scope.FACTORY)
            ... class RequestHandler:
            ...     def __init__(self):
            ...         self.request_id = id(self)

        With constructor-based dependency injection:
            >>> @component
            ... class UserService:
            ...     def __init__(self, db: Database):
            ...         self.db = db

        Auto-discovery and resolution:
            >>> container = Container()
            >>> container.scan()  # Discovers all @component classes
            >>> service = container.resolve(UserService)
            >>> assert isinstance(service.db, Database)

    Args:
        cls: The class being decorated (provided when used without parentheses).
        scope: Lifecycle scope controlling instance creation and caching.
            Defaults to Scope.SINGLETON. Use Scope.FACTORY for new instances
            on each resolve() call.

    Returns:
        The decorated class with dioxide metadata attached. The class can be
        used normally and will be discovered by Container.scan().

    Note:
        - Dependencies are resolved from constructor (__init__) type hints
        - Classes without __init__ or without type hints are supported
        - The decorator does not modify class behavior, only adds metadata
        - Manual registration takes precedence over decorator-based registration
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
    """Get all registered component classes.

    Internal function used by Container.scan() to discover @component
    decorated classes. Returns a copy of the registry to prevent
    external modification.

    Returns:
        Set of all classes that have been decorated with @component.

    Note:
        This is an internal API primarily for testing. Users should
        rely on Container.scan() for component discovery.
    """
    return _component_registry.copy()


def _clear_registry() -> None:
    """Clear the component registry.

    Internal function used in test cleanup to reset the global registry
    state between tests. Should not be used in production code.

    Note:
        This is an internal testing API. Clearing the registry does not
        affect already-configured Container instances.
    """
    _component_registry.clear()
