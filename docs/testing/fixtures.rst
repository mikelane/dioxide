Test Fixtures
=============

dioxide provides pytest fixtures and utilities for writing isolated, fast tests.

fresh_container Context Manager
-------------------------------

The recommended way to create isolated test containers:

.. code-block:: python

   from dioxide import Profile
   from dioxide.testing import fresh_container

   async def test_user_registration():
       async with fresh_container(profile=Profile.TEST) as container:
           service = container.resolve(UserService)
           result = await service.register("alice@example.com", "Alice")

           email = container.resolve(EmailPort)
           assert len(email.sent_emails) == 1

**Benefits**:

- Complete isolation - each test starts with a clean slate
- No state leakage - singletons are scoped to the container instance
- Lifecycle handled - ``@lifecycle`` components are properly initialized/disposed
- Simple - no need to track or clear fake state

Pytest Plugin Fixtures
----------------------

Add the following to your ``conftest.py`` to enable dioxide pytest fixtures:

.. code-block:: python

   pytest_plugins = ['dioxide.testing']

This makes the following fixtures available:

- ``dioxide_container`` - Fresh container per test (function-scoped)
- ``fresh_container_fixture`` - Alias for dioxide_container
- ``dioxide_container_session`` - Shared container across tests (session-scoped)

dioxide_container Fixture
~~~~~~~~~~~~~~~~~~~~~~~~~

Provides a fresh, isolated container for each test:

.. code-block:: python

   async def test_user_service(dioxide_container):
       dioxide_container.scan(profile=Profile.TEST)
       service = dioxide_container.resolve(UserService)
       result = await service.register_user('Alice', 'alice@example.com')
       assert result['name'] == 'Alice'

fresh_container_fixture
~~~~~~~~~~~~~~~~~~~~~~~

Alternative fixture with name matching the context manager:

.. code-block:: python

   async def test_isolated(fresh_container_fixture):
       fresh_container_fixture.scan(profile=Profile.TEST)
       # Guaranteed fresh container, no state leakage

dioxide_container_session Fixture
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A session-scoped container shared across all tests:

.. code-block:: python

   # In conftest.py - scan once at session start
   @pytest.fixture(scope='session', autouse=True)
   def setup_session_container(dioxide_container_session):
       dioxide_container_session.scan(profile=Profile.TEST)

   # In tests - just use the pre-scanned container
   async def test_shared_container(dioxide_container_session):
       service = dioxide_container_session.resolve(SharedService)
       # ... use shared container

.. warning::

   Session-scoped containers share state between tests. Only use this when you
   understand the implications and tests are designed to handle shared state.

----

Fresh Container Per Test (Recommended)
--------------------------------------

The simplest and most reliable approach is creating a fresh container for each test:

.. code-block:: python

   import pytest
   from dioxide import Container, Profile

   @pytest.fixture
   async def container():
       """Fresh container per test - complete test isolation.

       Each test gets a fresh Container instance with:
       - Clean singleton cache (no state from previous tests)
       - Fresh adapter instances
       - Automatic lifecycle management via async context manager

       This is the RECOMMENDED pattern for test isolation.
       """
       c = Container()
       c.scan(profile=Profile.TEST)
       async with c:
           yield c
       # Cleanup happens automatically

**Why this works:**

- **Complete isolation**: Each test starts with a clean slate
- **No state leakage**: Singletons are scoped to the container instance
- **Lifecycle handled**: ``@lifecycle`` components are properly initialized/disposed
- **Simple**: No need to track or clear fake state

Typed Fixtures for Fakes
------------------------

Create typed fixtures to access your fake adapters with IDE support:

.. code-block:: python

   from app.adapters.fakes import FakeEmailAdapter, FakeDatabaseAdapter
   from app.domain.ports import EmailPort, DatabasePort

   @pytest.fixture
   def email(container) -> FakeEmailAdapter:
       """Typed access to fake email for assertions."""
       return container.resolve(EmailPort)

   @pytest.fixture
   def db(container) -> FakeDatabaseAdapter:
       """Typed access to fake db for seeding test data."""
       return container.resolve(DatabasePort)

Complete Test Example
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   async def test_user_registration_sends_welcome_email(container, email, db):
       """Test that registering a user sends a welcome email."""
       # Arrange: Get the service (dependencies auto-injected)
       service = container.resolve(UserService)

       # Act: Call the real service with real fakes
       await service.register_user("alice@example.com", "Alice")

       # Assert: Check observable outcomes (no mock verification!)
       assert len(email.sent_emails) == 1
       assert email.sent_emails[0]["to"] == "alice@example.com"
       assert "Welcome" in email.sent_emails[0]["subject"]

----

Profile-Based Testing
---------------------

dioxide's profile system makes it trivial to swap between real implementations
and fakes.

Fast Unit Tests (TEST Profile)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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
           print(f"Email to {to}: {subject}")

----

CI/CD Test Strategy
-------------------

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

----

Lifecycle in Tests
------------------

When testing components with lifecycle (``@lifecycle``), use the container's
async context manager.

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
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Most fakes don't need lifecycle because they're simple in-memory structures.

.. code-block:: python

   from typing import Protocol
   from dioxide import adapter, lifecycle, Profile

   class UserRepository(Protocol):
       async def find_by_id(self, user_id: int) -> dict | None: ...
       async def create(self, name: str, email: str) -> dict: ...

   # Usually overkill - fakes don't need lifecycle
   @adapter.for_(UserRepository, profile=Profile.TEST)
   @lifecycle
   class FakeUserRepository:
       async def initialize(self) -> None:
           self.users = {}  # Just initialize in __init__ instead

       async def dispose(self) -> None:
           self.users.clear()  # Not needed, GC will handle it

   # Better - simple fake without lifecycle
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

Alternative: Reset Container Between Tests
------------------------------------------

If you need a shared container (e.g., for TestClient integration tests), use
``container.reset()``:

.. code-block:: python

   from dioxide import container, Profile

   @pytest.fixture(autouse=True)
   def setup_container():
       """Reset container between tests for isolation."""
       container.scan(profile=Profile.TEST)
       yield
       container.reset()  # Clears singleton cache, keeps registrations

Or clear fake state manually if you need more control:

.. code-block:: python

   @pytest.fixture(autouse=True)
   def clear_fakes():
       """Clear fake state before each test."""
       # Clear adapters from global container before test runs
       db = container.resolve(DatabasePort)
       if hasattr(db, "users"):
           db.users.clear()

       email = container.resolve(EmailPort)
       if hasattr(email, "sent_emails"):
           email.sent_emails.clear()

.. note::

   The fresh container pattern is preferred because it requires no knowledge
   of fake internals.

.. seealso::

   - :doc:`/api/dioxide/testing/index` - Testing utilities API reference
   - :doc:`patterns` - Common fake implementation patterns
   - :doc:`troubleshooting` - Common pitfalls and solutions
