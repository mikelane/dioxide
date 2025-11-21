"""Lifecycle management decorator for dioxide components."""

from typing import TypeVar

_T = TypeVar('_T', bound=type)


def lifecycle(cls: _T) -> _T:
    """
    Mark a component as having lifecycle management.

    The @lifecycle decorator marks components that need initialization/cleanup.
    Decorated classes must implement both initialize() and dispose() methods.

    **Required methods:**

    .. code-block:: python

        class MyComponent:
            async def initialize(self) -> None:
                '''Called by container at startup.'''
                ...

            async def dispose(self) -> None:
                '''Called by container at shutdown.'''
                ...

    **Usage:**

    .. code-block:: python

        @service
        @lifecycle
        class Database:
            async def initialize(self) -> None:
                self.conn = await create_connection()

            async def dispose(self) -> None:
                await self.conn.close()

    Args:
        cls: The class to decorate

    Returns:
        The same class, marked for lifecycle management

    Raises:
        TypeError: At decoration time if required methods are missing
            or have wrong signatures
    """
    # TODO: Implementation will be added in Phase 1, Stream 1
    # For now, this is just a marker decorator for type checking
    return cls
