Getting Started
===============

Welcome to dioxide! This guide will help you understand dioxide and get your first dependency injection system up and running in minutes.

What is dioxide?
----------------

**dioxide** is a declarative dependency injection framework for Python that makes clean architecture simple.

Why dioxide exists
^^^^^^^^^^^^^^^^^^

Most Python codebases struggle with:

- **Tight coupling**: Business logic hardcoded to specific databases, email providers, etc.
- **Hard to test**: Requires complex mocking setups that test mock behavior, not real code
- **Architecture drift**: No clear boundaries between core logic and infrastructure
- **Expensive changes**: Swapping implementations requires editing dozens of files

dioxide solves this by making the **Dependency Inversion Principle** trivial to apply:

- Define **ports** (interfaces using Python Protocols)
- Implement **adapters** (concrete implementations for different environments)
- Write **services** (business logic that depends on ports, not adapters)
- Let dioxide **wire everything automatically** based on type hints

Key Benefits
^^^^^^^^^^^^

- **Type-Safe**: If mypy passes, your wiring is correct
- **Profile-Based**: Different implementations for production, test, development
- **Fast Fakes**: Test with real implementations, not mocks
- **Rust Performance**: Fast container operations via PyO3
- **Zero Ceremony**: No manual `.bind()` or `.register()` calls
- **Request Scoping**: Isolate dependencies per request, task, or any bounded context

Installation
------------

Prerequisites
^^^^^^^^^^^^^

dioxide requires:

- **Python**: 3.11, 3.12, 3.13, or 3.14
- **Platform**: Linux (x86_64, ARM64), macOS (Intel, Apple Silicon), Windows (x86_64)

Install via pip
^^^^^^^^^^^^^^^

The simplest way to install dioxide:

.. code-block:: bash

   pip install dioxide

Install via uv (recommended)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you're using `uv <https://docs.astral.sh/uv/>`_ for fast Python package management:

.. code-block:: bash

   uv add dioxide

Install via poetry
^^^^^^^^^^^^^^^^^^

If you're using Poetry:

.. code-block:: bash

   poetry add dioxide

Verify installation
^^^^^^^^^^^^^^^^^^^

Check that dioxide is installed correctly:

.. code-block:: bash

   python -c "import dioxide; print(dioxide.__version__)"

Platform support matrix
^^^^^^^^^^^^^^^^^^^^^^^

.. list-table::
   :header-rows: 1
   :widths: 20 20 20

   * - Platform
     - x86_64
     - ARM64/aarch64
   * - Linux
     - ✅
     - ✅
   * - macOS
     - ✅
     - ✅ (M1/M2/M3)
   * - Windows
     - ✅
     - ❌

Your First Example
------------------

Let's build a simple notification system to understand dioxide's core concepts.

The Problem
^^^^^^^^^^^

You're building an app that sends welcome emails. In production, you'll use a real email service (SendGrid), but in tests, you want fast fakes without mocking frameworks.

**Traditional approach** (tight coupling):

.. code-block:: python

   # ❌ Tightly coupled to SendGrid
   class UserService:
       def __init__(self):
           self.sendgrid_client = SendGridAPIClient(api_key="...")

       async def register_user(self, email: str, name: str):
           # Hardcoded to SendGrid!
           self.sendgrid_client.send(...)

**Problems**:

- Can't test without hitting SendGrid API or complex mocking
- Can't swap to different email provider without rewriting UserService
- Business logic mixed with infrastructure details

The dioxide Way
^^^^^^^^^^^^^^^

Step 1: Define the Port (Interface)
""""""""""""""""""""""""""""""""""""

First, define what operations you need using a Python Protocol:

.. code-block:: python

   from typing import Protocol

   class EmailPort(Protocol):
       """Port (interface) for email operations."""

       async def send(self, to: str, subject: str, body: str) -> None:
           """Send an email to recipient."""
           ...

This is your **seam** - the boundary between core logic and infrastructure.

