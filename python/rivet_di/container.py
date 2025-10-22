"""Dependency injection container."""

from collections.abc import Callable
from typing import TypeVar

from rivet_di._rivet_core import Container as RustContainer

T = TypeVar('T')


class Container:
    """
    Dependency injection container.

    The container builds a dependency graph from registered components
    and resolves dependencies using the Rust-backed core.
    """

    def __init__(self) -> None:
        """Initialize the container."""
        self._rust_core = RustContainer()

    def register_instance(self, component_type: type[T], instance: T) -> None:
        """
        Register a pre-created instance for a given type.

        Args:
            component_type: Type to register
            instance: Pre-created instance to return for this type

        Raises:
            KeyError: If type is already registered
        """
        self._rust_core.register_instance(component_type, instance)

    def register_class(self, component_type: type[T], implementation: type[T]) -> None:
        """
        Register a class to instantiate for a given type.

        Args:
            component_type: Type to register
            implementation: Class to instantiate (calls __init__ with no args)

        Raises:
            KeyError: If type is already registered
        """
        self._rust_core.register_class(component_type, implementation)

    def register_factory(self, component_type: type[T], factory: Callable[[], T]) -> None:
        """
        Register a factory function for a given type.

        Args:
            component_type: Type to register
            factory: Callable that returns an instance (called with no args)

        Raises:
            KeyError: If type is already registered
        """
        self._rust_core.register_factory(component_type, factory)

    def resolve(self, component_type: type[T]) -> T:
        """
        Resolve a component instance.

        Args:
            component_type: Type to resolve

        Returns:
            Instance of the requested type

        Raises:
            KeyError: If type is not registered
        """
        return self._rust_core.resolve(component_type)

    def is_empty(self) -> bool:
        """
        Check if container has no registered providers.

        Returns:
            True if container is empty, False otherwise
        """
        return self._rust_core.is_empty()

    def __len__(self) -> int:
        """
        Get count of registered providers.

        Returns:
            Number of registered providers
        """
        return len(self._rust_core)
