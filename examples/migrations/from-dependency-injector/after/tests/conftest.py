"""Pytest fixtures for dioxide tests.

With dioxide, testing is simpler:
1. Create a container with Profile.TEST
2. Resolve services - fakes are used automatically
"""

import pytest

import app.adapters as _adapters  # noqa: F401 — register adapters
from dioxide import Container, Profile


@pytest.fixture
def container() -> Container:
    """Create a fresh container with test profile.

    No provider overrides needed - Profile.TEST automatically
    selects the fake adapters.
    """
    c = Container(profile=Profile.TEST)
    return c
