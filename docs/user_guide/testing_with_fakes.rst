Testing with Fakes
==================

**Version:** 1.0.0

**Last Updated:** 2025-11-22

**Status:** Canonical testing guide for dioxide

----

Introduction
------------

This guide documents dioxide's core testing philosophy: **use fast, simple fakes instead of mocking frameworks**.

Why This Matters
~~~~~~~~~~~~~~~~

Traditional Python testing relies heavily on mocking frameworks (``unittest.mock``, ``pytest-mock``). While mocks have their place, they create several problems:

- **Brittle tests** - Tests break when implementation changes
- **False confidence** - Tests pass but real code fails
- **Obscured intent** - What are we actually testing?
- **Complexity** - Mock setup becomes harder than the code being tested

dioxide takes a different approach: **use real implementations that are fast and deterministic**. These are called "fakes".

The dioxide Philosophy
~~~~~~~~~~~~~~~~~~~~~~~

    **Testing is architecture.** Good architecture makes testing easy without mocks.

dioxide encourages hexagonal architecture (ports-and-adapters), which creates natural seams for testing. Instead of mocking, you write simple fake implementations at these seams.

**Result**: Tests that are fast, clear, and test real behavior.

----

The Problem with Mocks
-----------------------

Anti-Pattern: Testing Mock Behavior
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Here's a typical test using mocks:

.. code-block:: python

    # ❌ BAD: Testing mock configuration, not real code
    from unittest.mock import Mock, patch

    def test_user_registration_with_mock():
        # Arrange: Set up mocks
        mock_db = Mock()
        mock_email = Mock()
        mock_db.create_user.return_value = {"id": "123", "email": "alice@example.com"}
        mock_email.send_welcome.return_value = True

        # Act: Call the service
        service = UserService(mock_db, mock_email)
        result = service.register_user("Alice", "alice@example.com")

        # Assert: Verify mock calls
        mock_db.create_user.assert_called_once_with("Alice", "alice@example.com")
        mock_email.send_welcome.assert_called_once()
        assert result["id"] == "123"

Problems with This Approach
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**1. Tight Coupling to Implementation**

The test knows too much about *how* the service works:

- It knows the exact method names (``create_user``, ``send_welcome``)
- It knows the order of operations
- It knows the exact arguments passed

If you refactor the service (rename methods, change order, etc.), tests break even though *behavior* didn't change.

**2. Unclear Test Intent**

What is this test actually verifying?

- That the service calls the right methods?
- That the service returns the right data?
- That user registration works correctly?

The mock setup obscures what we're trying to prove.

**3. Mocks Can Lie**

.. code-block:: python

    # Test passes...
    mock_db.create_user.return_value = {"id": "123"}

    # But real code fails!
    # (Real create_user raises DatabaseError on duplicate email)

Mocks give false confidence. They pass when real code would fail.

**4. Mock Setup is Complex**

.. code-block:: python

    # Complex mock setup becomes harder than the code being tested
    mock_email = Mock()
    mock_email.send.return_value = Mock(status_code=200)
    mock_email.send.side_effect = [
        Mock(status_code=500),  # First call fails
        Mock(status_code=200),  # Retry succeeds
    ]

When mock setup is more complex than the code under test, you've lost the plot.

The Root Cause
~~~~~~~~~~~~~~

**Mocks test implementation, not behavior.**

They verify that the code *does* something (calls methods), not that it *achieves* something (registers user successfully).

----

Fakes at the Seams
------------------

The dioxide Way: Real Implementations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Instead of mocks, use **fast, real implementations** for testing:

.. code-block:: python

    # ✅ GOOD: Using fakes with dioxide
    import pytest
    from dioxide import Container, Profile, adapter, service
    from typing import Protocol

    # Port (interface)
    class EmailPort(Protocol):
        async def send(self, to: str, subject: str, body: str) -> None: ...

    class UserRepository(Protocol):
        async def create_user(self, name: str, email: str) -> dict: ...

    # Fake implementations (in production code!)
    @adapter.for_(EmailPort, profile=Profile.TEST)
    class FakeEmailAdapter:
        def __init__(self):
            self.sent_emails = []

        async def send(self, to: str, subject: str, body: str) -> None:
            self.sent_emails.append({"to": to, "subject": subject, "body": body})

    @adapter.for_(UserRepository, profile=Profile.TEST)
    class FakeUserRepository:
        def __init__(self):
            self.users = {}

        async def create_user(self, name: str, email: str) -> dict:
            user = {"id": str(len(self.users) + 1), "name": name, "email": email}
            self.users[user["id"]] = user
            return user

    # Service (business logic)
    @service
    class UserService:
        def __init__(self, db: UserRepository, email: EmailPort):
            self.db = db
            self.email = email

        async def register_user(self, name: str, email_addr: str):
            # Real business logic runs!
            user = await self.db.create_user(name, email_addr)
            await self.email.send(
                to=email_addr,
                subject="Welcome!",
                body=f"Hello {name}, thanks for signing up!"
            )
            return user

    # Test - clean and clear
    async def test_user_registration():
        # Arrange: Set up container with fakes
        container = Container()
        container.scan(profile=Profile.TEST)  # Activates fakes!

        # Act: Call REAL service with REAL fakes
        service = container.resolve(UserService)
        result = await service.register_user("Alice", "alice@example.com")

        # Assert: Check REAL observable outcomes
        assert result["name"] == "Alice"
        assert result["email"] == "alice@example.com"

        # Verify email was sent (natural verification)
        email_adapter = container.resolve(EmailPort)
        assert len(email_adapter.sent_emails) == 1
        assert email_adapter.sent_emails[0]["to"] == "alice@example.com"
        assert email_adapter.sent_emails[0]["subject"] == "Welcome!"

