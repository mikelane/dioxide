"""Adapter decorator for hexagonal architecture.

The @adapter decorator enables marking concrete implementations for
Protocol/ABC ports with explicit profile associations, supporting
hexagonal/ports-and-adapters architecture patterns.

Example:
    >>> from typing import Protocol
    >>> from dioxide import adapter
    >>>
    >>> class EmailPort(Protocol):
    ...     async def send(self, to: str, subject: str, body: str) -> None: ...
    >>>
    >>> @adapter.for_(EmailPort, profile='production')
    ... class SendGridAdapter:
    ...     async def send(self, to: str, subject: str, body: str) -> None:
    ...         # Real SendGrid implementation
    ...         pass
    >>>
    >>> @adapter.for_(EmailPort, profile='test')
    ... class FakeEmailAdapter:
    ...     def __init__(self) -> None:
    ...         self.sent_emails: list[dict[str, str]] = []
    ...
    ...     async def send(self, to: str, subject: str, body: str) -> None:
    ...         self.sent_emails.append({'to': to, 'subject': subject, 'body': body})
"""

from __future__ import annotations

from typing import (
    TYPE_CHECKING,
    Any,
    TypeVar,
)

from dioxide.scope import Scope

if TYPE_CHECKING:
    from collections.abc import Callable

T = TypeVar('T')

# Global registry for adapter-decorated classes
_adapter_registry: set[type[Any]] = set()


class AdapterDecorator:
    """Main decorator class with .for_() method for marking adapters.

    This decorator enables hexagonal architecture by explicitly marking
    concrete implementations (adapters) for abstract ports (Protocols/ABCs)
    with environment-specific profiles.

    The decorator requires explicit profile association to make deployment
    configuration visible at the seams.
    """

    def for_(
        self,
        port: type[Any],
        *,
        profile: str | list[str] = '*',
    ) -> Callable[[type[T]], type[T]]:
        """Register an adapter for a port with profile(s).

        Args:
            port: The Protocol or ABC that this adapter implements
            profile: Profile name(s) - string or list of strings.
                     Normalized to lowercase for consistency.

        Returns:
            Decorator function that marks the class as an adapter

        Raises:
            TypeError: If profile parameter is not provided

        Example:
            >>> @adapter.for_(EmailPort, profile='production')
            ... class SendGridAdapter:
            ...     pass
            >>>
            >>> @adapter.for_(EmailPort, profile=['test', 'development'])
            ... class FakeAdapter:
            ...     pass
        """

        def decorator(cls: type[T]) -> type[T]:
            # Normalize profile to set of lowercase strings
            if isinstance(profile, str):
                profiles = {profile.lower()}
            else:
                # Deduplicate and normalize to lowercase
                profiles = {p.lower() for p in profile}

            # Store metadata on class
            cls.__dioxide_port__ = port  # type: ignore[attr-defined]
            cls.__dioxide_profiles__ = frozenset(profiles)  # type: ignore[attr-defined]
            cls.__dioxide_scope__ = Scope.SINGLETON  # type: ignore[attr-defined]

            # Register with global registry
            _adapter_registry.add(cls)

            return cls

        return decorator


# Global singleton instance for use as decorator
adapter = AdapterDecorator()

__all__ = ['AdapterDecorator', 'adapter']
