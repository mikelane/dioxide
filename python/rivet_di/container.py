"""Dependency injection container."""

import inspect
from collections.abc import Callable
from typing import Any, TypeVar, get_type_hints

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

    def scan(self) -> None:
        """
        Discover and register all @component decorated classes.

        This method finds all classes marked with the @component decorator
        and registers them with the container, automatically setting up
        dependency injection based on type hints.

        Components are registered as singletons by default.
        """
        from rivet_di.decorators import _get_registered_components
        from rivet_di.scope import Scope

        for component_class in _get_registered_components():
            # Create a factory that auto-injects dependencies
            factory = self._create_auto_injecting_factory(component_class)

            # Check the scope
            scope = getattr(component_class, '__rivet_scope__', Scope.SINGLETON)

            if scope == Scope.SINGLETON:
                # Wrap the factory in a singleton wrapper
                singleton_factory = self._create_singleton_factory(factory)
                self.register_factory(component_class, singleton_factory)
            else:
                # For non-singletons, just register the factory
                self.register_factory(component_class, factory)

    def _create_singleton_factory(self, factory: Callable[[], T]) -> Callable[[], T]:
        """
        Wrap a factory function to return the same instance each time.

        Args:
            factory: The factory function to wrap

        Returns:
            A factory that caches the first instance and returns it on subsequent calls
        """
        instance_holder: list[T] = []  # Use list to avoid closure issues

        def singleton_wrapper() -> T:
            if not instance_holder:
                instance_holder.append(factory())
            return instance_holder[0]

        return singleton_wrapper

    def _create_auto_injecting_factory(self, cls: type[T]) -> Callable[[], T]:
        """
        Create a factory function that auto-injects dependencies from type hints.

        Args:
            cls: The class to create a factory for

        Returns:
            A factory function that resolves dependencies and instantiates the class
        """
        try:
            init_signature = inspect.signature(cls.__init__)
            type_hints = get_type_hints(cls.__init__)
        except (ValueError, AttributeError):
            # No __init__ or no type hints - just instantiate directly
            return cls

        # Build factory that resolves dependencies
        def factory() -> T:
            kwargs: dict[str, Any] = {}
            for param_name in init_signature.parameters:
                if param_name == 'self':
                    continue
                if param_name in type_hints:
                    dependency_type = type_hints[param_name]
                    kwargs[param_name] = self.resolve(dependency_type)
            return cls(**kwargs)

        return factory
