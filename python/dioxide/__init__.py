"""dioxide: Fast, Rust-backed declarative dependency injection for Python.

dioxide is a modern dependency injection framework that combines:
- Declarative Python API with @component decorators
- High-performance Rust-backed container implementation
- Type-safe dependency resolution with IDE autocomplete support
- Support for SINGLETON and FACTORY component lifecycles

Quick Start (using global singleton container):
    >>> from dioxide import container, component
    >>>
    >>> @component
    ... class Database:
    ...     pass
    >>>
    >>> @component
    ... class UserService:
    ...     def __init__(self, db: Database):
    ...         self.db = db
    >>>
    >>> container.scan()
    >>> service = container.resolve(UserService)
    >>> # Or use bracket syntax:
    >>> service = container[UserService]
    >>> assert isinstance(service.db, Database)

Advanced: Creating separate containers for testing isolation:
    >>> from dioxide import Container, component
    >>>
    >>> test_container = Container()
    >>> test_container.scan()
    >>> service = test_container.resolve(UserService)

For more information, see the README and documentation.
"""

from .container import Container, container
from .decorators import _clear_registry, _get_registered_components, component
from .profile import profile
from .scope import Scope

__version__ = '0.1.0'
__all__ = [
    'Container',
    'Scope',
    '_clear_registry',
    '_get_registered_components',
    'component',
    'container',
    'profile',
]
