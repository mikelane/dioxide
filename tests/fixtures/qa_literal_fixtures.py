"""Fixture module for adversarial QA tests that require module-level
Literal type annotations to be properly resolved by get_type_hints."""

from __future__ import annotations

from typing import Literal

from dioxide import service


@service
class LiteralStringFixture:
    def __init__(self, mode: Literal['dev', 'prod'] = 'dev') -> None:
        self.mode = mode


@service
class LiteralIntFixture:
    def __init__(self, level: Literal[1, 2, 3] = 1) -> None:
        self.level = level
