"""
Type stubs for lifecycle decorator.

The @lifecycle decorator marks components that need initialization/cleanup.
Decorated classes must implement both initialize() and dispose() methods.

These stubs provide IDE autocomplete and documentation. Runtime validation
happens when the decorator is applied.
"""

from typing import TypeVar

# Accept any class type - runtime validation will check for required methods
_T = TypeVar('_T')

def lifecycle(cls: _T) -> _T:
    """
    Mark a component as having lifecycle management.

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
    ...
