"""Pytest configuration and fixtures for Flask example tests.

This module sets up the test environment using dioxide's TEST profile,
which activates fake adapters for fast, deterministic testing.
"""

import os

import pytest

# Set TEST profile BEFORE importing the app
os.environ["PROFILE"] = "test"

from app.adapters.fakes import (
    FakeDatabaseAdapter,
    FakeEmailAdapter,
)
from app.domain.ports import (
    DatabasePort,
    EmailPort,
)
from app.main import app


@pytest.fixture
def client():
    """Create a test client for the Flask app.

    The test client allows making HTTP requests to the app without
    running a real server.
    """
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def container():
    """Get the dioxide container from the app.

    The container is stored in app.config by configure_dioxide().
    """
    return app.config["dioxide_container"]


@pytest.fixture
def db(container):
    """Get the fake database adapter for testing.

    This allows tests to verify database state directly without
    going through the API.
    """
    adapter = container.resolve(DatabasePort)
    # Verify we got the fake (not a production adapter)
    assert isinstance(adapter, FakeDatabaseAdapter)
    # Clear state between tests
    adapter.users.clear()
    adapter._next_id = 1
    return adapter


@pytest.fixture
def email(container):
    """Get the fake email adapter for testing.

    This allows tests to verify what emails were "sent" without
    actually sending any emails.
    """
    adapter = container.resolve(EmailPort)
    # Verify we got the fake (not a production adapter)
    assert isinstance(adapter, FakeEmailAdapter)
    # Clear state between tests
    adapter.clear()
    return adapter
