"""Module with a TEST profile adapter for multi-package lazy scan tests."""

from typing import Protocol

from dioxide import (
    Profile,
    adapter,
)


class TestPort(Protocol):
    def do_work(self) -> str: ...


@adapter.for_(TestPort, profile=Profile.TEST)
class TestAdapter:
    def do_work(self) -> str:
        return 'test'
