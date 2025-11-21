from typing import (
    Protocol,
    TypeVar,
)

class LifecycleProtocol(Protocol):
    async def initialize(self) -> None: ...
    async def dispose(self) -> None: ...

_T = TypeVar('_T', bound=LifecycleProtocol)

def lifecycle(cls: type[_T]) -> type[_T]: ...
