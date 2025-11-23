"""Pytest configuration and fixtures for FastAPI example tests.

This module sets up the test environment with:
- TEST profile to activate fake adapters
- Test client for making HTTP requests
- Container access for verifying adapter behavior
"""

import os

import pytest
from fastapi.testclient import TestClient

# Set TEST profile BEFORE importing app
os.environ["PROFILE"] = "test"

from app.main import app, container  # noqa: E402
from app.domain.ports import DatabasePort, EmailPort  # noqa: E402


@pytest.fixture
def client() -> TestClient:
    """Create FastAPI test client.

    The test client automatically handles the lifespan context manager,
    which initializes and disposes the dioxide container.

    Returns:
        TestClient for making HTTP requests to the app
    """
    return TestClient(app)


@pytest.fixture
def db() -> DatabasePort:
    """Get the database adapter from container.

    In TEST profile, this will be FakeDatabaseAdapter.

    Returns:
        Database port (fake in tests)
    """
    return container.resolve(DatabasePort)


@pytest.fixture
def email() -> EmailPort:
    """Get the email adapter from container.

    In TEST profile, this will be FakeEmailAdapter.

    Returns:
        Email port (fake in tests)
    """
    return container.resolve(EmailPort)


@pytest.fixture(autouse=True)
def clear_fakes(db: DatabasePort, email: EmailPort) -> None:
    """Clear fake adapters before each test.

    This ensures tests don't interfere with each other by starting
    with clean state.

    Note: This assumes fakes have a clear() method. If not, you could
    recreate the container, but that's slower.
    """
    # Clear database
    if hasattr(db, "users"):
        db.users.clear()
        if hasattr(db, "_next_id"):
            db._next_id = 1

    # Clear email
    if hasattr(email, "sent_emails"):
        email.sent_emails.clear()
