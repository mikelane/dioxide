"""Type stubs for Rust core module."""

from typing import (
    Any,
)

class Container:
    """Rust-backed container implementation."""

    def __init__(self) -> None: ...
    def resolve(self, type_name: str) -> Any: ...
