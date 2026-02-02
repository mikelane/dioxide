Testing Patterns
================

This page catalogs common patterns for writing effective fakes and tests with dioxide.

Writing Effective Fakes
-----------------------

Fakes should be simple, fast, and deterministic. Here are patterns for writing
effective fakes.

Simple In-Memory Fakes
~~~~~~~~~~~~~~~~~~~~~~

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
~~~~~~~~~~~~~~~~~~~~~~~

For services that produce side effects (email, logging, events), capture calls
for verification.

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

Fakes with Error Injection
~~~~~~~~~~~~~~~~~~~~~~~~~~

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

----

Common Test Patterns
--------------------

Pattern 1: Reset Pattern
~~~~~~~~~~~~~~~~~~~~~~~~

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
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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
~~~~~~~~~~~~~~~~~~~~~~~~~~

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
~~~~~~~~~~~~~~~~~~~~~~~~

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
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test multiple scenarios without duplication.

.. code-block:: python

   import pytest
   from datetime import datetime, UTC

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
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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

Guidelines for Writing Fakes
----------------------------

**DO**:

- Keep fakes simple (less logic than real implementation)
- Make fakes fast (in-memory, no I/O)
- Make fakes deterministic (no random behavior, controllable time)
- Add test-only helpers (``seed()``, ``verify_*()``, ``clear()``)
- Implement the full protocol (all methods)
- Put fakes in production code (reusable)

**DON'T**:

- Make fakes complex (defeats the purpose)
- Add business logic to fakes (keep them dumb)
- Make fakes stateful across tests (use ``clear()`` or fresh container)
- Use fakes for code that doesn't need them (pure functions don't need fakes)

.. seealso::

   - :doc:`philosophy` - Why fakes over mocks
   - :doc:`fixtures` - Container fixtures for pytest
   - :doc:`troubleshooting` - Common pitfalls and solutions
