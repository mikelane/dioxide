"""Pytest fixtures for dioxide tests.

With dioxide, testing is simpler - no TestModule needed.
Just create a container with Profile.TEST.
"""

import pytest

import app.adapters as _adapters  # noqa: F401 — register adapters
from dioxide import Container, Profile


@pytest.fixture
def container() -> Container:
    """Create a fresh container with test profile.

    Profile.TEST automatically selects the fake adapters.
    No module configuration needed.
    """
    c = Container(profile=Profile.TEST)
    return c
