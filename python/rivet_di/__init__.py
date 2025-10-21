"""rivet-di: Fast, Rust-backed declarative dependency injection for Python."""

from rivet_di.container import Container
from rivet_di.decorators import component
from rivet_di.scope import Scope

__version__ = '0.1.0'
__all__ = [
    'Container',
    'Scope',
    'component',
]
