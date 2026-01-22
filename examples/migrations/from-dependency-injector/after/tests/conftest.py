"""Pytest fixtures for dioxide tests.

With dioxide, testing is simpler:
1. Create a container with Profile.TEST
2. Scan the app package
3. Resolve services - fakes are used automatically
"""

import pytest

from dioxide import Container, Profile


@pytest.fixture
def container() -> Container:
    """Create a fresh container with test profile.

    No provider overrides needed - Profile.TEST automatically
    selects the fake adapters.
    """
    c = Container()
    c.scan("app", profile=Profile.TEST)
    return c
