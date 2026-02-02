Testing Philosophy: Fakes Over Mocks
=====================================

dioxide's testing philosophy is simple: **use fast, real implementations instead of
mocking frameworks**.

The Problem with Mocks
----------------------

Anti-Pattern: Testing Mock Behavior
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Here's a typical test using mocks:

.. code-block:: python

   # BAD: Testing mock configuration, not real code
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

What's Wrong Here?
~~~~~~~~~~~~~~~~~~

**1. Tight Coupling to Implementation**

The test knows too much about *how* the service works:

- It knows the exact method names (``create_user``, ``send_welcome``)
- It knows the order of operations
- It knows the exact arguments passed

If you refactor the service (rename methods, change order, etc.), tests break even
though *behavior* didn't change.

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

They verify that the code *does* something (calls methods), not that it *achieves*
something (registers user successfully).

----

Fakes at the Seams
------------------

The dioxide Way: Real Implementations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Instead of mocks, use **fast, real implementations** for testing:

.. code-block:: python

   # GOOD: Using fakes with dioxide
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
~~~~~~~~~~~~~~~~~~~~~~~~~

**1. Tests Real Code**

The business logic in ``UserService.register_user()`` actually runs. You're testing
real behavior, not mock configuration.

**2. Fast and Deterministic**

Fakes are in-memory (no I/O), so tests are fast. No database, no API calls, no flaky
network.

**3. Clear Intent**

The test clearly shows what it's verifying:

- User is created with correct data
- Welcome email is sent to correct address

No mock setup obscuring the purpose.

**4. Refactor-Friendly**

You can refactor ``UserService`` internals without breaking tests, as long as behavior
stays the same.

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

When to Use Mocks Instead
-------------------------

Very rarely. Consider mocks only when:

1. You're testing a third-party library you don't control
2. You need to verify specific method calls (use sparingly)
3. Creating a fake is genuinely more complex than a mock

**In most cases, a simple fake is better than a mock.**

Why Not Just Use @patch?
~~~~~~~~~~~~~~~~~~~~~~~~

**Short answer**: ``@patch`` is fine for pure functions and isolated units. Fakes at
architectural boundaries are better for stateful dependencies and integration testing.

**When @patch works well:**

- Testing pure functions in isolation
- Mocking third-party APIs you don't control (and haven't wrapped in a port)
- Quick prototyping before architecture solidifies

**When fakes at seams win:**

- Stateful dependencies (databases, caches, queues)
- Boundaries between architectural layers
- When you want tests that survive refactoring
- When mock configuration becomes more complex than the test itself

**Our recommendation:**

Default to fakes at architectural seams. Use ``@patch`` sparingly for edge cases.
If you find yourself with complex mock setup, that's a signal to introduce a port
and fake.

----

Key Takeaways
-------------

1. **Mocks test implementation, fakes test behavior**
2. **Fakes are real implementations that happen to be fast**
3. **Fakes live in production code, not test code**
4. **Good architecture makes testing easy without mocks**
5. **Profile-based swapping makes fakes trivial to activate**

.. seealso::

   - :doc:`patterns` - Common fake implementation patterns
   - :doc:`fixtures` - Container fixtures for pytest
   - :doc:`/user_guide/hexagonal_architecture` - Understanding ports and adapters
