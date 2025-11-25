Tutorial 2: Email Service with Profiles
=========================================

This tutorial introduces **hexagonal architecture** (ports and adapters) and **profiles** to swap implementations between production and testing.

The Problem: Environment-Specific Behavior
-------------------------------------------

Applications need different implementations in different environments:

* **Production**: Send real emails via SendGrid, AWS SES, etc.
* **Testing**: Use fast fakes to verify behavior without I/O
* **Development**: Log emails to console for debugging

Without a good pattern, you end up with:

* Mock hell in tests (``@patch`` everywhere)
* Environment checks scattered throughout code (``if ENV == "test"``)
* Hard-coded dependencies that can't be swapped

The Solution: Ports and Adapters
---------------------------------

**Hexagonal Architecture** (also called Ports and Adapters) separates:

1. **Ports** - Interfaces that define what operations are needed
2. **Adapters** - Implementations of ports for specific environments
3. **Services** - Core business logic that depends on ports, not adapters

This creates **seams** where you can swap implementations without changing business logic.

Defining a Port
---------------

A **port** is an interface defined using Python's ``Protocol``:

.. code-block:: python

   from typing import Protocol

   class EmailPort(Protocol):
       """Port for sending emails.

       This defines WHAT email sending looks like,
       not HOW it's implemented.
       """

       async def send(self, to: str, subject: str, body: str) -> None:
           """Send an email to a recipient."""
           ...

**Key points:**

* Use ``Protocol`` from ``typing`` module
* Define method signatures only (no implementation)
* Add docstrings to explain the contract
* This is the **seam** where adapters connect

Creating Adapters
-----------------

**Adapters** are concrete implementations of ports for specific environments.

Production Adapter
~~~~~~~~~~~~~~~~~~

Real implementation using SendGrid:

.. code-block:: python

   from dioxide import adapter, Profile
   import httpx

   @adapter.for_(EmailPort, profile=Profile.PRODUCTION)
   class SendGridAdapter:
       """Production email adapter using SendGrid API."""

       def __init__(self, config: AppConfig):
           """Config injected by dioxide."""
           self.api_key = config.sendgrid_api_key

       async def send(self, to: str, subject: str, body: str) -> None:
           """Send email via SendGrid API."""
           async with httpx.AsyncClient() as client:
               response = await client.post(
                   "https://api.sendgrid.com/v3/mail/send",
                   headers={"Authorization": f"Bearer {self.api_key}"},
                   json={
                       "personalizations": [{"to": [{"email": to}]}],
                       "from": {"email": "noreply@example.com"},
                       "subject": subject,
                       "content": [{"type": "text/plain", "value": body}]
                   }
               )
               response.raise_for_status()

Test Adapter (Fake)
~~~~~~~~~~~~~~~~~~~

Fast fake for testing (no I/O):

.. code-block:: python

   @adapter.for_(EmailPort, profile=Profile.TEST)
   class FakeEmailAdapter:
       """Test adapter that records emails in memory."""

       def __init__(self):
           """No external dependencies - just in-memory storage."""
           self.sent_emails: list[dict] = []

       async def send(self, to: str, subject: str, body: str) -> None:
           """Record email instead of sending it."""
           self.sent_emails.append({
               "to": to,
               "subject": subject,
               "body": body
           })
           print(f"✅ [Fake] Recorded email to {to}: {subject}")

       def get_sent_emails(self) -> list[dict]:
           """Helper for test assertions."""
           return self.sent_emails

Development Adapter
~~~~~~~~~~~~~~~~~~~

Console logging for local development:

.. code-block:: python

   @adapter.for_(EmailPort, profile=Profile.DEVELOPMENT)
   class ConsoleEmailAdapter:
       """Development adapter that logs emails to console."""

       async def send(self, to: str, subject: str, body: str) -> None:
           """Print email to console."""
           print(f"\n{'='*70}")
           print("📧 [CONSOLE EMAIL]")
           print(f"To: {to}")
           print(f"Subject: {subject}")
           print(f"Body: {body}")
           print(f"{'='*70}\n")

Using Adapters with Profiles
-----------------------------

**Profile-based activation**: The container activates the correct adapter based on the profile:

