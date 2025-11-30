"""Pytest configuration and fixtures for FastAPI example tests.

This module demonstrates the RECOMMENDED testing patterns for dioxide:

1. **Fresh Container Per Test** - Complete test isolation (RECOMMENDED)
2. Typed fixtures for accessing fake adapters
3. TestClient integration with FastAPI lifespan

## Fresh Container Per Test Pattern (RECOMMENDED)

The recommended approach for test isolation is creating a fresh Container
instance for each test. This provides:

- **Clean singleton cache**: No state from previous tests
- **Fresh adapter instances**: Each test gets new fake instances
- **Automatic lifecycle management**: Use async context manager for cleanup
- **Complete isolation**: Tests cannot interfere with each other

Example::

    @pytest.fixture
    async def container():
        '''Fresh container per test - complete test isolation.'''
        c = Container()
        c.scan(profile=Profile.TEST)
        async with c:
            yield c
        # Cleanup happens automatically

This pattern is superior to clearing fake state because:

1. No risk of missing a fake's state
2. No coupling to fake implementation details
3. Works with @lifecycle components automatically
4. Simpler to understand and maintain

## Why Not Share a Container?

Sharing a container across tests creates coupling:

- Tests may pass in isolation but fail together
- Order-dependent failures are hard to debug
- State leakage causes flaky tests
- Requires knowing all fakes' internal state to reset

## This Example's Approach

This FastAPI example uses a module-level container for the app, which
matches how a real FastAPI application works. For test isolation, we
clear fake state between tests using the `clear_fakes` fixture.

For simpler applications or unit tests, prefer the fresh container pattern
shown above. The fixture-based clearing shown here is appropriate when:

- You need to test with TestClient (requires module-level app)
- The app's container is already initialized
- You're doing integration testing with the full app

See Also:
    - docs/TESTING_GUIDE.md: Comprehensive testing patterns
    - MLP_VISION.md: Testing philosophy (fakes > mocks)
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

import pytest
from fastapi.testclient import TestClient

# Set TEST profile BEFORE importing app
os.environ["PROFILE"] = "test"

from app.domain.ports import DatabasePort, EmailPort  # noqa: E402
from app.main import app  # noqa: E402

# Import the global container - DioxideMiddleware uses this when no explicit
# container is provided. The middleware scans and manages this container.
from dioxide import container  # noqa: E402

if TYPE_CHECKING:
    from app.adapters.fakes import FakeDatabaseAdapter, FakeEmailAdapter


# =============================================================================
# Test Client Fixture
# =============================================================================


@pytest.fixture
def client():
    """Create FastAPI test client with lifespan management.

    The test client uses context manager to handle the lifespan events,
    which initializes and disposes the dioxide container via DioxideMiddleware.

    IMPORTANT: This fixture must start BEFORE any fixtures that try to
    resolve from the container, because DioxideMiddleware only scans/starts
    the container on lifespan.startup (triggered by context manager entry).

    Yields:
        TestClient for making HTTP requests to the app
    """
    with TestClient(app) as client:
        yield client


# =============================================================================
# Typed Fake Adapter Fixtures
# =============================================================================
#
# These fixtures provide typed access to fake adapters for:
# - Seeding test data (e.g., db.users[1] = {...})
# - Verifying side effects (e.g., assert len(email.sent_emails) == 1)
#
# The return type annotation allows IDE autocomplete and type checking
# for fake-specific methods like `sent_emails` or `seed()`.
# =============================================================================


@pytest.fixture
def db(clear_fakes: None) -> FakeDatabaseAdapter:
    """Typed access to fake database for seeding and verification.

    In TEST profile, this returns FakeDatabaseAdapter which provides:
    - `users: dict[int, User]` - Direct access to stored users
    - `_next_id: int` - Auto-incrementing ID counter

    Example::

        def test_user_creation(db, client):
            # Seed test data
            db.users[1] = User(id=1, name="Alice", email="alice@example.com")

            # Make request
            response = client.get("/users/1")

            # Verify
            assert response.json()["name"] == "Alice"

    Returns:
        FakeDatabaseAdapter instance with test utilities
    """
    # Type assertion for IDE support - container.resolve returns the protocol type,
    # but in TEST profile we know it's actually the fake adapter
    adapter = container.resolve(DatabasePort)
    return adapter  # type: ignore[return-value]


@pytest.fixture
def email(clear_fakes: None) -> FakeEmailAdapter:
    """Typed access to fake email for verification.

    In TEST profile, this returns FakeEmailAdapter which provides:
    - `sent_emails: list[dict]` - All emails sent during the test

    Example::

        async def test_welcome_email(email, client):
            # Trigger action that sends email
            client.post("/users", json={"name": "Bob", "email": "bob@example.com"})

            # Verify email was sent
            assert len(email.sent_emails) == 1
            assert email.sent_emails[0]["to"] == "bob@example.com"
            assert "Welcome" in email.sent_emails[0]["subject"]

    Returns:
        FakeEmailAdapter instance with sent_emails list
    """
    adapter = container.resolve(EmailPort)
    return adapter  # type: ignore[return-value]


# =============================================================================
# Test Isolation Fixture
# =============================================================================


@pytest.fixture(autouse=True)
def clear_fakes(client) -> None:
    """Clear fake adapter state before each test for isolation.

    This fixture runs automatically before each test (autouse=True) and
    resets all fake adapters to their initial state.

    IMPORTANT: Depends on `client` to ensure the TestClient is started
    (triggering lifespan.startup which scans/starts the container) before
    we try to resolve adapters from the container.

    IMPORTANT: This approach requires knowing all fakes' internal state.
    For simpler test isolation, consider the fresh container pattern::

        @pytest.fixture
        async def container():
            '''Fresh container per test - recommended pattern.'''
            c = Container()
            c.scan(profile=Profile.TEST)
            async with c:
                yield c

    The fresh container pattern provides better isolation because:
    1. No risk of missing a fake's state
    2. Works with @lifecycle components automatically
    3. No coupling to fake implementation details

    Note:
        This fixture uses hasattr checks to handle cases where the
        container might have different adapter implementations.
    """
    # Get adapters from container (safe now - client fixture ensures lifespan ran)
    db_adapter = container.resolve(DatabasePort)
    email_adapter = container.resolve(EmailPort)

    # Clear database fake
    if hasattr(db_adapter, "users"):
        db_adapter.users.clear()
        if hasattr(db_adapter, "_next_id"):
            db_adapter._next_id = 1

    # Clear email fake
    if hasattr(email_adapter, "sent_emails"):
        email_adapter.sent_emails.clear()


# =============================================================================
# Alternative: Fresh Container Per Test (RECOMMENDED for unit tests)
# =============================================================================
#
# For unit tests that don't need TestClient, the fresh container pattern
# is simpler and provides better isolation:
#
# @pytest.fixture
# async def container():
#     """Isolated container per test - complete test isolation.
#
#     Each test gets a fresh Container instance with:
#     - Clean singleton cache (no state from previous tests)
#     - Fresh adapter instances
#     - Automatic lifecycle management via async context manager
#
#     This is the RECOMMENDED pattern for test isolation.
#     """
#     c = Container()
#     c.scan(profile=Profile.TEST)
#     async with c:
#         yield c
#
#
# @pytest.fixture
# def email(container) -> FakeEmailAdapter:
#     """Typed access to fake email for assertions."""
#     return container.resolve(EmailPort)
#
#
# @pytest.fixture
# def db(container) -> FakeDatabaseAdapter:
#     """Typed access to fake db for seeding."""
#     return container.resolve(DatabasePort)
# =============================================================================
