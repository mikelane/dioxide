Writing Good Fakes
==================

This guide teaches you how to write effective fake adapters for testing with dioxide.
Whether you're writing your first fake or refining your approach, these patterns will
help you build fast, reliable, and maintainable test doubles.

.. contents:: On This Page
   :local:
   :depth: 2

----

Fake vs Mock: The Mental Model
------------------------------

Before diving into patterns, let's clarify what makes a fake different from a mock.

A **mock** is a generic stand-in configured to return specific values and record calls.
You tell it what to do:

.. code-block:: python

   # Mock: You configure behavior from outside
   mock_repo = Mock()
   mock_repo.find_by_id.return_value = {"id": 1, "name": "Alice"}

A **fake** is a real, working implementation that's simpler than the production version.
It has its own internal logic:

.. code-block:: python

   # Fake: It has real behavior, just simplified
   @adapter.for_(UserRepository, profile=Profile.TEST)
   class FakeUserRepository:
       def __init__(self):
           self.users: dict[int, dict] = {}

       async def find_by_id(self, user_id: int) -> dict | None:
           return self.users.get(user_id)

The key difference:

.. list-table::
   :header-rows: 1
   :widths: 15 40 40

   * - Aspect
     - Mock
     - Fake
   * - Behavior
     - Configured externally per test
     - Built-in, self-contained logic
   * - What you test
     - That your code calls the right methods
     - That your code produces the right outcomes
   * - Refactoring
     - Breaks tests (coupled to method names/order)
     - Tests survive (coupled to behavior only)
   * - Reuse
     - Reconfigured per test
     - Same fake works across all tests
   * - Complexity
     - Grows with ``side_effect`` chains
     - Stays simple (dict, list)

**When to use which:**

- **Default to fakes** for all architectural boundaries (repositories, email, HTTP clients,
  clocks, queues). Fakes test real behavior and survive refactoring.
- **Consider mocks** only when wrapping a third-party library you don't control and haven't
  abstracted behind a port. Even then, prefer introducing a port and writing a fake.

----

The Simple Fake: Start Here
----------------------------

Every fake follows the same structure:

1. Implement the port's protocol methods
2. Use simple in-memory state (dict, list)
3. Add test-only helper methods that are not in the port

Here's the simplest useful fake:

.. code-block:: python

   from typing import Protocol
   from dioxide import adapter, Profile

   # Port (the interface your domain depends on)
   class UserRepository(Protocol):
       async def find_by_id(self, user_id: int) -> dict | None: ...
       async def save(self, user: dict) -> None: ...

   # Fake (a real implementation, just in-memory)
   @adapter.for_(UserRepository, profile=Profile.TEST)
   class FakeUserRepository:
       def __init__(self):
           self.users: dict[int, dict] = {}

       async def find_by_id(self, user_id: int) -> dict | None:
           return self.users.get(user_id)

       async def save(self, user: dict) -> None:
           self.users[user["id"]] = user

       # Test-only helper (NOT in the protocol)
       def seed(self, *users: dict) -> None:
           for user in users:
               self.users[user["id"]] = user

That's it. No frameworks. No configuration. Just a class with a dict.

----

Pattern: In-Memory Repository
------------------------------

The most common fake replaces a database repository with a dictionary.

.. code-block:: python

   from typing import Protocol
   from dioxide import adapter, Profile

   class UserRepository(Protocol):
       async def find_by_id(self, user_id: int) -> dict | None: ...
       async def create(self, name: str, email: str) -> dict: ...
       async def update(self, user: dict) -> None: ...
       async def delete(self, user_id: int) -> None: ...
       async def find_by_email(self, email: str) -> dict | None: ...

   @adapter.for_(UserRepository, profile=Profile.TEST)
   class FakeUserRepository:
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

       async def find_by_email(self, email: str) -> dict | None:
           for user in self.users.values():
               if user["email"] == email:
                   return user
           return None

       # Test-only helpers
       def seed(self, *users: dict) -> None:
           """Pre-populate with test data."""
           for user in users:
               self.users[user["id"]] = user
               if user["id"] >= self._next_id:
                   self._next_id = user["id"] + 1

