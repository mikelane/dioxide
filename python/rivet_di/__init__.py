"""rivet-di: Fast, Rust-backed declarative dependency injection for Python."""

from .container import Container
from .decorators import component
from .scope import Scope

__version__ = '0.1.0'
__all__ = [
    'Container',
    'Scope',
    'component',
]
