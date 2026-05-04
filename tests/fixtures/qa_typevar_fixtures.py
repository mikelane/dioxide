"""Fixture module for adversarial QA tests that require module-level
TypeVar annotations to be properly resolved by get_type_hints."""

from __future__ import annotations

from typing import TypeVar

from dioxide import service

T = TypeVar('T', bound=str)


@service
class TypeVarFixture:
    def __init__(self, value: T = 'ok') -> None:  # type: ignore[assignment]
        self.value = value
