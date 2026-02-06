"""Module that tracks when it is imported - simulates expensive module-level work."""

from typing import Protocol

from dioxide import (
    Profile,
    adapter,
)


class ExpensivePort(Protocol):
    def do_work(self) -> str: ...


@adapter.for_(ExpensivePort, profile=Profile.PRODUCTION)
class ExpensiveAdapter:
    def do_work(self) -> str:
        return 'expensive'
