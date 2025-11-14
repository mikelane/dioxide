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