Step 2: Create Adapters for Different Environments
"""""""""""""""""""""""""""""""""""""""""""""""""""

Now implement the port for production and testing:

.. code-block:: python

   from dioxide import adapter, Profile

   # Production adapter - real SendGrid
   @adapter.for_(EmailPort, profile=Profile.PRODUCTION)
   class SendGridAdapter:
       """Production email adapter using SendGrid API."""

       def __init__(self):
           import os
           self.api_key = os.getenv("SENDGRID_API_KEY")

       async def send(self, to: str, subject: str, body: str) -> None:
           # Real SendGrid API calls
           import httpx
           async with httpx.AsyncClient() as client:
               await client.post(
                   "https://api.sendgrid.com/v3/mail/send",
                   headers={"Authorization": f"Bearer {self.api_key}"},
                   json={
                       "personalizations": [{"to": [{"email": to}]}],
                       "from": {"email": "noreply@example.com"},
                       "subject": subject,
                       "content": [{"type": "text/plain", "value": body}]
                   }
               )

   # Test adapter - fast fake
   @adapter.for_(EmailPort, profile=Profile.TEST)
   class FakeEmailAdapter:
       """Test email adapter that captures sends in memory."""

       def __init__(self):
           self.sent_emails = []  # Observable state for assertions

       async def send(self, to: str, subject: str, body: str) -> None:
           # No I/O - just capture for verification
           self.sent_emails.append({
               "to": to,
               "subject": subject,
               "body": body
           })

   # Development adapter - console logging
   @adapter.for_(EmailPort, profile=Profile.DEVELOPMENT)
   class ConsoleEmailAdapter:
       """Development email adapter that prints to console."""

       async def send(self, to: str, subject: str, body: str) -> None:
           print(f"📧 Email to: {to}")
           print(f"   Subject: {subject}")
           print(f"   Body: {body}")

Step 3: Write Business Logic (Service)
"""""""""""""""""""""""""""""""""""""""

Your core business logic depends on the **port**, not any specific adapter:

.. code-block:: python

   from dioxide import service

   @service
   class UserService:
       """Core business logic for user operations."""

       def __init__(self, email: EmailPort):
           # Depends on PORT, not concrete adapter!
           # Container auto-injects based on active profile
           self.email = email

       async def register_user(self, email_addr: str, name: str):
           """Register a new user and send welcome email."""
           # Business logic - doesn't know/care which email adapter is active
           print(f"Registering user: {name} ({email_addr})")

           # Send welcome email via injected adapter
           await self.email.send(
               to=email_addr,
               subject="Welcome to Our Service!",
               body=f"Hello {name},\n\nThanks for signing up!\n\nBest regards,\nThe Team"
           )

           print(f"User {name} registered successfully!")
           return True

Step 4: Wire It All Together
"""""""""""""""""""""""""""""

dioxide automatically wires dependencies based on the active profile:

.. code-block:: python

   from dioxide import Container, Profile

   async def main():
       # Production: activates SendGridAdapter
       container = Container()
       container.scan(profile=Profile.PRODUCTION)

       user_service = container.resolve(UserService)
       await user_service.register_user("alice@example.com", "Alice")
       # 📧 Sends real email via SendGrid

Step 5: Test Without Mocks
"""""""""""""""""""""""""""

Testing is trivial - just change the profile:

.. code-block:: python

   import pytest
   from dioxide import Container, Profile

   @pytest.fixture
   def container():
       """Create test container with fakes."""
       c = Container()
       c.scan(profile=Profile.TEST)  # Activates FakeEmailAdapter
       return c

   @pytest.mark.asyncio
   async def test_register_user_sends_welcome_email(container):
       """Register user sends welcome email."""
       # Arrange
       user_service = container.resolve(UserService)
       fake_email = container.resolve(EmailPort)  # Gets FakeEmailAdapter

       # Act
       result = await user_service.register_user("bob@example.com", "Bob")

       # Assert - check real observable outcomes (no mocks!)
       assert result is True
       assert len(fake_email.sent_emails) == 1
       assert fake_email.sent_emails[0]["to"] == "bob@example.com"
       assert fake_email.sent_emails[0]["subject"] == "Welcome to Our Service!"
       assert "Bob" in fake_email.sent_emails[0]["body"]

Complete Working Example
^^^^^^^^^^^^^^^^^^^^^^^^

Here's the complete code you can copy and run:

.. code-block:: python

   """
   Complete dioxide example: User registration with email notifications.

   Run with different profiles to see adapter swapping in action:
   - DIOXIDE_PROFILE=production python example.py (uses SendGrid)
   - DIOXIDE_PROFILE=test python example.py (uses fake)
   - DIOXIDE_PROFILE=development python example.py (prints to console)
   """

   import asyncio
   import os
   from typing import Protocol

   from dioxide import Container, Profile, adapter, service


   # ============================================================================
   # PORTS (Interfaces)
   # ============================================================================
   class EmailPort(Protocol):
       """Port for email operations."""

       async def send(self, to: str, subject: str, body: str) -> None:
           """Send an email."""
           ...


   # ============================================================================
   # ADAPTERS (Implementations)
   # ============================================================================
   @adapter.for_(EmailPort, profile=Profile.PRODUCTION)
   class SendGridAdapter:
       """Production email via SendGrid."""

       def __init__(self):
           self.api_key = os.getenv("SENDGRID_API_KEY", "demo-key")

       async def send(self, to: str, subject: str, body: str) -> None:
           print(f"📧 [SendGrid] Sending email to {to}: {subject}")
           # Real API call would go here
           # await client.post("https://api.sendgrid.com/v3/mail/send", ...)


   @adapter.for_(EmailPort, profile=Profile.TEST)
   class FakeEmailAdapter:
       """Test email adapter (captures in memory)."""

       def __init__(self):
           self.sent_emails = []

       async def send(self, to: str, subject: str, body: str) -> None:
           self.sent_emails.append({"to": to, "subject": subject, "body": body})
           print(f"✅ [Fake] Email captured: {to}")


   @adapter.for_(EmailPort, profile=Profile.DEVELOPMENT)
   class ConsoleEmailAdapter:
       """Development email adapter (prints to console)."""

       async def send(self, to: str, subject: str, body: str) -> None:
           print(f"📧 [Console] Email to: {to}")
           print(f"   Subject: {subject}")
           print(f"   Body: {body[:50]}...")


   # ============================================================================
   # SERVICES (Business Logic)
   # ============================================================================
   @service
   class UserService:
       """Core business logic for user operations."""

       def __init__(self, email: EmailPort):
           self.email = email

       async def register_user(self, email_addr: str, name: str):
           """Register user and send welcome email."""
           print(f"Registering user: {name} ({email_addr})")

           await self.email.send(
               to=email_addr,
               subject="Welcome!",
               body=f"Hello {name}, thanks for signing up!"
           )

           print(f"User {name} registered successfully!")
           return True


   # ============================================================================
   # APPLICATION
   # ============================================================================
   async def main():
       # Get profile from environment (defaults to development)
       profile_name = os.getenv("DIOXIDE_PROFILE", "development")
       profile = getattr(Profile, profile_name.upper())

       print(f"Starting with profile: {profile.value}\n")

       # Create container and scan for components
       container = Container()
       container.scan(profile=profile)

       # Resolve and use service
       user_service = container.resolve(UserService)
       await user_service.register_user("alice@example.com", "Alice")


   if __name__ == "__main__":
       asyncio.run(main())

Run this example with different profiles:

.. code-block:: bash

   # Development (console output)
   DIOXIDE_PROFILE=development python example.py

   # Test (fake adapter)
   DIOXIDE_PROFILE=test python example.py

   # Production (SendGrid)
   export SENDGRID_API_KEY="your-api-key"
   DIOXIDE_PROFILE=production python example.py

Key Concepts Explained
----------------------

Ports
^^^^^

**Ports** are interfaces defined using Python's ``Protocol`` class. They define **what** operations you need without specifying **how** they're implemented.

.. code-block:: python

   from typing import Protocol

   class DatabasePort(Protocol):
       """Port for database operations."""

       async def save_user(self, user: dict) -> int:
           """Save user to database, return user ID."""
           ...

       async def get_user(self, user_id: int) -> dict | None:
           """Get user by ID, return None if not found."""
           ...

**Why ports?**

- Define clear boundaries (seams) in your architecture
- Business logic depends on ports, not concrete implementations
- Easy to swap implementations (PostgreSQL → SQLite → in-memory)
- Protocols provide type safety (mypy validates implementations)

Adapters
^^^^^^^^

**Adapters** are concrete implementations of ports for specific environments.

.. code-block:: python

   from dioxide import adapter, Profile

   @adapter.for_(DatabasePort, profile=Profile.PRODUCTION)
   class PostgresAdapter:
       """Production database using PostgreSQL."""

       def __init__(self):
           self.connection_string = "postgresql://..."

       async def save_user(self, user: dict) -> int:
           # Real PostgreSQL implementation
           pass

       async def get_user(self, user_id: int) -> dict | None:
           # Real PostgreSQL query
           pass

   @adapter.for_(DatabasePort, profile=Profile.TEST)
   class InMemoryAdapter:
       """Test database using in-memory dictionary."""

       def __init__(self):
           self.users = {}
           self.next_id = 1

       async def save_user(self, user: dict) -> int:
           user_id = self.next_id
           self.users[user_id] = user
           self.next_id += 1
           return user_id

       async def get_user(self, user_id: int) -> dict | None:
           return self.users.get(user_id)

**Key points**:

- One port can have multiple adapters (one per profile)
- Adapters are singletons by default (one instance per container)
- Container activates the correct adapter based on profile

Services
^^^^^^^^

**Services** contain core business logic and depend on ports:

.. code-block:: python

   from dioxide import service

   @service
   class UserService:
       """Core business logic."""

       def __init__(self, db: DatabasePort, email: EmailPort):
           # Depends on PORTS, not adapters!
           self.db = db
           self.email = email

       async def register_user(self, email: str, name: str):
           # Pure business logic
           user = {"email": email, "name": name}
           user_id = await self.db.save_user(user)
           await self.email.send(email, "Welcome!", f"Hello {name}!")
           return user_id

**Key points**:

- Services are always singletons (one instance per container)
- Available in ALL profiles (doesn't vary by environment)
- Dependencies auto-injected via constructor type hints
- Zero knowledge of which adapters are active

Profiles
^^^^^^^^

**Profiles** control which adapters are active for a given environment:

.. code-block:: python

   from dioxide import Profile

   # Standard profiles
   Profile.PRODUCTION   # Real implementations (PostgreSQL, SendGrid, AWS)
   Profile.TEST         # Fast fakes for testing (in-memory, fake email)
   Profile.DEVELOPMENT  # Dev-friendly (SQLite, console logging)
   Profile.STAGING      # Pre-production environment
   Profile.CI           # CI/CD pipelines
   Profile.ALL          # Available in all profiles

**Activation**:

.. code-block:: python

   from dioxide import Container, Profile

   # Production
   prod_container = Container()
   prod_container.scan(profile=Profile.PRODUCTION)
   # Activates: PostgresAdapter, SendGridAdapter, etc.

   # Testing
   test_container = Container()
   test_container.scan(profile=Profile.TEST)
   # Activates: InMemoryAdapter, FakeEmailAdapter, etc.

Container
^^^^^^^^^

The **Container** is dioxide's dependency injection engine:

.. code-block:: python

   from dioxide import Container, Profile

   # Create container
   container = Container()

   # Scan for components with profile
   container.scan(profile=Profile.PRODUCTION)

   # Resolve dependencies
   user_service = container.resolve(UserService)
   # UserService auto-injected with production adapters

   # Alternative syntax
   user_service = container[UserService]

**How it works**:

1. ``container.scan(profile=...)`` discovers all ``@adapter`` and ``@service`` decorators
2. Activates adapters matching the profile
3. Builds dependency graph from constructor type hints
4. ``container.resolve(Type)`` walks graph and injects dependencies
5. Singletons cached (one instance per type per container)

Next Steps
----------

Now that you understand the basics, explore:

1. **Hexagonal Architecture** - Deep dive into ports-and-adapters pattern
2. **Profiles** - Advanced profile configuration and custom profiles
3. **Lifecycle Management** - Initialize and cleanup resources with ``@lifecycle``
4. **Scoping** - Isolate dependencies per request, background task, or CLI command
5. **Testing with Fakes** - Best practices for testing without mocks
6. **Framework Integration** - Use dioxide with FastAPI, Flask, Django

.. seealso::

   - :doc:`hexagonal_architecture` - Complete guide to ports-and-adapters
   - :doc:`profiles` - Profile system in depth
   - :doc:`lifecycle` - Resource management and cleanup
   - :doc:`/guides/scoping` - Request scoping and bounded contexts
   - :doc:`testing_with_fakes` - Testing philosophy and patterns
   - :doc:`framework_integration` - FastAPI, Flask, Django integration

Getting Help
------------

- **GitHub Issues**: `<https://github.com/mikelane/dioxide/issues>`_
- **Discussions**: `<https://github.com/mikelane/dioxide/discussions>`_
- **Documentation**: `<https://dioxide.readthedocs.io>`_

Common Questions
----------------

**Q: Do I need to use Rust?**

No! dioxide is a Python package. The Rust backend is compiled into binary wheels, so you just ``pip install dioxide`` like any other package.

**Q: Can I use regular Python classes instead of Protocols?**

Yes! Ports can be Protocols or ABC (Abstract Base Classes). Protocols are preferred for structural typing, but ABCs work too.

**Q: What if I don't want hexagonal architecture?**

dioxide is designed for hexagonal architecture (ports-and-adapters). If you don't need that pattern, simpler DI frameworks might be better fit.

**Q: How do I debug which adapter is active?**

.. code-block:: python

   # Resolve the port to see which adapter is active
   email_adapter = container.resolve(EmailPort)
   print(type(email_adapter))  # <class 'SendGridAdapter'>

**Q: Can I have multiple containers?**

Yes! Each ``Container()`` instance is independent with its own singletons and active profile.

**Q: Is dioxide production-ready?**

dioxide is in **beta** (v0.1.0-beta.2 as of Nov 2025). The API is now frozen. Use with caution in production until v1.0.0 stable.
