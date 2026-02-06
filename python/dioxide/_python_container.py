"""Pure Python container implementation for benchmark comparison.

This module provides a pure Python implementation of the dependency injection
container, mirroring the Rust-backed container's interface. It exists solely
for performance benchmarking to quantify the value of the Rust backend.

This is NOT intended for production use.
"""

from __future__ import annotations

from collections.abc import Callable
from enum import (
    Enum,
    auto,
)
from typing import Any


class _ProviderKind(Enum):
    INSTANCE = auto()
    CLASS = auto()
    SINGLETON_FACTORY = auto()
    TRANSIENT_FACTORY = auto()


class _Provider:
    __slots__ = ('kind', 'value')

    def __init__(self, kind: _ProviderKind, value: Any) -> None:
        self.kind = kind
        self.value = value


class PythonContainer:
    """Pure Python dependency injection container for benchmarking."""

    def __init__(self) -> None:
        self._providers: dict[type, _Provider] = {}
        self._singletons: dict[type, object] = {}

    def is_empty(self) -> bool:
        return len(self._providers) == 0

    def __len__(self) -> int:
        return len(self._providers)

    def register_instance(self, component_type: type, instance: object) -> None:
        if component_type in self._providers:
            raise KeyError(f'Duplicate provider registration: {component_type.__name__}')
        self._providers[component_type] = _Provider(_ProviderKind.INSTANCE, instance)

    def register_class(self, component_type: type, implementation: type) -> None:
        if component_type in self._providers:
            raise KeyError(f'Duplicate provider registration: {component_type.__name__}')
        self._providers[component_type] = _Provider(_ProviderKind.CLASS, implementation)

    def register_singleton_factory(self, component_type: type, factory: Callable[[], Any]) -> None:
        if component_type in self._providers:
            raise KeyError(f'Duplicate provider registration: {component_type.__name__}')
        self._providers[component_type] = _Provider(_ProviderKind.SINGLETON_FACTORY, factory)

    def register_transient_factory(self, component_type: type, factory: Callable[[], Any]) -> None:
        if component_type in self._providers:
            raise KeyError(f'Duplicate provider registration: {component_type.__name__}')
        self._providers[component_type] = _Provider(_ProviderKind.TRANSIENT_FACTORY, factory)

    def resolve(self, component_type: type) -> Any:
        if component_type in self._singletons:
            return self._singletons[component_type]

        provider = self._providers.get(component_type)
        if provider is None:
            raise KeyError(f'Dependency not registered: {component_type.__name__}')

        if provider.kind == _ProviderKind.INSTANCE:
            return provider.value

        if provider.kind == _ProviderKind.SINGLETON_FACTORY:
            instance = provider.value()
            self._singletons[component_type] = instance
            return instance

        if provider.kind == _ProviderKind.TRANSIENT_FACTORY:
            return provider.value()

        if provider.kind == _ProviderKind.CLASS:
            return provider.value()

        raise KeyError(f'Dependency not registered: {component_type.__name__}')

    def reset(self) -> None:
        self._singletons.clear()

    def contains(self, component_type: type) -> bool:
        return component_type in self._providers

    def get_registered_types(self) -> list[type]:
        return list(self._providers.keys())

    def register_singleton(self, component_type: type, factory: Callable[[], Any]) -> None:
        self.register_singleton_factory(component_type, factory)

    def register_factory(self, component_type: type, factory: Callable[[], Any]) -> None:
        self.register_transient_factory(component_type, factory)
