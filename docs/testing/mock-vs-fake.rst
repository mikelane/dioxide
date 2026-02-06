Mock vs Fake: A Practical Comparison
=====================================

You've heard dioxide recommends "fakes over mocks." Maybe that sounds like religious
dogma. This page makes the case with code: same scenarios tested both ways, so you
can judge for yourself.

.. contents:: On this page
   :local:
   :depth: 2

----

The Setup: A Notification Service
----------------------------------

Every example on this page tests the same service. It sends a welcome email when a
user registers, with a 30-day throttle to avoid spamming.

.. code-block:: python

   # domain/ports.py
   from typing import Protocol
   from datetime import datetime

   class UserRepository(Protocol):
       def find_by_id(self, user_id: int) -> dict | None: ...
       def save(self, user: dict) -> None: ...

   class EmailPort(Protocol):
       def send(self, to: str, subject: str, body: str) -> None: ...

   class Clock(Protocol):
       def now(self) -> datetime: ...

.. code-block:: python

   # domain/services.py
   from datetime import timedelta

   class WelcomeService:
       def __init__(
           self,
           users: UserRepository,
           email: EmailPort,
           clock: Clock,
       ):
           self.users = users
           self.email = email
           self.clock = clock

       def send_welcome(self, user_id: int) -> bool:
           user = self.users.find_by_id(user_id)
           if not user:
               return False

           if user.get("last_welcome_sent"):
               elapsed = self.clock.now() - user["last_welcome_sent"]
               if elapsed < timedelta(days=30):
                   return False

           self.email.send(
               to=user["email"],
               subject="Welcome!",
               body=f"Hello {user['name']}, thanks for joining!",
           )

           user["last_welcome_sent"] = self.clock.now()
           self.users.save(user)
           return True

Now let's test it both ways.

----

Problem 1: Mocks Test Wiring, Not Behavior
--------------------------------------------

**With unittest.mock**

.. code-block:: python

   from unittest.mock import Mock

   def test_send_welcome_with_mock():
       mock_users = Mock()
       mock_email = Mock()
       mock_clock = Mock()

       mock_users.find_by_id.return_value = {
           "id": 1,
           "name": "Alice",
           "email": "alice@example.com",
           "last_welcome_sent": None,
       }
       mock_clock.now.return_value = datetime(2024, 6, 1, tzinfo=UTC)

       service = WelcomeService(mock_users, mock_email, mock_clock)
       result = service.send_welcome(1)

       assert result is True
       mock_email.send.assert_called_once_with(
           to="alice@example.com",
           subject="Welcome!",
           body="Hello Alice, thanks for joining!",
       )
       mock_users.save.assert_called_once()

This test passes. But what is it actually proving? It verifies that the service *calls*
``email.send`` with the right arguments. It verifies that ``users.save`` is *called*.
It does not verify that the user record is actually updated, or that the email body
makes sense, or that the throttle window is correctly calculated. The mock lets any
return value through, and the assertions check wiring, not outcomes.

**With dioxide fakes**

.. code-block:: python

   from datetime import datetime, UTC
   from dioxide import Container, Profile, adapter

   @adapter.for_(UserRepository, profile=Profile.TEST)
   class FakeUserRepository:
       def __init__(self):
           self.users: dict[int, dict] = {}

       def find_by_id(self, user_id: int) -> dict | None:
           return self.users.get(user_id)

       def save(self, user: dict) -> None:
           self.users[user["id"]] = user

       def seed(self, *users: dict) -> None:
           for u in users:
               self.users[u["id"]] = u

   @adapter.for_(EmailPort, profile=Profile.TEST)
   class FakeEmailAdapter:
       def __init__(self):
           self.sent_emails: list[dict] = []

       def send(self, to: str, subject: str, body: str) -> None:
           self.sent_emails.append({"to": to, "subject": subject, "body": body})

   @adapter.for_(Clock, profile=Profile.TEST)
   class FakeClock:
       def __init__(self):
           self._now = datetime(2024, 1, 1, tzinfo=UTC)

       def now(self) -> datetime:
           return self._now

       def set_time(self, dt: datetime) -> None:
           self._now = dt

       def advance(self, **kwargs) -> None:
           from datetime import timedelta
           self._now += timedelta(**kwargs)