**When to use**: Any port that wraps persistent storage (databases, file systems, key-value
stores, caches).

**Usage in tests**:

.. code-block:: python

   async def test_finds_user_by_email(container):
       repo = container.resolve(UserRepository)
       repo.seed(
           {"id": 1, "name": "Alice", "email": "alice@example.com"},
           {"id": 2, "name": "Bob", "email": "bob@example.com"},
       )

       service = container.resolve(UserService)
       result = await service.lookup("alice@example.com")

       assert result["name"] == "Alice"

**Design notes**:

- Use ``seed()`` for test data setup instead of calling ``create()`` repeatedly.
  ``seed()`` gives you direct control over IDs and fields.
- Keep ``find_by_email()`` as a linear scan. It's fast enough for tests (you'll
  have at most a handful of entries). Don't add indexes.
- Auto-increment ``_next_id`` so ``create()`` works without specifying IDs.

----

Pattern: Controllable Clock
----------------------------

Replace ``datetime.now()`` with a port that your tests can control.

.. code-block:: python

   from datetime import datetime, timedelta, UTC
   from typing import Protocol
   from dioxide import adapter, Profile

   # Port
   class Clock(Protocol):
       def now(self) -> datetime: ...

   # Production adapter
   @adapter.for_(Clock, profile=Profile.PRODUCTION)
   class SystemClock:
       def now(self) -> datetime:
           return datetime.now(UTC)

   # Test fake
   @adapter.for_(Clock, profile=Profile.TEST)
   class FakeClock:
       def __init__(self):
           self._now = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)

       def now(self) -> datetime:
           return self._now

       # Test-only control methods
       def set_time(self, dt: datetime) -> None:
           self._now = dt

       def advance(self, **kwargs) -> None:
           self._now += timedelta(**kwargs)

**When to use**: Any code that depends on the current time -- throttling, expiration,
scheduling, audit timestamps.

**Usage in tests**:

.. code-block:: python

   async def test_token_expires_after_24_hours(container):
       clock = container.resolve(Clock)
       service = container.resolve(AuthService)

       clock.set_time(datetime(2024, 6, 15, 10, 0, 0, tzinfo=UTC))
       token = await service.create_token(user_id=1)
       assert await service.validate_token(token) is True

       clock.advance(hours=25)
       assert await service.validate_token(token) is False

**Design notes**:

- Always use timezone-aware datetimes (``tzinfo=UTC``).
- Start with a fixed, recognizable default (``2024-01-01T12:00:00Z``). This makes
  test output easy to read.
- ``advance()`` takes ``**kwargs`` passed to ``timedelta``, so you can write
  ``advance(hours=2, minutes=30)`` naturally.

----

Pattern: Fake HTTP Client
--------------------------

Replace real HTTP calls with a fake that records requests and returns stubbed responses.

.. code-block:: python

   from dataclasses import dataclass, field
   from typing import Protocol
   from dioxide import adapter, Profile

   @dataclass
   class HttpResponse:
       status_code: int = 200
       body: str = ""
       headers: dict = field(default_factory=dict)

   @dataclass
   class HttpRequest:
       method: str
       url: str
       body: str | None = None
       headers: dict = field(default_factory=dict)

   class HttpClient(Protocol):
       async def get(self, url: str, headers: dict | None = None) -> HttpResponse: ...
       async def post(self, url: str, body: str, headers: dict | None = None) -> HttpResponse: ...

   @adapter.for_(HttpClient, profile=Profile.TEST)
   class FakeHttpClient:
       def __init__(self):
           self.requests: list[HttpRequest] = []
           self.responses: dict[str, HttpResponse] = {}
           self.default_response = HttpResponse(status_code=404, body="Not Found")

       async def get(self, url: str, headers: dict | None = None) -> HttpResponse:
           self.requests.append(HttpRequest("GET", url, headers=headers or {}))
           return self.responses.get(url, self.default_response)

       async def post(self, url: str, body: str, headers: dict | None = None) -> HttpResponse:
           self.requests.append(HttpRequest("POST", url, body=body, headers=headers or {}))
           return self.responses.get(url, self.default_response)

       # Test-only helpers
       def stub_response(self, url: str, status_code: int = 200, body: str = "") -> None:
           self.responses[url] = HttpResponse(status_code=status_code, body=body)

       def last_request(self) -> HttpRequest | None:
           return self.requests[-1] if self.requests else None