Benefits of This Approach
~~~~~~~~~~~~~~~~~~~~~~~~~~

**1. Tests Real Code**

The business logic in ``UserService.register_user()`` actually runs. You're testing real behavior, not mock configuration.

**2. Fast and Deterministic**

Fakes are in-memory (no I/O), so tests are fast. No database, no API calls, no flaky network.

**3. Clear Intent**

The test clearly shows what it's verifying:

- User is created with correct data
- Welcome email is sent to correct address

No mock setup obscuring the purpose.

**4. Refactor-Friendly**

You can refactor ``UserService`` internals without breaking tests, as long as behavior stays the same.

**5. Reusable Fakes**

The same ``FakeEmailAdapter`` works for:

- Unit tests
- Integration tests
- Development environment
- Demos and documentation

Where Fakes Live
~~~~~~~~~~~~~~~~

**IMPORTANT**: Fakes live in **production code**, not test code:

.. code-block:: text

    app/
      domain/
        services.py           # Business logic (@service)

      adapters/
        postgres.py           # @adapter.for_(UserRepository, profile=Profile.PRODUCTION)
        sendgrid.py           # @adapter.for_(EmailPort, profile=Profile.PRODUCTION)

        # Fakes in production code!
        fake_repository.py    # @adapter.for_(UserRepository, profile=Profile.TEST)
        fake_email.py         # @adapter.for_(EmailPort, profile=Profile.TEST)
        fake_clock.py         # @adapter.for_(Clock, profile=Profile.TEST)

**Why in production code?**

1. Reusable across tests, dev environment, and demos
2. Maintained alongside real implementations
3. Documents the port's contract (what methods are required)
4. Can be shipped for user testing
5. Developers can run app locally without PostgreSQL, SendGrid, etc.

----

Writing Effective Fakes
-----------------------

Fakes should be simple, fast, and deterministic. Here are patterns for writing effective fakes.

Simple In-Memory Fakes
~~~~~~~~~~~~~~~~~~~~~~~

The most common pattern: store data in memory instead of database.

.. code-block:: python

    from typing import Protocol
    from dioxide import adapter, Profile

    # Port
    class UserRepository(Protocol):
        async def find_by_id(self, user_id: int) -> dict | None: ...
        async def create(self, name: str, email: str) -> dict: ...
        async def update(self, user: dict) -> None: ...
        async def delete(self, user_id: int) -> None: ...

    # Fake implementation
    @adapter.for_(UserRepository, profile=Profile.TEST)
    class FakeUserRepository:
        """In-memory user repository for testing."""

        def __init__(self):
            self.users: dict[int, dict] = {}
            self._next_id = 1

        async def find_by_id(self, user_id: int) -> dict | None:
            return self.users.get(user_id)

        async def create(self, name: str, email: str) -> dict:
            user = {
                "id": self._next_id,
                "name": name,
                "email": email,
            }
            self.users[self._next_id] = user
            self._next_id += 1
            return user

        async def update(self, user: dict) -> None:
            if user["id"] in self.users:
                self.users[user["id"]] = user

        async def delete(self, user_id: int) -> None:
            self.users.pop(user_id, None)

        # Test-only helper (not in protocol!)
        def seed(self, *users: dict) -> None:
            """Seed with test data."""
            for user in users:
                self.users[user["id"]] = user

**Key points**:

- Simple dict storage
- Auto-incrementing ID
- Implements all protocol methods
- Test-only ``seed()`` helper for test setup

Fakes with Verification
~~~~~~~~~~~~~~~~~~~~~~~~

For services that produce side effects (email, logging, events), capture calls for verification.

