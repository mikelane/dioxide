"""Lifecycle management decorator for dioxide components.

The @lifecycle decorator enables opt-in lifecycle management for components
that need initialization and cleanup.
"""

import inspect
from typing import TypeVar

T = TypeVar('T', bound=type)


def lifecycle(cls: T) -> T:
    """Mark a class as having lifecycle management.

    Components decorated with @lifecycle must implement:
    - async def initialize(self) -> None: Called at container startup
    - async def dispose(self) -> None: Called at container shutdown

    Args:
        cls: The class to mark for lifecycle management

    Returns:
        The class with _dioxide_lifecycle attribute set

    Raises:
        TypeError: If the class does not implement initialize() method

    Example:
        >>> @service
        ... @lifecycle
        ... class Database:
        ...     async def initialize(self) -> None:
        ...         self.engine = create_async_engine(...)
        ...
        ...     async def dispose(self) -> None:
        ...         await self.engine.dispose()
    """
    # Validate that initialize() method exists
    if not hasattr(cls, 'initialize'):
        msg = f'{cls.__name__} must implement initialize() method'
        raise TypeError(msg)

    # Validate that initialize() is async
    init_method = cls.initialize
    if not inspect.iscoroutinefunction(init_method):
        msg = f'{cls.__name__}.initialize() must be async'
        raise TypeError(msg)

    # Validate that dispose() method exists
    if not hasattr(cls, 'dispose'):
        msg = f'{cls.__name__} must implement dispose() method'
        raise TypeError(msg)

    # Validate that dispose() is async
    dispose_method = cls.dispose  # type: ignore[attr-defined]
    if not inspect.iscoroutinefunction(dispose_method):
        msg = f'{cls.__name__}.dispose() must be async'
        raise TypeError(msg)

    cls._dioxide_lifecycle = True  # type: ignore[attr-defined]
    return cls