.. code-block:: python

   def test_send_welcome_with_fakes():
       container = Container(profile=Profile.TEST)

       users = container.resolve(UserRepository)
       email = container.resolve(EmailPort)
       clock = container.resolve(Clock)

       users.seed({
           "id": 1,
           "name": "Alice",
           "email": "alice@example.com",
           "last_welcome_sent": None,
       })
       clock.set_time(datetime(2024, 6, 1, tzinfo=UTC))

       service = container.resolve(WelcomeService)
       result = service.send_welcome(1)

       assert result is True
       assert len(email.sent_emails) == 1
       assert email.sent_emails[0]["to"] == "alice@example.com"
       assert "Alice" in email.sent_emails[0]["body"]

       updated_user = users.find_by_id(1)
       assert updated_user["last_welcome_sent"] == datetime(2024, 6, 1, tzinfo=UTC)

The fake test checks *outcomes*: an email appeared in the outbox, the user record was
updated with a timestamp. The business logic actually ran. If the service has a bug
(wrong email address, wrong timestamp), this test catches it. The mock test would not.

----

Problem 2: Mocks Lie When Implementations Change
--------------------------------------------------

Suppose ``UserRepository.save`` starts raising ``ValueError`` when the email field
is missing. Here is what happens to each test:

**Mock test: still passes (wrong)**

.. code-block:: python

   # The real save() now validates:
   # def save(self, user: dict) -> None:
   #     if "email" not in user:
   #         raise ValueError("email required")

   def test_send_welcome_with_mock():
       mock_users = Mock()
       # ... same setup as before ...

       # mock_users.save never validates anything.
       # This test passes, but real code would raise ValueError
       # if the service accidentally dropped the email key.
       result = service.send_welcome(1)
       assert result is True  # Green. False confidence.

**Fake test: catches the problem**

.. code-block:: python

   @adapter.for_(UserRepository, profile=Profile.TEST)
   class FakeUserRepository:
       def save(self, user: dict) -> None:
           if "email" not in user:
               raise ValueError("email required")
           self.users[user["id"]] = user

Since the fake is a real implementation of the port's contract, it can enforce
the same invariants. If the service accidentally strips the email key during a
refactor, the fake test fails immediately. The mock test stays green and the bug
ships to production.

This is the core argument: **fakes behave like real implementations, so they catch
real bugs. Mocks behave like puppets, so they only catch what you script.**

----

Problem 3: Refactoring Breaks Mock Tests But Not Fake Tests
-------------------------------------------------------------

Consider a routine refactor: renaming the internal ``send`` call to use a
``_dispatch_email`` helper method.

**Before refactor:**

.. code-block:: python

   class WelcomeService:
       def send_welcome(self, user_id: int) -> bool:
           # ...
           self.email.send(to=user["email"], subject="Welcome!", body=body)
           return True

**After refactor (same behavior, different structure):**

.. code-block:: python

   class WelcomeService:
       def send_welcome(self, user_id: int) -> bool:
           # ...
           self._dispatch_email(user)
           return True

       def _dispatch_email(self, user: dict) -> None:
           self.email.send(
               to=user["email"],
               subject="Welcome!",
               body=f"Hello {user['name']}, thanks for joining!",
           )

**Mock test: breaks**

.. code-block:: python

   # This assertion now fails even though behavior is identical
   mock_email.send.assert_called_once_with(
       to="alice@example.com",
       subject="Welcome!",
       body="Hello Alice, thanks for joining!",
   )
   # Why? Because Mock tracks call counts on the mock_email object.
   # The send *was* called (via _dispatch_email), but if your mock
   # setup was patching at the wrong level, it could miss it.

   # More commonly, tests that assert call ORDER break:
   # mock_users.find_by_id.assert_called_before(mock_email.send)
   # This couples to the service's internal sequencing.

**Fake test: passes unchanged**

The fake test asserts ``len(email.sent_emails) == 1`` -- it checks the observable
outcome. It does not care whether ``send`` was called directly, through a helper, or
via a strategy pattern. The behavior is the same, so the test stays green.

**This is why mocks are called "brittle."** They break when you change *how* code
works, not *what* it does. Fakes only break when behavior changes, which is exactly
when you want tests to break.

----

Performance: Mock Setup Overhead vs. In-Memory Fakes
-----------------------------------------------------

Mocks create proxy objects that intercept every attribute access and method call.
This is fast enough for small tests but adds up:

.. list-table::
   :header-rows: 1
   :widths: 40 30 30

   * - Operation
     - ``unittest.mock``
     - dioxide Fake
   * - Create test double
     - ``Mock()`` + configure return values
     - ``FakeUserRepository()``
   * - Method call overhead
     - Proxy interception + call recording
     - Direct Python method call
   * - Assertion style
     - ``assert_called_once_with(...)``
     - ``assert len(repo.users) == 1``
   * - Lines of setup per test
     - 5-15 (return values, side effects)
     - 2-5 (seed data)

The real cost is not runtime milliseconds. It is **cognitive overhead**. Mock tests
require you to mentally simulate what the mock will return and then verify the call
graph. Fake tests read like stories: seed data, call service, check results.

Consider this mock setup for testing retry logic:

.. code-block:: python

   # Mock: 8 lines of ceremony
   mock_email = Mock()
   mock_email.send.side_effect = [
       ConnectionError("timeout"),
       ConnectionError("timeout"),
       None,  # Third call succeeds
   ]

   service = WelcomeService(mock_users, mock_email, mock_clock)
   result = service.send_welcome(1)

   assert result is True
   assert mock_email.send.call_count == 3

Versus the fake equivalent:

.. code-block:: python

   # Fake: readable intent
   @adapter.for_(EmailPort, profile=Profile.TEST)
   class FakeEmailWithRetry:
       def __init__(self):
           self.sent_emails: list[dict] = []
           self.failures_remaining = 0

       def send(self, to: str, subject: str, body: str) -> None:
           if self.failures_remaining > 0:
               self.failures_remaining -= 1
               raise ConnectionError("timeout")
           self.sent_emails.append({"to": to, "subject": subject, "body": body})

   email = container.resolve(EmailPort)
   email.failures_remaining = 2

   service = container.resolve(WelcomeService)
   result = service.send_welcome(1)

   assert result is True
   assert len(email.sent_emails) == 1

Both work. The fake version names the concept (``failures_remaining``) and produces
a reusable component. The mock version uses ``side_effect`` arrays that must be read
carefully to understand.

----

Real-World Example: Profile-Based Testing with dioxide
-------------------------------------------------------

Here is a complete, working example showing how dioxide's profile system makes fakes
a first-class architectural concept, not a testing afterthought.

.. code-block:: python

   from typing import Protocol
   from datetime import datetime, timedelta, UTC
   from dioxide import adapter, service, Container, Profile

   # --- Ports ---

   class UserRepository(Protocol):
       def find_by_id(self, user_id: int) -> dict | None: ...
       def save(self, user: dict) -> None: ...

   class EmailPort(Protocol):
       def send(self, to: str, subject: str, body: str) -> None: ...

   class Clock(Protocol):
       def now(self) -> datetime: ...

   # --- Service (business logic) ---

   @service
   class WelcomeService:
       def __init__(self, users: UserRepository, email: EmailPort, clock: Clock):
           self.users = users
           self.email = email
           self.clock = clock

       def send_welcome(self, user_id: int) -> bool:
           user = self.users.find_by_id(user_id)
           if not user:
               return False

           if user.get("last_welcome_sent"):
               elapsed = self.clock.now() - user["last_welcome_sent"]
               if elapsed < timedelta(days=30):
                   return False

           self.email.send(
               to=user["email"],
               subject="Welcome!",
               body=f"Hello {user['name']}, thanks for joining!",
           )
           user["last_welcome_sent"] = self.clock.now()
           self.users.save(user)
           return True

   # --- Test Fakes (live in production code, activated by Profile.TEST) ---

   @adapter.for_(UserRepository, profile=Profile.TEST)
   class FakeUserRepository:
       def __init__(self):
           self.users: dict[int, dict] = {}

       def find_by_id(self, user_id: int) -> dict | None:
           return self.users.get(user_id)

       def save(self, user: dict) -> None:
           self.users[user["id"]] = user

       def seed(self, *users: dict) -> None:
           for u in users:
               self.users[u["id"]] = u

   @adapter.for_(EmailPort, profile=Profile.TEST)
   class FakeEmailAdapter:
       def __init__(self):
           self.sent_emails: list[dict] = []

       def send(self, to: str, subject: str, body: str) -> None:
           self.sent_emails.append({"to": to, "subject": subject, "body": body})

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

   # --- Tests ---
   import pytest

   @pytest.fixture
   def container():
       return Container(profile=Profile.TEST)

   @pytest.fixture
   def users(container):
       return container.resolve(UserRepository)

   @pytest.fixture
   def email(container):
       return container.resolve(EmailPort)

   @pytest.fixture
   def clock(container):
       return container.resolve(Clock)

   @pytest.fixture
   def welcome_service(container):
       return container.resolve(WelcomeService)

   class DescribeWelcomeService:
       def it_sends_welcome_email_to_new_user(self, welcome_service, users, email, clock):
           users.seed({"id": 1, "name": "Alice", "email": "alice@example.com", "last_welcome_sent": None})
           clock.set_time(datetime(2024, 6, 1, tzinfo=UTC))

           result = welcome_service.send_welcome(1)

           assert result is True
           assert len(email.sent_emails) == 1
           assert email.sent_emails[0]["to"] == "alice@example.com"

       def it_throttles_within_30_days(self, welcome_service, users, email, clock):
           clock.set_time(datetime(2024, 6, 15, tzinfo=UTC))
           users.seed({
               "id": 1,
               "name": "Alice",
               "email": "alice@example.com",
               "last_welcome_sent": datetime(2024, 6, 1, tzinfo=UTC),
           })

           result = welcome_service.send_welcome(1)

           assert result is False
           assert len(email.sent_emails) == 0

       def it_sends_again_after_30_days(self, welcome_service, users, email, clock):
           clock.set_time(datetime(2024, 7, 5, tzinfo=UTC))
           users.seed({
               "id": 1,
               "name": "Alice",
               "email": "alice@example.com",
               "last_welcome_sent": datetime(2024, 6, 1, tzinfo=UTC),
           })

           result = welcome_service.send_welcome(1)

           assert result is True
           assert len(email.sent_emails) == 1

       def it_returns_false_for_unknown_user(self, welcome_service, email):
           result = welcome_service.send_welcome(999)

           assert result is False
           assert len(email.sent_emails) == 0

       def it_records_the_send_timestamp(self, welcome_service, users, email, clock):
           clock.set_time(datetime(2024, 6, 1, 12, 0, 0, tzinfo=UTC))
           users.seed({"id": 1, "name": "Alice", "email": "alice@example.com", "last_welcome_sent": None})

           welcome_service.send_welcome(1)

           updated = users.find_by_id(1)
           assert updated["last_welcome_sent"] == datetime(2024, 6, 1, 12, 0, 0, tzinfo=UTC)

