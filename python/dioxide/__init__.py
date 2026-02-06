"""dioxide: Fast, Rust-backed declarative dependency injection for Python.

dioxide is a modern dependency injection framework that combines:
- Declarative Python API with hexagonal architecture support
- High-performance Rust-backed container implementation
- Type-safe dependency resolution with IDE autocomplete support
- Profile-based configuration for different environments

Quick Start (using instance container - recommended):
    >>> from dioxide import Container, service, adapter, Profile
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
    >>> container = Container()
    >>> container.scan(profile=Profile.PRODUCTION)
    >>> user_service = container.resolve(UserService)
    >>> # Or use bracket syntax:
    >>> user_service = container[UserService]

Global container (convenient for simple scripts):
    >>> from dioxide import container, Profile
    >>>
    >>> container.scan(profile=Profile.PRODUCTION)
    >>> user_service = container.resolve(UserService)
    >>>
    >>> # For testing with global container, use reset_global_container()
    >>> from dioxide import reset_global_container
    >>> reset_global_container()

Testing (fresh container per test - recommended):
    >>> from dioxide.testing import fresh_container
    >>> from dioxide import Profile
    >>>
    >>> async with fresh_container(profile=Profile.TEST) as test_container:
    ...     service = test_container.resolve(UserService)
    ...     # Test with isolated container

For more information, see the README and documentation.
"""

from importlib.metadata import version as _metadata_version

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
    CircularDependencyError,
    DioxideError,
    ResolutionError,
    ScopeError,
    ServiceNotFoundError,
)
from .lifecycle import lifecycle
from .profile_enum import Profile
from .scope import Scope
from .services import service
from .testing import fresh_container

__version__ = _metadata_version('dioxide')
__all__ = [
    'AdapterNotFoundError',
    'CaptiveDependencyError',
    'CircularDependencyError',
    'Container',
    'DioxideError',
    'Profile',
    'ResolutionError',
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
