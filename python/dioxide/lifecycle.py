"""Lifecycle management decorator for dioxide components."""

from typing import TypeVar

_T = TypeVar('_T', bound=type)


def lifecycle(cls: _T) -> _T:
    """
    Mark a component as having lifecycle management.

    Components decorated with @lifecycle must implement:
    - async def initialize(self) -> None
    - async def dispose(self) -> None

    The container will call these methods at startup/shutdown.
    """
    # TODO: Implementation will be added in Phase 1, Stream 1
    # For now, this is just a marker decorator for type checking
    return cls