Notice what these tests look like: plain English descriptions, no mock ceremony,
assertions on *observable outcomes*. The fixtures resolve adapters from the container,
which means the exact same fakes work if you switch to a different test runner, use
them in development mode, or seed a demo environment.

----

Why Fakes Live in Production Code
-----------------------------------

This is the part that makes people uncomfortable. Here is the directory structure
dioxide recommends:

.. code-block:: text

   app/
   +-- domain/
   |   +-- services.py           # @service (business logic)
   +-- adapters/
   |   +-- production/
   |   |   +-- sendgrid.py       # @adapter.for_(EmailPort, profile=Profile.PRODUCTION)
   |   |   +-- postgres.py       # @adapter.for_(UserRepository, profile=Profile.PRODUCTION)
   |   +-- fakes/
   |       +-- fake_email.py     # @adapter.for_(EmailPort, profile=Profile.TEST)
   |       +-- fake_repo.py      # @adapter.for_(UserRepository, profile=Profile.TEST)
   +-- tests/
       +-- conftest.py           # pytest fixtures (NOT fake implementations)
       +-- test_welcome.py       # tests

Fakes are **alternative implementations of ports**, not test utilities. They belong
with the other adapter implementations because:

1. **They implement the same port contract.** ``FakeEmailAdapter`` satisfies
   ``EmailPort`` the same way ``SendGridAdapter`` does. Both are adapters.

2. **They are reusable beyond tests.** The same fakes power local development
   (``Profile.DEVELOPMENT``), sales demos, CI pipelines, and documentation examples.

3. **They evolve with the port.** When ``EmailPort`` gains a new method, the fake
   gets updated in the same PR. Test mocks buried in ``tests/`` tend to drift.

4. **They document the contract.** Reading ``FakeEmailAdapter`` tells you exactly
   what ``EmailPort`` expects. It is the simplest possible implementation.

Deployment Reality
~~~~~~~~~~~~~~~~~~

In production, fake code **exists in the codebase but is never executed**:

.. code-block:: python

   # Production startup
   container = Container(profile=Profile.PRODUCTION)

   # Only Profile.PRODUCTION adapters are scanned and instantiated.
   # FakeEmailAdapter (Profile.TEST) is never imported, never
   # instantiated, never called. It is inert code.