**When to use**: Any port that wraps external API calls (REST APIs, webhooks, third-party
services).

**Usage in tests**:

.. code-block:: python

   async def test_fetches_weather_data(container):
       http = container.resolve(HttpClient)
       http.stub_response(
           "https://api.weather.com/v1/seattle",
           body='{"temperature": 15.5}',
       )

       service = container.resolve(WeatherService)
       temp = await service.get_temperature("seattle")

       assert temp == 15.5
       assert http.last_request().method == "GET"

----

Pattern: Event Collector
-------------------------

Capture events, messages, or notifications for assertion in tests.

.. code-block:: python

   from dataclasses import dataclass
   from typing import Protocol
   from dioxide import adapter, Profile

   @dataclass
   class Event:
       type: str
       payload: dict

   class EventBus(Protocol):
       async def publish(self, event_type: str, payload: dict) -> None: ...

   @adapter.for_(EventBus, profile=Profile.TEST)
   class FakeEventBus:
       def __init__(self):
           self.events: list[Event] = []

       async def publish(self, event_type: str, payload: dict) -> None:
           self.events.append(Event(type=event_type, payload=payload))

       # Test-only helpers
       def events_of_type(self, event_type: str) -> list[Event]:
           return [e for e in self.events if e.type == event_type]

       def has_event(self, event_type: str) -> bool:
           return any(e.type == event_type for e in self.events)

       def clear(self) -> None:
           self.events = []

**When to use**: Message queues, event buses, audit logs, notification systems -- any
port where the important behavior is "something was emitted."

**Usage in tests**:

.. code-block:: python

   async def test_publishes_user_created_event(container):
       bus = container.resolve(EventBus)
       service = container.resolve(UserService)

       await service.register("Alice", "alice@example.com")

       assert bus.has_event("user.created")
       event = bus.events_of_type("user.created")[0]
       assert event.payload["email"] == "alice@example.com"

----

Pattern: Configurable Responses
--------------------------------

Queue multiple responses for sequential calls. This is useful when testing retry
logic or paginated API calls.

.. code-block:: python

   from collections import deque
   from typing import Protocol
   from dioxide import adapter, Profile

   class PaymentGateway(Protocol):
       async def charge(self, amount: float, card: str) -> dict: ...

   class PaymentError(Exception):
       pass

   @adapter.for_(PaymentGateway, profile=Profile.TEST)
   class FakePaymentGateway:
       def __init__(self):
           self.charges: list[dict] = []
           self._responses: deque = deque()
           self._default_success = True

       async def charge(self, amount: float, card: str) -> dict:
           if self._responses:
               response = self._responses.popleft()
               if isinstance(response, Exception):
                   raise response

               self.charges.append(response)
               return response

           if not self._default_success:
               raise PaymentError("Card declined")

           result = {
               "id": f"ch_{len(self.charges) + 1}",
               "amount": amount,
               "card": card,
               "status": "succeeded",
           }
           self.charges.append(result)
           return result

       # Test-only helpers
       def enqueue_response(self, response: dict) -> None:
           """Queue a successful response for the next call."""
           self._responses.append(response)

       def enqueue_failure(self, reason: str = "Card declined") -> None:
           """Queue a failure for the next call."""
           self._responses.append(PaymentError(reason))

       def reset(self) -> None:
           self.charges = []
           self._responses.clear()
           self._default_success = True

**When to use**: Testing retry logic, paginated responses, or any scenario where
successive calls should return different results.

**Usage in tests**:

