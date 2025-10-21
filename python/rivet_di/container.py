"""Dependency injection container."""

from typing import Any, TypeVar

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
        self._components: dict[type, Any] = {}

    def register(self, component_class: type[T]) -> None:
        """
        Register a component class with the container.

        Args:
            component_class: Class decorated with @component

        Raises:
            ValueError: If class is not decorated with @component
        """
        if not hasattr(component_class, '__rivet_scope__'):
            msg = f'{component_class.__name__} must be decorated with @component'
            raise ValueError(msg)

        self._components[component_class] = component_class

    def resolve(self, component_type: type[T]) -> T:
        """
        Resolve a component instance.

        Args:
            component_type: Type to resolve

        Returns:
            Instance of the requested type

        Raises:
            ValueError: If type is not registered
        """
        # Will delegate to Rust core in walking skeleton
        if component_type not in self._components:
            msg = f'{component_type.__name__} is not registered'
            raise ValueError(msg)

        # Placeholder - will use Rust core
        return component_type()  # type: ignore[return-value]
