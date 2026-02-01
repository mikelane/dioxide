Troubleshooting
===============

Common pitfalls and solutions when testing with dioxide.

Common Pitfalls
---------------

Pitfall 1: Fakes That Are Too Complex
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Problem**: Fake becomes harder to understand than real implementation.

.. code-block:: python

   # BAD: Fake is too complex
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

   # GOOD: Fake is simple
   class FakeUserRepository:
       def __init__(self):
           self.users = {}

       async def create(self, name: str, email: str) -> dict:
           user = {"id": len(self.users) + 1, "name": name, "email": email}
           self.users[user["id"]] = user
           return user

**Solution**: Keep fakes simple. If you need to test complex behavior (transactions,
locks), write integration tests with real implementation.

Pitfall 2: Not Resetting Fakes Between Tests
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Problem**: State leaks between tests cause flaky failures.

.. code-block:: python

   # BAD: Tests affect each other
   async def test_first(fake_email, service):
       await service.register("alice@example.com")
       assert len(fake_email.sent_emails) == 1

   async def test_second(fake_email, service):
       # FAILS! sent_emails still has 1 email from previous test
       assert len(fake_email.sent_emails) == 0  # Flaky!

   # GOOD: Reset between tests
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
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Problem**: Faking things that don't need faking.

.. code-block:: python

   # BAD: Unnecessary fake
   def calculate_discount(price: float, percent: float) -> float:
       return price * (percent / 100)

   # Don't fake this! It's a pure function
   class FakeDiscountCalculator:
       def calculate(self, price: float, percent: float) -> float:
           return price * (percent / 100)

   # GOOD: Test directly
   def test_discount():
       result = calculate_discount(100.0, 10.0)
       assert result == 10.0

**Solution**: Only fake at architectural boundaries (ports). Pure functions don't
need fakes.

Pitfall 4: Adding Business Logic to Fakes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Problem**: Fakes become a second implementation to maintain.

.. code-block:: python

   # BAD: Fake has business logic
   class FakeUserRepository:
       async def create(self, name: str, email: str) -> dict:
           # Business rule duplicated in fake!
           if len(name) < 3:
               raise ValidationError("Name too short")
           # ...

   # GOOD: Fake is dumb, validation is in service
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

**Solution**: Keep business logic in services, not fakes. Fakes should be dumb
storage/transport.

Pitfall 5: Mixing Fakes and Mocks
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Problem**: Inconsistent testing strategy.

.. code-block:: python

   # BAD: Mixing fakes and mocks
   async def test_mixed(container):
       # Use dioxide fake for email
       service = container.resolve(UserService)

       # But use mock for database (inconsistent!)
       with patch('app.database.save') as mock_save:
           await service.register("Alice", "alice@example.com")
           mock_save.assert_called_once()

   # GOOD: Consistent - all fakes
   async def test_consistent(container):
       service = container.resolve(UserService)
       fake_users = container.resolve(UserRepository)
       fake_email = container.resolve(EmailPort)

       await service.register("Alice", "alice@example.com")

       assert len(fake_users.users) == 1
       assert len(fake_email.sent_emails) == 1

**Solution**: Be consistent. Either use fakes everywhere or mocks everywhere
(prefer fakes).

----

Frequently Asked Questions
--------------------------

When should I use fakes vs real implementations?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Use fakes for**:

- Unit tests (fast, isolated)
- Development environment (no real services needed)
- Demos and documentation
- CI/CD (fast pipeline)

**Use real implementations for**:

- Integration tests (verify real behavior)
- Staging environment (realistic testing)
- Production (obviously)

**Rule of thumb**: Use fakes unless you specifically need to test integration with
real services.

How do I test error cases with fakes?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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

How do I test code that depends on the current time?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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

Error Messages
--------------

Missing Adapter for Port
~~~~~~~~~~~~~~~~~~~~~~~~

**Error**: ``NoAdapterError: No adapter registered for port 'EmailPort' in profile 'test'``

**Cause**: No adapter is registered for the port in the active profile.

**Solution**: Create an adapter for the port with the correct profile:

.. code-block:: python

   @adapter.for_(EmailPort, profile=Profile.TEST)
   class FakeEmailAdapter:
       async def send(self, to: str, subject: str, body: str) -> None:
           self.sent_emails.append({"to": to, "subject": subject, "body": body})

Circular Dependency
~~~~~~~~~~~~~~~~~~~

**Error**: ``CircularDependencyError: Circular dependency detected: A -> B -> A``

**Cause**: Two or more services depend on each other in a cycle.

**Solution**: Refactor to break the cycle:

1. Extract shared logic into a third service
2. Use dependency inversion (depend on port, not concrete service)
3. Use events for loose coupling

Unresolvable Dependency
~~~~~~~~~~~~~~~~~~~~~~~

**Error**: ``UnresolvableDependencyError: Cannot resolve 'Config' - no adapter or service registered``

**Cause**: A dependency type is not registered in the container.

**Solution**: Register the dependency:

.. code-block:: python

   @service
   class Config:
       """Application configuration."""
       pass

Or for adapters:

.. code-block:: python

   @adapter.for_(ConfigPort, profile=Profile.PRODUCTION)
   class EnvConfig:
       pass

.. seealso::

   - :doc:`philosophy` - Understanding the testing philosophy
   - :doc:`patterns` - Common fake implementation patterns
   - :doc:`fixtures` - Container fixtures for pytest