.. code-block:: python

   from dioxide import Container, Profile, service

   @service
   class UserService:
       def __init__(self, email: EmailPort):
           """Depends on PORT (interface), not specific adapter."""
           self.email = email

       async def register_user(self, email_addr: str, name: str):
           """Business logic doesn't know which adapter is active."""
           await self.email.send(
               to=email_addr,
               subject="Welcome!",
               body=f"Hello {name}, welcome to our platform!"
           )

   # Production: Uses SendGridAdapter
   prod_container = Container()
   prod_container.scan("myapp", profile=Profile.PRODUCTION)
   prod_service = prod_container.resolve(UserService)
   await prod_service.register_user("alice@example.com", "Alice")

   # Testing: Uses FakeEmailAdapter
   test_container = Container()
   test_container.scan("myapp", profile=Profile.TEST)
   test_service = test_container.resolve(UserService)
   await test_service.register_user("bob@test.com", "Bob")

**Key insight**: ``UserService`` is identical in both cases. Only the profile changes.

Complete Example
----------------

Here's a complete, runnable example:

.. code-block:: python

   """
   Email Service with Profiles Example

   This example demonstrates:
   - Defining ports (interfaces) with Protocol
   - Creating adapters for different environments
   - Using profiles to activate different adapters
   - Testing without mocks using fakes
   """
   import asyncio
   from typing import Protocol
   from dioxide import adapter, service, Container, Profile

   # ===== PORT (INTERFACE) =====
   class EmailPort(Protocol):
       """Port for email sending."""

       async def send(self, to: str, subject: str, body: str) -> None:
           """Send an email."""
           ...

   # ===== ADAPTERS (IMPLEMENTATIONS) =====
   @adapter.for_(EmailPort, profile=Profile.PRODUCTION)
   class SendGridAdapter:
       """Production email via SendGrid (simulated)."""

       async def send(self, to: str, subject: str, body: str) -> None:
           print(f"📧 [SendGrid] Sending email to {to}")
           print(f"   Subject: {subject}")
           # In real app: call SendGrid API
           print(f"   ✅ Email sent via SendGrid API")

   @adapter.for_(EmailPort, profile=Profile.TEST)
   class FakeEmailAdapter:
       """Test fake - records emails in memory."""

       def __init__(self):
           self.sent_emails: list[dict] = []

       async def send(self, to: str, subject: str, body: str) -> None:
           self.sent_emails.append({"to": to, "subject": subject, "body": body})
           print(f"✅ [Fake] Recorded email to {to}: {subject}")

   @adapter.for_(EmailPort, profile=Profile.DEVELOPMENT)
   class ConsoleEmailAdapter:
       """Development email - prints to console."""

       async def send(self, to: str, subject: str, body: str) -> None:
           print(f"\n{'='*60}")
           print(f"📧 [CONSOLE] Email to {to}")
           print(f"Subject: {subject}")
           print(f"Body: {body}")
           print(f"{'='*60}\n")

   # ===== SERVICE (CORE LOGIC) =====
   @service
   class UserService:
       """User registration service."""

       def __init__(self, email: EmailPort):
           """Depends on PORT, not specific adapter."""
           self.email = email

       async def register_user(self, email_addr: str, name: str) -> None:
           """Register user and send welcome email."""
           print(f"Registering user: {name} ({email_addr})")
           await self.email.send(
               to=email_addr,
               subject="Welcome!",
               body=f"Hello {name}, welcome to our platform!"
           )
           print(f"User {name} registered\n")

   # ===== USAGE =====
   async def main():
       print("=" * 70)
       print("EMAIL SERVICE WITH PROFILES EXAMPLE")
       print("=" * 70)

       # Production Profile
       print("\n🏭 PRODUCTION PROFILE - SendGrid Adapter")
       print("-" * 70)
       prod_container = Container()
       prod_container.scan(__name__, profile=Profile.PRODUCTION)
       prod_service = prod_container.resolve(UserService)
       await prod_service.register_user("alice@example.com", "Alice")

       # Test Profile
       print("🧪 TEST PROFILE - Fake Adapter")
       print("-" * 70)
       test_container = Container()
       test_container.scan(__name__, profile=Profile.TEST)
       test_service = test_container.resolve(UserService)
       await test_service.register_user("bob@test.com", "Bob")

       # Verify fake captured the email
       fake_email = test_container.resolve(EmailPort)
       assert len(fake_email.sent_emails) == 1
       assert fake_email.sent_emails[0]["to"] == "bob@test.com"
       print("✅ Test assertion passed: Email was recorded")

       # Development Profile
       print("\n💻 DEVELOPMENT PROFILE - Console Adapter")
       print("-" * 70)
       dev_container = Container()
       dev_container.scan(__name__, profile=Profile.DEVELOPMENT)
       dev_service = dev_container.resolve(UserService)
       await dev_service.register_user("charlie@dev.local", "Charlie")

       print("=" * 70)
       print("KEY TAKEAWAYS:")
       print("✅ Ports define interfaces (Protocol)")
       print("✅ Adapters implement ports for specific environments")
       print("✅ Services depend on ports, not adapters")
       print("✅ Profiles activate different adapters")
       print("✅ Testing uses fast fakes, not mocks")
       print("=" * 70)

   if __name__ == "__main__":
       asyncio.run(main())