.. code-block:: python

    from typing import Protocol
    from dioxide import adapter, Profile

    # Port
    class EmailPort(Protocol):
        async def send(self, to: str, subject: str, body: str) -> None: ...

    # Fake with verification
    @adapter.for_(EmailPort, profile=Profile.TEST)
    class FakeEmailAdapter:
        """Fake email that captures sends for verification."""

        def __init__(self):
            self.sent_emails = []  # Record all sends

        async def send(self, to: str, subject: str, body: str) -> None:
            self.sent_emails.append({
                "to": to,
                "subject": subject,
                "body": body,
            })

        # Test-only helpers (not in protocol!)
        def verify_sent_to(self, email: str) -> bool:
            """Check if email was sent to address."""
            return any(e["to"] == email for e in self.sent_emails)

        def verify_subject_contains(self, text: str) -> bool:
            """Check if any email subject contains text."""
            return any(text in e["subject"] for e in self.sent_emails)

        def clear(self) -> None:
            """Clear sent emails (for test isolation)."""
            self.sent_emails = []

**Usage in tests**:

.. code-block:: python

    from dioxide import Container, Profile

    async def test_welcome_email_sent(container: Container):
        service = container.resolve(UserService)
        await service.register_user("Alice", "alice@example.com")

        # Natural verification
        email = container.resolve(EmailPort)
        assert email.verify_sent_to("alice@example.com")
        assert email.verify_subject_contains("Welcome")

Controllable Fakes
~~~~~~~~~~~~~~~~~~

For testing time-dependent logic, make fakes controllable.

.. code-block:: python

    from datetime import datetime, UTC
    from typing import Protocol
    from dioxide import adapter, Profile

    # Port
    class Clock(Protocol):
        def now(self) -> datetime: ...

    # Controllable fake
    @adapter.for_(Clock, profile=Profile.TEST)
    class FakeClock:
        """Controllable fake clock for testing time logic."""

        def __init__(self):
            self._now = datetime(2024, 1, 1, tzinfo=UTC)

        def now(self) -> datetime:
            return self._now

        # Test-only control methods
        def set_time(self, dt: datetime) -> None:
            """Set current time."""
            self._now = dt

        def advance(self, **kwargs) -> None:
            """Advance time by delta."""
            from datetime import timedelta
            self._now += timedelta(**kwargs)

**Usage in tests**:

.. code-block:: python

    from datetime import datetime, timedelta, UTC
    from dioxide import Container

    async def test_throttles_within_30_days(container: Container):
        clock = container.resolve(Clock)
        users = container.resolve(UserRepository)
        service = container.resolve(NotificationService)

        # Set initial time
        clock.set_time(datetime(2024, 1, 1, tzinfo=UTC))

        # First send succeeds
        users.seed({"id": 1, "email": "alice@example.com", "last_sent": None})
        result = await service.send_welcome(1)
        assert result is True

        # Advance 14 days
        clock.advance(days=14)

        # Second send is throttled
        result = await service.send_welcome(1)
        assert result is False  # Throttled!

        # Advance 20 more days (total 34 days)
        clock.advance(days=20)

        # Third send succeeds
        result = await service.send_welcome(1)
        assert result is True

Fakes with Errors
~~~~~~~~~~~~~~~~~

For testing error handling, make fakes configurable to fail.

.. code-block:: python

    from typing import Protocol
    from dioxide import adapter, Profile

    # Port
    class PaymentGateway(Protocol):
        async def charge(self, amount: float, card: str) -> dict: ...

    # Define custom exception
    class PaymentError(Exception):
        """Payment processing error."""
        pass

    # Fake with error injection
    @adapter.for_(PaymentGateway, profile=Profile.TEST)
    class FakePaymentGateway:
        """Fake payment gateway with error injection."""

        def __init__(self):
            self.charges = []
            self.should_fail = False
            self.failure_reason = "Card declined"

        async def charge(self, amount: float, card: str) -> dict:
            if self.should_fail:
                raise PaymentError(self.failure_reason)

            charge = {
                "id": f"ch_{len(self.charges) + 1}",
                "amount": amount,
                "card": card,
                "status": "succeeded",
            }
            self.charges.append(charge)
            return charge

        # Test-only control
        def fail_next_charge(self, reason: str = "Card declined") -> None:
            """Make next charge fail."""
            self.should_fail = True
            self.failure_reason = reason

        def reset(self) -> None:
            """Clear state between tests."""
            self.charges = []
            self.should_fail = False
            self.failure_reason = "Card declined"

**Usage in tests**:

.. code-block:: python

    import pytest
    from dioxide import Container

    async def test_payment_failure_handling(container: Container):
        gateway = container.resolve(PaymentGateway)
        service = container.resolve(CheckoutService)

        # Configure fake to fail
        gateway.fail_next_charge(reason="Insufficient funds")

        # Test error handling
        with pytest.raises(PaymentError) as exc_info:
            await service.checkout(cart_id=123, card="4242424242424242")

        assert "Insufficient funds" in str(exc_info.value)

    # Use fixture with cleanup to prevent state leakage
    @pytest.fixture
    def payment_gateway(container: Container):
        """Get payment gateway with automatic cleanup."""
        gateway = container.resolve(PaymentGateway)
        yield gateway
        gateway.reset()  # Clean up after test

