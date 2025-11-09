"""Profile decorator for environment-specific component implementations.

The profile system enables "fakes at the seams" testing by allowing different
implementations of the same protocol for different environments (production, test, dev).

Example:
    >>> from typing import Protocol
    >>> from dioxide import component, profile
    >>>
    >>> class EmailProvider(Protocol):
    ...     async def send(self, to: str, subject: str, body: str) -> None: ...
    >>>
    >>> @component.implements(EmailProvider)
    >>> @profile.production
    >>> class SendGridEmail:
    ...     async def send(self, to: str, subject: str, body: str) -> None:
    ...         # Real SendGrid implementation
    ...         pass
    >>>
    >>> @component.implements(EmailProvider)
    >>> @profile.test
    >>> class FakeEmail:
    ...     def __init__(self) -> None:
    ...         self.sent_emails: list[dict[str, str]] = []
    ...
    ...     async def send(self, to: str, subject: str, body: str) -> None:
    ...         self.sent_emails.append({'to': to, 'subject': subject, 'body': body})
"""

from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar, overload

if TYPE_CHECKING:
    from collections.abc import Callable

T = TypeVar('T')

# Attribute name for storing profiles on decorated classes
PROFILE_ATTRIBUTE = '__dioxide_profiles__'


class Profile:
    """Profile decorator for marking components with environment profiles.

    Supports both attribute access (@profile.production) and callable syntax
    (@profile("prod", "staging")) for maximum flexibility.

    Pre-defined profiles:
        - production: Production environment
        - test: Test environment
        - development: Development environment

    Custom profiles via __getattr__:
        - @profile.staging
        - @profile.custom_name

    Multiple profiles:
        - @profile("prod", "staging")

    Attributes:
        production: Decorator for production profile
        test: Decorator for test profile
        development: Decorator for development profile
    """

    def __init__(self) -> None:
        """Initialize Profile decorator."""
        # Pre-defined profile decorators
        self.production = self._create_profile_decorator('production')
        self.test = self._create_profile_decorator('test')
        self.development = self._create_profile_decorator('development')

    def __getattr__(self, name: str) -> Callable[[type[T]], type[T]]:
        """Support custom profiles via attribute access.

        Args:
            name: Profile name (e.g., "staging")

        Returns:
            Decorator function for the custom profile

        Example:
            >>> @profile.staging
            >>> class StagingService:
            ...     pass
        """
        return self._create_profile_decorator(name)

    @overload
    def __call__(self, cls: type[T], /) -> type[T]: ...

    @overload
    def __call__(self, *profile_names: str) -> Callable[[type[T]], type[T]]: ...

    def __call__(self, *args: type[T] | str) -> type[T] | Callable[[type[T]], type[T]]:
        """Support callable syntax for multiple profiles.

        Args:
            *args: Either a single class (when used as @profile) or
                   multiple profile names (when used as @profile("prod", "staging"))

        Returns:
            Decorated class or decorator function

        Raises:
            ValueError: If no profile names provided or empty strings
            TypeError: If profile names are not strings

        Example:
            >>> @profile("prod", "staging")
            >>> class SharedService:
            ...     pass
        """
        # Check if called with a class directly (e.g., @profile without parens)
        # This shouldn't happen in normal usage, but handle it gracefully
        if len(args) == 1 and isinstance(args[0], type):
            # Default to production if used as bare @profile
            cls = args[0]
            return self._create_profile_decorator('production')(cls)

        # Called as @profile("name1", "name2", ...)
        if not args:
            raise ValueError('At least one profile name required')

        # Validate all arguments are strings
        for name in args:
            if not isinstance(name, str):
                raise TypeError('Profile names must be strings')
            if not name:
                raise ValueError('Profile names cannot be empty')

        # Normalize to lowercase - all args are strings at this point
        normalized_names = [name.lower() for name in args]  # type: ignore[union-attr]

        return self._create_multi_profile_decorator(normalized_names)

    def _create_profile_decorator(self, profile_name: str) -> Callable[[type[T]], type[T]]:
        """Create a decorator for a single profile.

        Args:
            profile_name: Name of the profile

        Returns:
            Decorator function
        """

        def decorator(cls: type[T]) -> type[T]:
            """Add profile to class metadata.

            Args:
                cls: Class to decorate

            Returns:
                Same class with profile metadata added
            """
            # Get existing profiles or create new set
            existing_profiles: frozenset[str] = getattr(cls, PROFILE_ATTRIBUTE, frozenset())

            # Add new profile (frozenset is immutable, so create new one)
            new_profiles = existing_profiles | {profile_name.lower()}

            # Store as frozenset (immutable)
            setattr(cls, PROFILE_ATTRIBUTE, frozenset(new_profiles))

            return cls

        return decorator

    def _create_multi_profile_decorator(self, profile_names: list[str]) -> Callable[[type[T]], type[T]]:
        """Create a decorator for multiple profiles.

        Args:
            profile_names: List of profile names (already normalized)

        Returns:
            Decorator function
        """

        def decorator(cls: type[T]) -> type[T]:
            """Add all profiles to class metadata.

            Args:
                cls: Class to decorate

            Returns:
                Same class with profile metadata added
            """
            # Get existing profiles or create new set
            existing_profiles: frozenset[str] = getattr(cls, PROFILE_ATTRIBUTE, frozenset())

            # Add all new profiles (deduplicated by set)
            new_profiles = existing_profiles | set(profile_names)

            # Store as frozenset (immutable)
            setattr(cls, PROFILE_ATTRIBUTE, frozenset(new_profiles))

            return cls

        return decorator


# Global singleton instance for use as decorator
profile = Profile()

__all__ = ['PROFILE_ATTRIBUTE', 'Profile', 'profile']