This is the same model as having multiple database drivers in your dependencies: the
PostgreSQL driver exists in your wheel even when you connect to MySQL. The code is
present; it is not active.

.. list-table:: Common Concerns
   :header-rows: 1
   :widths: 30 70

   * - Concern
     - Response
   * - "Bloats the production build"
     - A fake adapter is typically 10-30 lines. The code size impact is negligible
       compared to your dependencies.
   * - "Security risk"
     - Fakes contain no credentials and perform no real I/O. They are the
       *least* dangerous code in your application.
   * - "Confusing to new developers"
     - The directory structure (``adapters/production/``, ``adapters/fakes/``) makes
       the separation obvious. The ``profile=`` parameter labels each adapter.
   * - "Violates separation of concerns"
     - Ports-and-adapters *is* the separation. Fakes are adapters. They live where
       adapters live.

Alternative: Separate Package
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If your organization requires strict separation, you can extract fakes into a
separate package:

.. code-block:: text

   myapp/
   +-- adapters/
   |   +-- production/
   myapp-testing/
   +-- fakes/

dioxide supports any structure. The ``@adapter.for_()`` decorator works regardless
of where the file lives. The recommendation is about what works best for most teams,
not a hard requirement.

----

When to Use Which: A Decision Guide
-------------------------------------

.. list-table::
   :header-rows: 1
   :widths: 35 20 45

   * - Situation
     - Recommendation
     - Rationale
   * - Stateful boundary (database, cache, queue)
     - **Fake**
     - In-memory implementation tests real behavior and is reusable across tests,
       dev, and demos.
   * - External API you control (your microservice)
     - **Fake**
     - Wrap in a port, write a fake adapter. Survives refactoring.
   * - External API you don't control (Stripe, Twilio)
     - **Fake port**
     - Create a port that wraps the third-party SDK. Write a fake for the port.
       This insulates you from SDK changes too.
   * - Pure function (no side effects)
     - **Neither**
     - Call the function directly. No test doubles needed.
   * - Time-dependent logic
     - **Fake Clock**
     - Controllable, deterministic, no ``freezegun`` dependency.
   * - Verifying a function is called (logging, analytics)
     - **Fake with recording**
     - Capture calls in a list. Same pattern as ``FakeEmailAdapter.sent_emails``.
   * - Quick prototype or spike
     - **Mock (temporarily)**
     - Mocks are fine for throwaway code. Migrate to fakes when the code
       solidifies.
   * - Testing ``@patch`` target (module-level function)
     - **Mock**
     - If the function is not behind a port and cannot be easily wrapped,
       ``@patch`` is the pragmatic choice.

.. note::

   The goal is not "never use mocks." The goal is to **default to fakes at
   architectural boundaries** and reach for mocks only when a fake is
   genuinely impractical.

----

Summary: Side-by-Side Comparison
----------------------------------

.. list-table::
   :header-rows: 1
   :widths: 30 35 35

   * - Dimension
     - ``unittest.mock``
     - dioxide Fake
   * - **What it tests**
     - That methods were called with expected args
     - That the system produced the expected outcomes
   * - **When real impl changes**
     - Test still passes (false confidence)
     - Fake enforces contract (catches bugs)
   * - **After refactoring**
     - Tests break (coupled to call structure)
     - Tests pass (coupled to behavior)
   * - **Setup cost**
     - ``Mock()`` + return values + side effects
     - One-time fake class, reused everywhere
   * - **Readability**
     - ``assert_called_once_with(...)``
     - ``assert len(emails) == 1``
   * - **Reusability**
     - Per-test mock configuration
     - Shared across tests, dev, demos
   * - **Where it lives**
     - ``tests/`` (test-only)
     - ``adapters/`` (production code, profile-gated)
   * - **Maintained with port**
     - Often drifts out of sync
     - Updated in the same PR

----

Next Steps
----------

- :doc:`philosophy` -- The full testing philosophy behind fakes over mocks
- :doc:`patterns` -- Common fake patterns: in-memory repos, controllable clocks, error injection
- :doc:`fixtures` -- Container fixtures for pytest
- :doc:`/user_guide/hexagonal_architecture` -- Understanding ports and adapters

.. seealso::

   - `Martin Fowler: Mocks Aren't Stubs <https://martinfowler.com/articles/mocksArentStubs.html>`_ -- The classic reference on test double taxonomy
   - `Test Doubles (Meszaros) <http://xunitpatterns.com/Test%20Double.html>`_ -- Formal definitions of stubs, mocks, fakes, and spies