.. code-block:: python

   async def test_retries_payment_on_transient_failure(container):
       gateway = container.resolve(PaymentGateway)
       service = container.resolve(CheckoutService)

       # First attempt fails, retry succeeds
       gateway.enqueue_failure("Network timeout")
       gateway.enqueue_response({"id": "ch_1", "amount": 50.0, "status": "succeeded"})

       result = await service.checkout(amount=50.0, card="4242424242424242")

       assert result["status"] == "succeeded"
       assert len(gateway.charges) == 1  # Only successful charge recorded

----

Error Injection: Testing Failure Paths
----------------------------------------

Good tests cover failure paths. Make your fakes configurable to fail on demand.

The simplest approach uses a ``should_fail`` flag:

.. code-block:: python

   @adapter.for_(EmailPort, profile=Profile.TEST)
   class FakeEmailAdapter:
       def __init__(self):
           self.sent_emails: list[dict] = []
           self.should_fail = False
           self.failure_reason = "SMTP connection refused"

       async def send(self, to: str, subject: str, body: str) -> None:
           if self.should_fail:
               raise EmailError(self.failure_reason)
           self.sent_emails.append({"to": to, "subject": subject, "body": body})

       # Test-only helpers
       def fail_with(self, reason: str) -> None:
           self.should_fail = True
           self.failure_reason = reason

       def reset(self) -> None:
           self.sent_emails = []
           self.should_fail = False
           self.failure_reason = "SMTP connection refused"

**Usage in tests**:

.. code-block:: python

   async def test_handles_email_failure_gracefully(container):
       email = container.resolve(EmailPort)
       email.fail_with("SMTP server unavailable")

       service = container.resolve(RegistrationService)
       result = await service.register("alice@example.com")

       # Registration succeeds even when email fails
       assert result.user_created is True
       assert result.welcome_email_sent is False

**Use a fixture with cleanup** to prevent error state from leaking between tests:

.. code-block:: python

   @pytest.fixture
   def fake_email(container):
       email = container.resolve(EmailPort)
       yield email
       email.reset()

----

Test Helpers: Methods Not in the Port
--------------------------------------

The port (protocol) defines the contract your domain uses. Test helpers live on the
fake but are not part of the port. This is a feature, not a hack.

Common helper types:

.. list-table::
   :header-rows: 1
   :widths: 20 30 50

   * - Helper Type
     - Purpose
     - Examples
   * - ``seed()``
     - Pre-populate test data
     - ``repo.seed({"id": 1, "name": "Alice"})``
   * - ``verify_*()``
     - Readable assertions
     - ``email.verify_sent_to("alice@example.com")``
   * - ``clear()`` / ``reset()``
     - Clean state between tests
     - ``gateway.reset()``
   * - ``fail_with()``
     - Trigger error paths
     - ``email.fail_with("SMTP timeout")``
   * - ``set_time()`` / ``advance()``
     - Control time
     - ``clock.advance(days=30)``
   * - ``last_request()``
     - Inspect the most recent call
     - ``http.last_request().method``
   * - ``enqueue_*()``
     - Queue sequential responses
     - ``gateway.enqueue_failure("Timeout")``

**Accessing helpers in tests**: Resolve the port from the container, but type-hint
the fixture with the concrete fake type:

.. code-block:: python

   @pytest.fixture
   def fake_users(container) -> FakeUserRepository:
       return container.resolve(UserRepository)

   # Now your test has access to seed(), clear(), etc.
   async def test_user_lookup(fake_users, container):
       fake_users.seed({"id": 1, "name": "Alice", "email": "alice@example.com"})
       service = container.resolve(UserService)
       result = await service.find_user(1)
       assert result["name"] == "Alice"

----

Complete Example: Port to Test
-------------------------------

Here's the full lifecycle of a port, from definition through production adapter,
fake adapter, and test:

.. code-block:: python

   # --- Step 1: Define the port ---
   from typing import Protocol
   from datetime import datetime

   class AuditLog(Protocol):
       async def record(self, action: str, user_id: int, details: str) -> None: ...
       async def entries_for_user(self, user_id: int) -> list[dict]: ...

   # --- Step 2: Production adapter ---
   from dioxide import adapter, Profile

   @adapter.for_(AuditLog, profile=Profile.PRODUCTION)
   class PostgresAuditLog:
       def __init__(self, db: Database):
           self.db = db

       async def record(self, action: str, user_id: int, details: str) -> None:
           await self.db.execute(
               "INSERT INTO audit_log (action, user_id, details, timestamp) VALUES (?, ?, ?, ?)",
               action, user_id, details, datetime.now(),
           )

       async def entries_for_user(self, user_id: int) -> list[dict]:
           rows = await self.db.fetch_all(
               "SELECT * FROM audit_log WHERE user_id = ? ORDER BY timestamp", user_id
           )
           return [dict(row) for row in rows]

   # --- Step 3: Fake adapter ---
   @adapter.for_(AuditLog, profile=Profile.TEST)
   class FakeAuditLog:
       def __init__(self):
           self.entries: list[dict] = []

       async def record(self, action: str, user_id: int, details: str) -> None:
           self.entries.append({
               "action": action,
               "user_id": user_id,
               "details": details,
           })

       async def entries_for_user(self, user_id: int) -> list[dict]:
           return [e for e in self.entries if e["user_id"] == user_id]

       # Test helpers
       def has_entry(self, action: str, user_id: int) -> bool:
           return any(
               e["action"] == action and e["user_id"] == user_id
               for e in self.entries
           )

       def clear(self) -> None:
           self.entries = []

   # --- Step 4: Service (depends on the port, not the adapter) ---
   from dioxide import service

   @service
   class AccountService:
       def __init__(self, users: UserRepository, audit: AuditLog):
           self.users = users
           self.audit = audit

       async def delete_account(self, user_id: int) -> bool:
           user = await self.users.find_by_id(user_id)
           if not user:
               return False
           await self.users.delete(user_id)
           await self.audit.record("account_deleted", user_id, f"Deleted user {user['name']}")
           return True

   # --- Step 5: Test ---
   class DescribeAccountService:
       async def it_records_deletion_in_audit_log(self, container):
           users = container.resolve(UserRepository)
           audit = container.resolve(AuditLog)
           service = container.resolve(AccountService)

           users.seed({"id": 1, "name": "Alice", "email": "alice@example.com"})

           result = await service.delete_account(1)

           assert result is True
           assert audit.has_entry("account_deleted", user_id=1)

       async def it_does_not_audit_when_user_missing(self, container):
           audit = container.resolve(AuditLog)
           service = container.resolve(AccountService)

           result = await service.delete_account(999)

           assert result is False
           assert len(audit.entries) == 0

----

Anti-Patterns: Fakes That Are Too Smart
-----------------------------------------

A fake should be **simpler than the real implementation**. If your fake is getting
complex, something is wrong.

Fake with too much logic
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # BAD: Fake reimplements database constraints
   class FakeUserRepository:
       async def create(self, name: str, email: str) -> dict:
           # Simulating unique constraint
           for user in self.users.values():
               if user["email"] == email:
                   raise DuplicateEmailError(email)

           # Simulating transaction isolation
           with self._lock:
               if self._in_transaction:
                   self._pending.append(user)
               else:
                   self.users[user["id"]] = user

           return user

   # GOOD: Keep it simple
   class FakeUserRepository:
       async def create(self, name: str, email: str) -> dict:
           user = {"id": self._next_id, "name": name, "email": email}
           self.users[self._next_id] = user
           self._next_id += 1
           return user

If you need to test unique constraint behavior, that belongs in an integration test
with the real database, not in a fake.

Business logic in the fake
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # BAD: Validation belongs in the service, not the fake
   class FakeUserRepository:
       async def create(self, name: str, email: str) -> dict:
           if len(name) < 3:
               raise ValidationError("Name too short")
           if "@" not in email:
               raise ValidationError("Invalid email")
           # ...

   # GOOD: Fake stores data; service validates
   @service
   class UserService:
       async def register(self, name: str, email: str) -> dict:
           if len(name) < 3:
               raise ValidationError("Name too short")
           return await self.repo.create(name, email)

   class FakeUserRepository:
       async def create(self, name: str, email: str) -> dict:
           user = {"id": self._next_id, "name": name, "email": email}
           self.users[self._next_id] = user
           self._next_id += 1
           return user

