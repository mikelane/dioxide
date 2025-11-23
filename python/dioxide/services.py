"""Service decorator for core domain logic.

The @service decorator marks classes as core domain logic that:
- Is a singleton (one shared instance across the application)
- Available in ALL profiles (doesn't vary by environment)
- Supports constructor-based dependency injection via type hints

Services represent the core business logic layer in hexagonal architecture,
sitting between ports (interfaces) and adapters (implementations).
"""

from typing import TypeVar

from dioxide._registry import _component_registry
from dioxide.scope import Scope

T = TypeVar('T')


def service(cls: type[T]) -> type[T]:
    """Mark a class as a core domain service.

    Services are singleton components that represent core business logic.
    They are available in all profiles (production, test, development) and
    support automatic dependency injection.

    This is a specialized form of @component that:
    - Always uses SINGLETON scope (one shared instance)
    - Does not require profile specification (available everywhere)
    - Represents core domain logic in hexagonal architecture

    Usage:
        Basic service:
            >>> from dioxide import service
            >>>
            >>> @service
            ... class UserService:
            ...     def create_user(self, name: str) -> dict:
            ...         return {'name': name, 'id': 1}

        Service with dependencies:
            >>> @service
            ... class EmailService:
            ...     pass
            >>>
            >>> @service
            ... class NotificationService:
            ...     def __init__(self, email: EmailService):
            ...         self.email = email

        Auto-discovery and resolution:
            >>> from dioxide import container
            >>>
            >>> container.scan()
            >>> notifications = container.resolve(NotificationService)
            >>> assert isinstance(notifications.email, EmailService)

    Args:
        cls: The class being decorated.

    Returns:
        The decorated class with dioxide metadata attached. The class can be
        used normally and will be discovered by Container.scan().

    Note:
        - Services are always SINGLETON scope
        - Services are available in all profiles
        - Dependencies are resolved from constructor (__init__) type hints
        - For profile-specific implementations, use @component with @profile
    """
    # Store DI metadata on the class
    cls.__dioxide_scope__ = Scope.SINGLETON  # type: ignore[attr-defined]
    cls.__dioxide_profiles__ = frozenset(['*'])  # type: ignore[attr-defined]  # Available in all profiles
    # Add to global registry for auto-discovery
    _component_registry.add(cls)
    return cls
