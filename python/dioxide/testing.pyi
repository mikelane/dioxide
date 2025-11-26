"""Type stubs for dioxide.testing module."""

from contextlib import AbstractAsyncContextManager

from dioxide.container import Container
from dioxide.profile_enum import Profile

def fresh_container(
    profile: Profile | str | None = None,
    package: str | None = None,
) -> AbstractAsyncContextManager[Container]: ...