Shared Fakes Across Tests
~~~~~~~~~~~~~~~~~~~~~~~~~~

Fakes are reusable. Define once, use everywhere.

.. code-block:: python

    # conftest.py - Shared test fixtures
    import pytest
    from dioxide import Container, Profile

    @pytest.fixture
    def container():
        """Container with test fakes."""
        c = Container()
        c.scan(profile=Profile.TEST)
        return c

    @pytest.fixture
    def fake_email(container) -> FakeEmailAdapter:
        """Get the fake email adapter."""
        return container.resolve(EmailPort)

    @pytest.fixture
    def fake_users(container) -> FakeUserRepository:
        """Get the fake user repository."""
        return container.resolve(UserRepository)

    @pytest.fixture
    def fake_clock(container) -> FakeClock:
        """Get the fake clock."""
        return container.resolve(Clock)

    # Individual tests can use these fixtures
    async def test_sends_email(fake_email, container):
        service = container.resolve(UserService)
        await service.register_user("Alice", "alice@example.com")

        assert len(fake_email.sent_emails) == 1

Guidelines for Writing Fakes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**DO**:

- ✅ Keep fakes simple (less logic than real implementation)
- ✅ Make fakes fast (in-memory, no I/O)
- ✅ Make fakes deterministic (no random behavior, controllable time)
- ✅ Add test-only helpers (``seed()``, ``verify_*()``, ``clear()``)
- ✅ Implement the full protocol (all methods)
- ✅ Put fakes in production code (reusable)

**DON'T**:

- ❌ Make fakes complex (defeats the purpose)
- ❌ Add business logic to fakes (keep them dumb)
- ❌ Make fakes stateful across tests (use ``clear()`` or fresh container)
- ❌ Use fakes for code that doesn't need them (pure functions don't need fakes)

----

Profile-Based Testing
---------------------

dioxide's profile system makes it trivial to swap between real implementations and fakes.

Fast Unit Tests (TEST Profile)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Most tests should use the TEST profile with fakes.

.. code-block:: python

    # conftest.py
    import pytest
    from dioxide import Container, Profile

    @pytest.fixture
    def container():
        """Container with test fakes for fast unit tests."""
        c = Container()
        c.scan(profile=Profile.TEST)  # Use fakes!
        return c

    # test_user_service.py
    async def test_user_registration(container):
        # Fast - no database, no API calls
        service = container.resolve(UserService)
        result = await service.register_user("Alice", "alice@example.com")

        assert result["name"] == "Alice"

**Characteristics**:

- Fast (milliseconds)
- No external dependencies
- Deterministic (no flaky failures)
- Run on every commit

Integration Tests (PRODUCTION Profile)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Some tests need real implementations to verify integration.

.. code-block:: python

    # test_integration.py
    import pytest
    from dioxide import Container, Profile

    @pytest.fixture
    def prod_container():
        """Container with production adapters."""
        c = Container()
        c.scan(profile=Profile.PRODUCTION)
        return c

    @pytest.mark.integration
    async def test_database_integration(prod_container):
        # Slower - uses real PostgreSQL
        repo = prod_container.resolve(UserRepository)
        user = await repo.create("Alice", "alice@example.com")

        # Verify in real database
        found = await repo.find_by_id(user["id"])
        assert found["email"] == "alice@example.com"

**Characteristics**:

- Slower (seconds)
- Requires external services (PostgreSQL, Redis, etc.)
- More realistic
- Run pre-merge or nightly

CI/CD Test Strategy
~~~~~~~~~~~~~~~~~~~

Organize tests by speed and profile:

.. code-block:: python

    # pytest.ini or pyproject.toml
    [tool.pytest.ini_options]
    markers = [
        "unit: Fast unit tests with fakes (TEST profile)",
        "integration: Slower integration tests (PRODUCTION profile)",
    ]

    # Run fast tests always
    # pytest -m unit

    # Run integration tests pre-merge
    # pytest -m integration

**CI pipeline**:

.. code-block:: yaml

    # .github/workflows/ci.yml
    jobs:
      unit-tests:
        runs-on: ubuntu-latest
        steps:
          - uses: actions/checkout@v4
          - name: Run unit tests
            run: pytest -m unit  # Fast, uses TEST profile

      integration-tests:
        runs-on: ubuntu-latest
        services:
          postgres:
            image: postgres:15
            env:
              POSTGRES_PASSWORD: postgres
        steps:
          - uses: actions/checkout@v4
          - name: Run integration tests
            run: pytest -m integration  # Slower, uses PRODUCTION profile

