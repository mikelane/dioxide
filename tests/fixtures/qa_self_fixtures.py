"""Fixture module for adversarial QA tests that require module-level
typing.Self annotations to be properly resolved by get_type_hints."""

from __future__ import annotations

from typing import Self

from dioxide import service


@service
class SelfFixture:
    def __init__(self, clone: Self | None = None) -> None:  # type: ignore[name-defined,type-arg]
        self.clone = clone


@service
class SelfNoDefaultFixture:
    def __init__(self, clone: Self) -> None:  # type: ignore[name-defined,type-arg]
        self.clone = clone
