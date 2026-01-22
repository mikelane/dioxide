"""Profile enum for hexagonal architecture adapter selection.

This module defines the Profile enum that specifies which adapter
implementations should be active for a given environment.
"""

from __future__ import annotations

from enum import Enum


class Profile(str, Enum):
    """Profile specification for adapters.

    Profiles determine which adapter implementations are active
    for a given environment. The Profile enum provides standard
    environment profiles used throughout dioxide for adapter selection.

    **Canonical Usage Pattern**:

    Always use Profile enum values instead of raw strings::

        # Recommended (canonical pattern)
        @adapter.for_(EmailPort, profile=Profile.PRODUCTION)
        @adapter.for_(CachePort, profile=[Profile.TEST, Profile.DEVELOPMENT])
        @adapter.for_(LogPort, profile=Profile.ALL)

        # Deprecated (emits DeprecationWarning)
        @adapter.for_(EmailPort, profile='production')  # Use Profile.PRODUCTION
        @adapter.for_(CachePort, profile='*')  # Use Profile.ALL

    Attributes:
        PRODUCTION: Production environment profile
        TEST: Test environment profile
        DEVELOPMENT: Development environment profile
        STAGING: Staging environment profile
        CI: Continuous integration environment profile
        ALL: Universal profile - available in all environments

    Examples:
        >>> Profile.PRODUCTION
        <Profile.PRODUCTION: 'production'>
        >>> Profile.PRODUCTION.value
        'production'
        >>> str(Profile.TEST)
        'test'
        >>> Profile('production') == Profile.PRODUCTION
        True
    """

    PRODUCTION = 'production'
    TEST = 'test'
    DEVELOPMENT = 'development'
    STAGING = 'staging'
    CI = 'ci'
    ALL = '*'
