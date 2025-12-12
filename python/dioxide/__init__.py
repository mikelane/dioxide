"""dioxide: Fast, Rust-backed declarative dependency injection for Python.

dioxide is a modern dependency injection framework that combines:
- Declarative Python API with hexagonal architecture support
- High-performance Rust-backed container implementation
- Type-safe dependency resolution with IDE autocomplete support
- Profile-based configuration for different environments

Quick Start (using global singleton container):
    >>> from dioxide import container, service, adapter, Profile
    >>> from typing import Protocol
    >>>
    >>> class EmailPort(Protocol):
    ...     async def send(self, to: str, subject: str, body: str) -> None: ...
    >>>
    >>> @adapter.for_(EmailPort, profile=Profile.PRODUCTION)
    ... class SendGridAdapter:
    ...     async def send(self, to: str, subject: str, body: str) -> None:
    ...         pass  # Real implementation
    >>>
    >>> @service
    ... class UserService:
    ...     def __init__(self, email: EmailPort):
    ...         self.email = email
    >>>
    >>> container.scan(profile=Profile.PRODUCTION)
    >>> service = container.resolve(UserService)
    >>> # Or use bracket syntax:
    >>> service = container[UserService]

Advanced: Creating separate containers for testing isolation:
    >>> from dioxide import Container
    >>>
    >>> test_container = Container()
    >>> test_container.scan(profile=Profile.TEST)
    >>> service = test_container.resolve(UserService)

For more information, see the README and documentation.
"""

from ._registry import (
    _clear_registry,
    _get_registered_components,
)
from .adapter import adapter
from .container import (
    Container,
    ScopedContainer,
    container,
    reset_global_container,
)
from .exceptions import (
    AdapterNotFoundError,
    CaptiveDependencyError,
    ScopeError,
    ServiceNotFoundError,
)
from .lifecycle import lifecycle
from .profile_enum import Profile
from .scope import Scope
from .services import service
from .testing import fresh_container

__version__ = '1.0.0'
__all__ = [
    'AdapterNotFoundError',
    'CaptiveDependencyError',
    'Container',
    'Profile',
    'Scope',
    'ScopeError',
    'ScopedContainer',
    'ServiceNotFoundError',
    '_clear_registry',
    '_get_registered_components',
    'adapter',
    'container',
    'fresh_container',
    'lifecycle',
    'reset_global_container',
    'service',
]
