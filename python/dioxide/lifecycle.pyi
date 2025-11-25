"""Type stubs for dioxide lifecycle management.

This module provides type hints for IDE autocomplete and mypy validation
of the @lifecycle decorator and the lifecycle protocol interface.
"""

from typing import Protocol

class LifecycleProtocol(Protocol):
    """Protocol defining the lifecycle interface for components.

    Components decorated with @lifecycle must implement both initialize()
    and dispose() methods as async coroutines. This protocol enables type
    checkers to validate that decorated classes satisfy the requirements.

    Methods:
        async def initialize(self) -> None:
            Called once when container starts (via container.start() or
            async with container:). Use this to establish connections,
            allocate resources, warm caches, etc.

        async def dispose(self) -> None:
            Called once when container stops (via container.stop() or
            when exiting async with block). Use this to close connections,
            release resources, flush buffers, etc. Should be idempotent.

    Example:
        >>> from dioxide import service, lifecycle
        >>>
        >>> @service
        ... @lifecycle
        ... class Database:
        ...     async def initialize(self) -> None:
        ...         self.connection = await connect_to_db()
        ...
        ...     async def dispose(self) -> None:
        ...         if self.connection:
        ...             await self.connection.close()

    Type Checking:
        mypy validates that classes decorated with @lifecycle implement
        both required methods with correct signatures::

            @lifecycle
            class BrokenService:
                pass  # Error: Missing initialize() and dispose()

            @lifecycle
            class SyncService:
                def initialize(self) -> None:  # Error: Not async
                    pass
                async def dispose(self) -> None:
                    pass

    See Also:
        - :class:`dioxide.lifecycle.lifecycle` - The decorator implementation
        - :class:`dioxide.container.Container.start` - Calls initialize()
        - :class:`dioxide.container.Container.stop` - Calls dispose()
    """

    async def initialize(self) -> None: ...
    async def dispose(self) -> None: ...

def lifecycle(cls: type[LifecycleProtocol]) -> type[LifecycleProtocol]:
    """Mark a class for lifecycle management (type stub).

    This is the type stub for the @lifecycle decorator. It provides type
    information for IDEs and mypy, ensuring decorated classes implement
    the LifecycleProtocol interface.

    Args:
        cls: The class to decorate. Must implement initialize() and dispose()
            methods as async coroutines.

    Returns:
        The decorated class with _dioxide_lifecycle attribute set.

    Raises:
        TypeError: If the class doesn't implement required methods (runtime).

    Example:
        >>> @service
        ... @lifecycle
        ... class Database:
        ...     async def initialize(self) -> None:
        ...         pass
        ...     async def dispose(self) -> None:
        ...         pass

    See Also:
        - :class:`dioxide.lifecycle.lifecycle` - Full implementation documentation
        - :class:`LifecycleProtocol` - Required interface
    """
    ...