Development Profile
~~~~~~~~~~~~~~~~~~~

Use the DEVELOPMENT profile for running the app locally without real services.

.. code-block:: python

    # dev.py - Local development script
    from dioxide import Container, Profile

    async def main():
        # Development mode: in-memory storage, console email
        container = Container()
        container.scan(profile=Profile.DEVELOPMENT)

        # Seed with dev data
        users = container.resolve(UserRepository)
        users.seed(
            {"id": 1, "email": "dev@example.com", "name": "Dev User"},
            {"id": 2, "email": "test@example.com", "name": "Test User"},
        )

        # Run dev server (no PostgreSQL, no SendGrid needed!)
        print("Development environment ready!")
        print("Using in-memory database and console email")
        # ... start FastAPI/Flask app

Multiple Profiles in One Adapter
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Adapters can be available in multiple profiles:

.. code-block:: python

    from typing import Protocol
    from dioxide import adapter, Profile

    class EmailPort(Protocol):
        async def send(self, to: str, subject: str, body: str) -> None: ...

    # Simple adapter for both test and development
    @adapter.for_(EmailPort, profile=[Profile.TEST, Profile.DEVELOPMENT])
    class SimpleEmailAdapter:
        """Simple email for test and dev (logs to console)."""

        def __init__(self):
            self.sent_emails = []

        async def send(self, to: str, subject: str, body: str) -> None:
            self.sent_emails.append({"to": to, "subject": subject, "body": body})
            print(f"📧 Email to {to}: {subject}")

----

Lifecycle in Tests
------------------

When testing components with lifecycle (``@lifecycle``), use the container's async context manager.

.. note::

    Container lifecycle management (``async with container``, ``container.start()``, ``container.stop()``) is available in v0.0.4-alpha and later. If you're using an earlier version, the ``@lifecycle`` decorator is available but container integration is not yet implemented.

Container Lifecycle
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from dioxide import Container, Profile

    async def test_with_lifecycle():
        """Test with lifecycle components."""
        container = Container()
        container.scan(profile=Profile.TEST)

        # Use async context manager
        async with container:
            # All @lifecycle components initialized here
            service = container.resolve(UserService)
            result = await service.register_user("Alice", "alice@example.com")

            assert result["name"] == "Alice"
        # All @lifecycle components disposed here

Test Isolation with Lifecycle
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Each test should get a fresh container to avoid state leakage.

.. code-block:: python

    # conftest.py
    import pytest
    from dioxide import Container, Profile

    @pytest.fixture
    async def container():
        """Fresh container with test fakes for each test."""
        c = Container()
        c.scan(profile=Profile.TEST)

        async with c:
            yield c
        # Cleanup happens automatically

    # Tests are isolated
    async def test_user_creation(container):
        service = container.resolve(UserService)
        # ...

    async def test_email_sending(container):
        service = container.resolve(UserService)
        # Fresh container, no state from previous test

Lifecycle in Fakes (Usually Not Needed)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Most fakes don't need lifecycle because they're simple in-memory structures.

.. code-block:: python

    from typing import Protocol
    from dioxide import adapter, lifecycle, Profile

    class UserRepository(Protocol):
        async def find_by_id(self, user_id: int) -> dict | None: ...
        async def create(self, name: str, email: str) -> dict: ...

    # ❌ Usually overkill - fakes don't need lifecycle
    @adapter.for_(UserRepository, profile=Profile.TEST)
    @lifecycle
    class FakeUserRepository:
        async def initialize(self) -> None:
            self.users = {}  # Just initialize in __init__ instead

        async def dispose(self) -> None:
            self.users.clear()  # Not needed, GC will handle it

    # ✅ Better - simple fake without lifecycle
    @adapter.for_(UserRepository, profile=Profile.TEST)
    class FakeUserRepository:
        def __init__(self):
            self.users = {}

        def clear(self):
            """Test helper to clear state between tests."""
            self.users = {}

**Use lifecycle in fakes only when**:

- Fake needs actual resources (temp files, connections)
- Fake needs cleanup for test isolation

----

Complete Testing Example
------------------------

Here's a complete example showing dioxide testing philosophy in practice. Due to length, this section would contain the full example from the markdown version, showing:

- Domain Layer (ports and services)
- Adapter Layer (production implementations)
- Adapter Layer (test fakes)
- Test Suite with comprehensive examples

(The full example code is available in the complete guide.)

----

Common Patterns
---------------

Catalog of common testing patterns with dioxide.

Pattern 1: Reset Pattern
~~~~~~~~~~~~~~~~~~~~~~~~~

Clear fake state between tests for isolation.