State leakage between tests
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # BAD: Shared state across tests
   fake_repo = FakeUserRepository()  # Module-level = shared

   def test_first():
       fake_repo.seed({"id": 1, "name": "Alice"})
       # ...

   def test_second():
       # Alice is still in the repo from test_first!
       result = fake_repo.find_by_id(1)  # Returns Alice unexpectedly

   # GOOD: Fresh container per test via fixture
   @pytest.fixture
   def container():
       return Container(profile=Profile.TEST)  # Fresh instance = fresh fakes

----

Rules of Thumb
--------------

1. **Fakes should be simpler than the real implementation.** If your fake has more
   than ~20 lines of logic, reconsider the design.

2. **Fakes live in production code, not test directories.** Tag them with
   ``profile=Profile.TEST`` so they're never instantiated in production, but keep
   them alongside real adapters so they stay in sync.

3. **Fakes implement the full protocol.** Every method in the port should have a
   corresponding method in the fake. This way, type checkers catch drift between
   port and fake.

4. **Test helpers go on the fake, not in the protocol.** Methods like ``seed()``,
   ``clear()``, and ``verify_sent_to()`` are testing affordances, not domain
   contracts.

5. **Use ``Profile.TEST`` for all test fakes.** The profile system ensures fakes
   are only activated in test environments:

   .. code-block:: python

      container = Container(profile=Profile.TEST)  # Activates all test fakes
      container = Container(profile=Profile.PRODUCTION)  # Real adapters only

6. **Prefer fresh containers over manual cleanup.** A fresh ``Container`` per test
   gives you complete isolation with zero effort. Use ``reset()``/``clear()``
   methods only when container creation is expensive.

7. **Don't fake pure functions.** If code has no side effects and no external
   dependencies, test it directly:

   .. code-block:: python

      # No fake needed - just call it
      def test_calculates_discount():
          result = calculate_discount(100.0, 15.0)
          assert result == 15.0

----

Where Fakes Live in Your Project
----------------------------------

Organize fakes alongside real adapters in production code:

.. code-block:: text

   app/
     domain/
       ports.py                  # Protocol definitions (UserRepository, EmailPort, Clock)
       services.py               # Business logic (@service)

     adapters/
       postgres_users.py         # @adapter.for_(UserRepository, profile=Profile.PRODUCTION)
       sendgrid_email.py         # @adapter.for_(EmailPort, profile=Profile.PRODUCTION)
       system_clock.py           # @adapter.for_(Clock, profile=Profile.PRODUCTION)

       fake_users.py             # @adapter.for_(UserRepository, profile=Profile.TEST)
       fake_email.py             # @adapter.for_(EmailPort, profile=Profile.TEST)
       fake_clock.py             # @adapter.for_(Clock, profile=Profile.TEST)

   tests/
     conftest.py                 # Fixtures that resolve fakes from container
     test_user_service.py        # Tests using fakes

**Why in production code?**

- **Profile.PRODUCTION excludes fakes**: Fakes are never instantiated in production.
  The code exists in the codebase, but is never executed outside of tests.
- **Reusable across environments**: The same ``FakeUserRepository`` works for unit tests,
  dev environment, and demos.
- **Maintained alongside real adapters**: When ``UserRepository`` protocol changes, both
  ``PostgresUserRepository`` and ``FakeUserRepository`` need updating. Co-locating them
  makes drift visible.
- **Documents the port contract**: A fake is a readable specification of what the port
  expects.

.. seealso::

   - :doc:`philosophy` - The deeper "why" behind fakes over mocks
   - :doc:`patterns` - Additional testing patterns and recipes
   - :doc:`fixtures` - Container fixtures for pytest
   - :doc:`/TESTING_GUIDE` - Comprehensive testing guide