Running the Example
-------------------

Save the example to a file (e.g., ``email_profiles.py``) and run it:

.. code-block:: bash

   python email_profiles.py

Testing with Fakes
------------------

The fake adapter makes testing trivial - no mocking required:

.. code-block:: python

   import pytest
   from dioxide import Container, Profile

   @pytest.fixture
   def container():
       """Test container with fake adapters."""
       c = Container()
       c.scan("myapp", profile=Profile.TEST)
       return c

   @pytest.fixture
   def user_service(container):
       """Get UserService with fake email injected."""
       return container.resolve(UserService)

   @pytest.fixture
   def fake_email(container):
       """Get the fake email adapter for assertions."""
       return container.resolve(EmailPort)

   @pytest.mark.asyncio
   async def test_register_user_sends_welcome_email(user_service, fake_email):
       """Verify welcome email is sent on registration."""
       # Act
       await user_service.register_user("alice@test.com", "Alice")

       # Assert
       assert len(fake_email.sent_emails) == 1
       email = fake_email.sent_emails[0]
       assert email["to"] == "alice@test.com"
       assert email["subject"] == "Welcome!"
       assert "Alice" in email["body"]

**No mocks required!** The fake adapter is a **real implementation** that's fast and deterministic.

Key Concepts
------------

Ports (Protocols)
~~~~~~~~~~~~~~~~~

* Define **interfaces** using ``Protocol``
* Specify method signatures without implementation
* Create **seams** where adapters connect
* Services depend on ports, not concrete classes

Adapters
~~~~~~~~

* Concrete implementations of ports
* Use ``@adapter.for_(Port, profile=...)`` decorator
* One adapter per environment/profile
* Can have different dependencies (e.g., API keys in production, none in test)

Profiles
~~~~~~~~

Available profiles:

* ``Profile.PRODUCTION`` - Real implementations (SendGrid, PostgreSQL, etc.)
* ``Profile.TEST`` - Fast fakes (in-memory, no I/O)
* ``Profile.DEVELOPMENT`` - Dev-friendly implementations (console logging, SQLite)
* ``Profile.STAGING`` - Staging environment
* ``Profile.CI`` - CI/CD pipelines

Custom profiles are also supported:

.. code-block:: python

   @adapter.for_(EmailPort, profile="demo")
   class DemoEmailAdapter:
       """Custom profile for demos."""
       pass

   container.scan("myapp", profile="demo")

Fakes vs Mocks
~~~~~~~~~~~~~~

**Fakes** are better than **mocks** because:

* **Fakes** are real implementations (fast, no I/O)
* **Mocks** test mock configuration, not real behavior
* **Fakes** are reusable (tests, dev, demos)
* **Mocks** are brittle (break when refactoring)

.. code-block:: python

   # ❌ Mock approach (testing mock behavior)
   @patch("myapp.SendGridClient.send")
   async def test_with_mock(mock_send):
       mock_send.return_value = True
       # Are we testing real code or mock setup? 🤔

   # ✅ Fake approach (testing real code)
   async def test_with_fake(fake_email):
       await user_service.register_user("alice@test.com", "Alice")
       assert len(fake_email.sent_emails) == 1  # Real behavior!

Next Steps
----------

This tutorial showed hexagonal architecture with a single port. In the next tutorial, we'll build a multi-tier application with:

* Multiple ports (database, cache, email)
* Multiple adapters per port
* Service layer orchestrating multiple ports
* Integration testing patterns

Continue to: :doc:`03-multi-tier-application`