.. code-block:: python

    # conftest.py
    import pytest

    @pytest.fixture
    def fake_email(container):
        adapter = container.resolve(EmailPort)
        yield adapter
        adapter.clear()  # Reset after each test

    # Or use fresh container per test
    @pytest.fixture
    def container():
        c = Container()
        c.scan(profile=Profile.TEST)
        return c  # Fresh container = fresh fakes

Pattern 2: Verification Pattern
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Check fake calls in natural, readable way.

.. code-block:: python

    async def test_sends_email(fake_email, service):
        await service.register_user("Alice", "alice@example.com")

        # Natural verification
        assert len(fake_email.sent_emails) == 1
        assert fake_email.sent_emails[0]["to"] == "alice@example.com"

        # Or with helper
        assert fake_email.verify_sent_to("alice@example.com")

Pattern 3: Fixture Pattern
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use pytest fixtures for clean test setup.

.. code-block:: python

    # conftest.py
    @pytest.fixture
    def alice_user(fake_users):
        """Seed a test user named Alice."""
        fake_users.seed({
            "id": 1,
            "name": "Alice",
            "email": "alice@example.com",
        })
        return 1  # Return user ID

    # Test uses fixture
    async def test_sends_to_alice(alice_user, service, fake_email):
        await service.send_welcome_email(alice_user)
        assert fake_email.sent_emails[0]["to"] == "alice@example.com"

Pattern 4: Async Pattern
~~~~~~~~~~~~~~~~~~~~~~~~~

Testing async code is straightforward with pytest-asyncio.

.. code-block:: python

    # Install: pip install pytest-asyncio
    # pyproject.toml:
    # [tool.pytest.ini_options]
    # asyncio_mode = "auto"

    # Tests can be async
    async def test_async_operation(container):
        service = container.resolve(AsyncService)
        result = await service.do_something()
        assert result is not None

Pattern 5: Parametrization Pattern
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test multiple scenarios without duplication.

.. code-block:: python

    import pytest

    @pytest.mark.parametrize("days_elapsed,should_send", [
        (0, True),   # Never sent before
        (14, False), # Too soon (14 days)
        (29, False), # Still too soon (29 days)
        (30, True),  # Exactly 30 days
        (35, True),  # More than 30 days
    ])
    async def test_throttling(
        days_elapsed,
        should_send,
        notification_service,
        fake_users,
        fake_clock,
    ):
        # Arrange
        fake_users.seed({
            "id": 1,
            "email": "alice@example.com",
            "last_welcome_sent": datetime(2024, 1, 1, tzinfo=UTC) if days_elapsed > 0 else None,
        })
        fake_clock.set_time(datetime(2024, 1, 1 + days_elapsed, tzinfo=UTC))

        # Act
        result = await notification_service.send_welcome_email(1)

        # Assert
        assert result == should_send

Pattern 6: Error Injection Pattern
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test error handling with configurable fakes.

.. code-block:: python

    # Fake with error injection
    class FakePaymentGateway:
        def __init__(self):
            self.should_fail = False

        async def charge(self, amount: float) -> dict:
            if self.should_fail:
                raise PaymentError("Card declined")
            return {"status": "succeeded"}

    # Test error handling
    async def test_handles_payment_failure(fake_gateway, service):
        fake_gateway.should_fail = True

        with pytest.raises(PaymentError):
            await service.checkout(amount=100.0)

----

Common Pitfalls
---------------

Things to avoid when testing with dioxide.

Pitfall 1: Fakes That Are Too Complex
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Problem**: Fake becomes harder to understand than real implementation.

.. code-block:: python

    # ❌ BAD: Fake is too complex
    class FakeUserRepository:
        def __init__(self):
            self.users = {}
            self.transaction_log = []
            self.locks = {}

        async def create(self, name: str, email: str) -> dict:
            # Complex transaction simulation
            lock_id = self._acquire_lock()
            try:
                if email in [u["email"] for u in self.users.values()]:
                    raise DuplicateEmailError()
                # ... 50 lines of complex logic
            finally:
                self._release_lock(lock_id)

    # ✅ GOOD: Fake is simple
    class FakeUserRepository:
        def __init__(self):
            self.users = {}

        async def create(self, name: str, email: str) -> dict:
            user = {"id": len(self.users) + 1, "name": name, "email": email}
            self.users[user["id"]] = user
            return user

**Solution**: Keep fakes simple. If you need to test complex behavior (transactions, locks), write integration tests with real implementation.

Pitfall 2: Not Resetting Fakes Between Tests
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Problem**: State leaks between tests cause flaky failures.

