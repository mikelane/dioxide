"""Dependency injection scopes."""

from enum import (
    Enum,
)


class Scope(str, Enum):
    """Component lifecycle scope."""

    SINGLETON = 'singleton'
    FACTORY = 'factory'
