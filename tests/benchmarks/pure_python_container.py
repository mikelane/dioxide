"""Pure Python reference container for benchmark comparison.

This module provides a minimal dependency injection container implemented
entirely in Python (no Rust/C extensions). It mirrors the core operations
of dioxide's Rust-backed container to enable fair performance comparison.

This is NOT intended for production use. It exists solely to answer:
"How much faster is the Rust backend compared to equivalent pure Python?"
"""

from __future__ import annotations

import inspect
import threading
from typing import (
    Any,
    get_type_hints,
)


class PurePythonContainer:
    """Minimal pure Python DI container for benchmarking.

    Supports:
    - Singleton registration and cached resolution
    - Factory registration (new instance per resolve)
    - Dependency chain resolution via type hints
    - Thread-safe singleton caching
    """

    def __init__(self) -> None:
        self._singletons: dict[type[Any], Any] = {}
        self._factories: dict[type[Any], type[Any]] = {}
        self._singleton_classes: dict[type[Any], type[Any]] = {}
        self._lock = threading.RLock()

    def register_singleton(self, key: type[Any], impl: type[Any]) -> None:
        """Register a type as singleton (cached after first creation)."""
        self._singleton_classes[key] = impl

    def register_factory(self, key: type[Any], impl: type[Any]) -> None:
        """Register a type as factory (new instance each resolve)."""
        self._factories[key] = impl

    def register_singleton_with_deps(self, cls: type[Any]) -> None:
        """Register a singleton that may have constructor dependencies."""
        self._singleton_classes[cls] = cls

    def resolve(self, key: type[Any]) -> Any:
        """Resolve a component by type.

        For singletons: returns cached instance (creating on first call).
        For factories: creates a new instance each time.
        """
        # Fast path: cached singleton
        cached = self._singletons.get(key)
        if cached is not None:
            return cached

        # Factory path: always create new
        factory_cls = self._factories.get(key)
        if factory_cls is not None:
            return factory_cls()

        # Singleton path: create, cache, return
        singleton_cls = self._singleton_classes.get(key)
        if singleton_cls is not None:
            with self._lock:
                # Double-check after acquiring lock
                cached = self._singletons.get(key)
                if cached is not None:
                    return cached

                instance = self._create_with_deps(singleton_cls)
                self._singletons[key] = instance
                return instance

        msg = f'No registration found for {key.__name__}'
        raise KeyError(msg)

    def _create_with_deps(self, cls: type[Any]) -> Any:
        """Create an instance, resolving constructor dependencies."""
        init = cls.__init__
        if init is object.__init__:
            return cls()

        try:
            hints = get_type_hints(init)
        except Exception:
            return cls()

        hints.pop('return', None)
        if not hints:
            return cls()

        kwargs: dict[str, Any] = {}
        sig = inspect.signature(init)
        for param_name, _param in sig.parameters.items():
            if param_name == 'self':
                continue
            dep_type = hints.get(param_name)
            if dep_type is not None:
                kwargs[param_name] = self.resolve(dep_type)

        return cls(**kwargs)
