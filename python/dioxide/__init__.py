"""dioxide: Fast, Rust-backed declarative dependency injection for Python."""

from .container import Container
from .decorators import _clear_registry, _get_registered_components, component
from .scope import Scope

__version__ = '0.1.0'
__all__ = [
    'Container',
    'Scope',
    '_clear_registry',
    '_get_registered_components',
    'component',
]
