"""Profile class for hexagonal architecture adapter selection.

This module defines the Profile class that specifies which adapter
implementations should be active for a given environment.

Profile is an extensible, type-safe string subclass that allows both
built-in profiles and custom user-defined profiles.
"""

from __future__ import annotations

from typing import ClassVar


class Profile(str):
    """Extensible, type-safe profile identifier for adapter selection.

    Profile is a string subclass that provides type safety while remaining
    fully extensible. Built-in profiles are available as class attributes,
    and users can create custom profiles for their specific needs.

    **Built-in Profiles**:

    - ``Profile.PRODUCTION`` - Production environment
    - ``Profile.TEST`` - Test environment
    - ``Profile.DEVELOPMENT`` - Development environment
    - ``Profile.STAGING`` - Staging environment
    - ``Profile.CI`` - Continuous integration environment
    - ``Profile.ALL`` - Universal profile (matches all environments)

    **Usage**:

    Use built-in profiles for common environments::

        @adapter.for_(EmailPort, profile=Profile.PRODUCTION)
        @adapter.for_(CachePort, profile=[Profile.TEST, Profile.DEVELOPMENT])
        @adapter.for_(LogPort, profile=Profile.ALL)

    Create custom profiles for specific needs::

        # Define custom profiles (type-safe)
        INTEGRATION = Profile('integration')
        PREVIEW = Profile('preview')
        LOAD_TEST = Profile('load-test')

        @adapter.for_(Port, profile=INTEGRATION)
        @adapter.for_(Port, profile=[PREVIEW, Profile.STAGING])

    **Type Safety**:

    All profiles are instances of ``Profile``, providing static type checking::

        def configure(profile: Profile) -> None: ...


        configure(Profile.PRODUCTION)  # OK
        configure(Profile('custom'))  # OK
        configure('raw-string')  # Type error (if strict)

    **Backward Compatibility**:

    Profile is a ``str`` subclass, so it works anywhere strings are expected.
    Raw strings are still accepted at runtime for backward compatibility,
    but using ``Profile(...)`` is recommended for type safety.

    Examples:
        >>> repr(Profile.PRODUCTION)
        'Profile.PRODUCTION'
        >>> str(Profile.ALL)
        'ALL'
        >>> Profile.PRODUCTION == 'production'
        True
        >>> isinstance(Profile.PRODUCTION, str)
        True
        >>> Profile('custom') == 'custom'
        True
        >>> type(Profile('custom'))
        <class 'dioxide.profile_enum.Profile'>
    """

    # Class-level constants for built-in profiles
    PRODUCTION: ClassVar[Profile]
    TEST: ClassVar[Profile]
    DEVELOPMENT: ClassVar[Profile]
    STAGING: ClassVar[Profile]
    CI: ClassVar[Profile]
    ALL: ClassVar[Profile]

    _BUILTIN_DISPLAY_NAMES: ClassVar[dict[str, str]] = {
        '*': 'ALL',
        'production': 'PRODUCTION',
        'test': 'TEST',
        'development': 'DEVELOPMENT',
        'staging': 'STAGING',
        'ci': 'CI',
    }

    def __new__(cls, value: str) -> Profile:
        """Create a new Profile instance.

        Args:
            value: The profile identifier string. Will be lowercased
                   for consistent matching.

        Returns:
            A new Profile instance.

        Examples:
            >>> Profile('integration') == 'integration'
            True
            >>> Profile('PREVIEW') == 'preview'
            True
        """
        # Lowercase for consistent matching
        return super().__new__(cls, value.lower())

    def __str__(self) -> str:
        """Return the display name, hiding implementation details.

        Built-in profiles return their constant name (e.g., 'ALL' instead
        of '*'). Custom profiles return their string value unchanged.

        Examples:
            >>> str(Profile.ALL)
            'ALL'
            >>> str(Profile.PRODUCTION)
            'PRODUCTION'
            >>> str(Profile('custom'))
            'custom'
        """
        return self._BUILTIN_DISPLAY_NAMES.get(str.__str__(self), str.__str__(self))

    def __format__(self, format_spec: str) -> str:
        """Format using the display name rather than the raw value.

        Examples:
            >>> f'{Profile.ALL:>10}'
            '       ALL'
            >>> f'{Profile.PRODUCTION:>15}'
            '     PRODUCTION'
        """
        return format(str(self), format_spec)

    def __repr__(self) -> str:
        """Return a detailed string representation.

        Built-in profiles show their constant name (e.g., Profile.ALL).
        Custom profiles show the constructor form (e.g., Profile('custom')).

        Examples:
            >>> repr(Profile.ALL)
            'Profile.ALL'
            >>> repr(Profile.PRODUCTION)
            'Profile.PRODUCTION'
            >>> repr(Profile('custom'))
            "Profile('custom')"
        """
        display_name = self._BUILTIN_DISPLAY_NAMES.get(str.__str__(self))
        if display_name is not None:
            return f'Profile.{display_name}'
        return f'Profile({str.__repr__(self)})'


# Initialize built-in profile constants
Profile.PRODUCTION = Profile('production')
Profile.TEST = Profile('test')
Profile.DEVELOPMENT = Profile('development')
Profile.STAGING = Profile('staging')
Profile.CI = Profile('ci')
Profile.ALL = Profile('*')
