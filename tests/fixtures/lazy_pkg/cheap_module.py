"""Module with a simple adapter - does not have expensive side effects."""

from typing import Protocol

from dioxide import (
    Profile,
    adapter,
)

IMPORTED = True


class CheapPort(Protocol):
    def do_work(self) -> str: ...


@adapter.for_(CheapPort, profile=Profile.PRODUCTION)
class CheapAdapter:
    def do_work(self) -> str:
        return 'cheap'