.. code-block:: python

    # ❌ BAD: Tests affect each other
    async def test_first(fake_email, service):
        await service.register("alice@example.com")
        assert len(fake_email.sent_emails) == 1

    async def test_second(fake_email, service):
        # FAILS! sent_emails still has 1 email from previous test
        assert len(fake_email.sent_emails) == 0  # Flaky!

    # ✅ GOOD: Reset between tests
    @pytest.fixture
    def fake_email(container):
        adapter = container.resolve(EmailPort)
        yield adapter
        adapter.clear()  # Clean state

    # Or use fresh container
    @pytest.fixture
    def container():
        c = Container()
        c.scan(profile=Profile.TEST)
        return c  # Fresh container = isolated tests

**Solution**: Either reset fakes explicitly or use fresh container per test.

Pitfall 3: Using Fakes for Pure Functions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Problem**: Faking things that don't need faking.

.. code-block:: python

    # ❌ BAD: Unnecessary fake
    def calculate_discount(price: float, percent: float) -> float:
        return price * (percent / 100)

    # Don't fake this! It's a pure function
    class FakeDiscountCalculator:
        def calculate(self, price: float, percent: float) -> float:
            return price * (percent / 100)

    # ✅ GOOD: Test directly
    def test_discount():
        result = calculate_discount(100.0, 10.0)
        assert result == 10.0

**Solution**: Only fake at architectural boundaries (ports). Pure functions don't need fakes.

Pitfall 4: Adding Business Logic to Fakes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Problem**: Fakes become a second implementation to maintain.

.. code-block:: python

    # ❌ BAD: Fake has business logic
    class FakeUserRepository:
        async def create(self, name: str, email: str) -> dict:
            # Business rule duplicated in fake!
            if len(name) < 3:
                raise ValidationError("Name too short")
            # ...

    # ✅ GOOD: Fake is dumb, validation is in service
    @service
    class UserService:
        def __init__(self, repo: UserRepository):
            self.repo = repo

        async def register(self, name: str, email: str):
            # Business rule in service
            if len(name) < 3:
                raise ValidationError("Name too short")
            return await self.repo.create(name, email)

    class FakeUserRepository:
        async def create(self, name: str, email: str) -> dict:
            # Dumb storage
            user = {"id": 1, "name": name, "email": email}
            self.users[1] = user
            return user

**Solution**: Keep business logic in services, not fakes. Fakes should be dumb storage/transport.

Pitfall 5: Mixing Fakes and Mocks
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Problem**: Inconsistent testing strategy.

.. code-block:: python

    # ❌ BAD: Mixing fakes and mocks
    async def test_mixed(container):
        # Use dioxide fake for email
        service = container.resolve(UserService)

        # But use mock for database (inconsistent!)
        with patch('app.database.save') as mock_save:
            await service.register("Alice", "alice@example.com")
            mock_save.assert_called_once()

    # ✅ GOOD: Consistent - all fakes
    async def test_consistent(container):
        service = container.resolve(UserService)
        fake_users = container.resolve(UserRepository)
        fake_email = container.resolve(EmailPort)

        await service.register("Alice", "alice@example.com")

        assert len(fake_users.users) == 1
        assert len(fake_email.sent_emails) == 1

**Solution**: Be consistent. Either use fakes everywhere or mocks everywhere (prefer fakes).

----

FAQ
---

When should I use fakes vs real implementations?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Use fakes for**:

- Unit tests (fast, isolated)
- Development environment (no real services needed)
- Demos and documentation
- CI/CD (fast pipeline)

**Use real implementations for**:

- Integration tests (verify real behavior)
- Staging environment (realistic testing)
- Production (obviously)

**Rule of thumb**: Use fakes unless you specifically need to test integration with real services.

How do I test error cases with fakes?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Make fakes configurable to fail:

.. code-block:: python

    class FakeEmailAdapter:
        def __init__(self):
            self.should_fail = False
            self.failure_reason = "Network error"

        async def send(self, to: str, subject: str, body: str) -> None:
            if self.should_fail:
                raise EmailError(self.failure_reason)
            # ... normal behavior

    # In test
    async def test_handles_email_failure(fake_email, service):
        fake_email.should_fail = True
        fake_email.failure_reason = "SMTP timeout"

        with pytest.raises(EmailError):
            await service.register("alice@example.com")

Can I use fakes with existing test frameworks?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Yes! dioxide fakes work with any testing framework:

.. code-block:: python

    # pytest
    async def test_with_pytest(container):
        service = container.resolve(UserService)
        # ...

    # unittest
    class TestUserService(unittest.TestCase):
        def setUp(self):
            self.container = Container()
            self.container.scan(profile=Profile.TEST)

        async def test_registration(self):
            service = self.container.resolve(UserService)
            # ...

    # Robot Framework, behave, etc.
    # Just create container with TEST profile and use it

What about stubbing third-party APIs?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For third-party APIs that you don't control, create a port and two adapters:

.. code-block:: python

    from typing import Protocol
    from dioxide import adapter, Profile
    import httpx

    # Port (your interface)
    class WeatherPort(Protocol):
        async def get_temperature(self, city: str) -> float: ...

    # Production adapter (calls real API)
    @adapter.for_(WeatherPort, profile=Profile.PRODUCTION)
    class OpenWeatherAdapter:
        async def get_temperature(self, city: str) -> float:
            # Real API call
            response = await httpx.get(f"https://api.openweather.org/...")
            return response.json()["temperature"]

    # Test fake (returns predictable data)
    @adapter.for_(WeatherPort, profile=Profile.TEST)
    class FakeWeatherAdapter:
        def __init__(self):
            self.temperatures = {"Seattle": 15.5, "Miami": 28.0}

        async def get_temperature(self, city: str) -> float:
            return self.temperatures.get(city, 20.0)

Should fakes implement all protocol methods?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Yes! Fakes should implement the complete protocol. This ensures:

1. Type checkers validate the fake
2. Tests exercise the full interface
3. Changes to protocol affect fakes (you'll know)

.. code-block:: python

    # Port
    class UserRepository(Protocol):
        async def find_by_id(self, user_id: int) -> dict | None: ...
        async def create(self, name: str, email: str) -> dict: ...
        async def update(self, user: dict) -> None: ...
        async def delete(self, user_id: int) -> None: ...

    # Fake MUST implement all methods
    class FakeUserRepository:
        async def find_by_id(self, user_id: int) -> dict | None:
            # ...

        async def create(self, name: str, email: str) -> dict:
            # ...

        async def update(self, user: dict) -> None:
            # ...

        async def delete(self, user_id: int) -> None:
            # ...

If some methods aren't needed in tests yet, implement them as no-ops:

.. code-block:: python

    async def delete(self, user_id: int) -> None:
        # Not used in tests yet, but required by protocol
        self.users.pop(user_id, None)

How do I handle fakes that need cleanup?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use test fixtures with cleanup:

.. code-block:: python

    import tempfile
    import shutil
    import pytest
    from dioxide import Container

    # Fake that creates temp files
    class FakeFileStorage:
        def __init__(self):
            self.temp_dir = tempfile.mkdtemp()

        def cleanup(self):
            shutil.rmtree(self.temp_dir)

    # Fixture with cleanup
    @pytest.fixture
    def fake_storage(container: Container):
        storage = container.resolve(FileStorage)
        yield storage
        storage.cleanup()

Or use lifecycle (``@lifecycle``) if the fake needs async cleanup:

.. code-block:: python

    import tempfile
    import shutil
    from dioxide import adapter, lifecycle, Profile

    @adapter.for_(FileStorage, profile=Profile.TEST)
    @lifecycle
    class FakeFileStorage:
        async def initialize(self) -> None:
            self.temp_dir = tempfile.mkdtemp()

        async def dispose(self) -> None:
            shutil.rmtree(self.temp_dir)

When should I use mocks instead of fakes?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Very rarely. Consider mocks only when:

1. You're testing a third-party library you don't control
2. You need to verify specific method calls (use sparingly)
3. Creating a fake is genuinely more complex than a mock

**In most cases, a simple fake is better than a mock.**

How do I test code that depends on the current time?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use a fake clock:

.. code-block:: python

    from datetime import datetime, timedelta, UTC
    from typing import Protocol
    from dioxide import adapter, Profile

    # Port
    class Clock(Protocol):
        def now(self) -> datetime: ...

    # Fake
    @adapter.for_(Clock, profile=Profile.TEST)
    class FakeClock:
        def __init__(self):
            self._now = datetime(2024, 1, 1, tzinfo=UTC)

        def now(self) -> datetime:
            return self._now

        def set_time(self, dt: datetime) -> None:
            self._now = dt

        def advance(self, **kwargs) -> None:
            self._now += timedelta(**kwargs)

    # Test
    async def test_time_dependent(fake_clock, service):
        fake_clock.set_time(datetime(2024, 1, 1, tzinfo=UTC))
        # ... test at specific time

        fake_clock.advance(days=30)
        # ... test 30 days later

This eliminates flaky tests from time-dependent logic.

----

References
----------

dioxide Documentation
~~~~~~~~~~~~~~~~~~~~~

- :doc:`../MLP_VISION` - Canonical design philosophy
- :doc:`../README` - Quick start and API overview
- :doc:`../ROADMAP` - Development timeline

External Resources
~~~~~~~~~~~~~~~~~~

- `Martin Fowler: Mocks Aren't Stubs <https://martinfowler.com/articles/mocksArentStubs.html>`_
- `Test Doubles (Meszaros) <http://xunitpatterns.com/Test%20Double.html>`_
- `Hexagonal Architecture <https://alistair.cockburn.us/hexagonal-architecture/>`_

----

**This guide represents dioxide's core testing philosophy. When in doubt, prefer simple fakes over complex mocks.**
