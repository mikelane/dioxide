AdapterNotFoundError
====================

.. contents::
   :local:
   :depth: 2

Overview
--------

``AdapterNotFoundError`` is raised when you try to resolve a port (Protocol or ABC) but
no adapter is registered for the current profile.

This error means:

1. No adapter exists for this port + profile combination, OR
2. An adapter exists but for a different profile, OR
3. The adapter wasn't imported before container scanning

Example Error
-------------

.. code-block:: text

   Adapter Not Found: No adapter for EmailPort in profile 'test'
     Registered: SendGridAdapter (production), ConsoleEmailAdapter (development)

   Context:
     - port: EmailPort
     - profile: test
     - available_adapters: [('SendGridAdapter', ['production']), ('ConsoleEmailAdapter', ['development'])]

   -> See: https://dioxide.readthedocs.io/en/stable/troubleshooting/adapter-not-found.html

Common Causes
-------------

Profile Mismatch (Most Common)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You have an adapter registered for one profile, but you're scanning with a different profile.

.. code-block:: python

   from dioxide import Container, Profile, adapter

   class EmailPort(Protocol):
       async def send(self, to: str, subject: str, body: str) -> None: ...

   # Only PRODUCTION adapter exists
   @adapter.for_(EmailPort, profile=Profile.PRODUCTION)
   class SendGridAdapter:
       async def send(self, to: str, subject: str, body: str) -> None:
           ...

   # But you're scanning with TEST profile
   container = Container(profile=Profile.TEST)  # AdapterNotFoundError!

**Solution**: Add an adapter for the TEST profile:

.. code-block:: python

   @adapter.for_(EmailPort, profile=Profile.TEST)
   class FakeEmailAdapter:
       def __init__(self):
           self.sent_emails = []

       async def send(self, to: str, subject: str, body: str) -> None:
           self.sent_emails.append({"to": to, "subject": subject, "body": body})

Missing Adapter Completely
~~~~~~~~~~~~~~~~~~~~~~~~~~

No adapter is registered for the port at all.

.. code-block:: python

   class DatabasePort(Protocol):
       async def query(self, sql: str) -> list[dict]: ...

   @service
   class UserService:
       def __init__(self, db: DatabasePort):  # Depends on DatabasePort
           self.db = db

   container = Container(profile=Profile.PRODUCTION)  # AdapterNotFoundError!

**Solution**: Register an adapter for the port:

.. code-block:: python

   @adapter.for_(DatabasePort, profile=Profile.PRODUCTION)
   class PostgresAdapter:
       async def query(self, sql: str) -> list[dict]:
           ...

Adapter Not Imported
~~~~~~~~~~~~~~~~~~~~

The adapter module wasn't imported before scanning, so the decorator never executed.

.. code-block:: python

   # myapp/adapters/email.py
   @adapter.for_(EmailPort, profile=Profile.PRODUCTION)
   class SendGridAdapter:
       ...

   # myapp/main.py
   # Forgot to import myapp.adapters.email!
   container = Container(profile=Profile.PRODUCTION)  # AdapterNotFoundError!

**Solution**: Either import the module or use package scanning:

.. code-block:: python

   # Option 1: Explicit import
   import myapp.adapters.email  # Decorator runs at import

   container = Container(profile=Profile.PRODUCTION)

   # Option 2: Package scanning (recommended)
   container = Container(profile=Profile.PRODUCTION)
   container.scan(package="myapp.adapters")

Solutions
---------

Universal Adapter (Profile.ALL)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If an adapter should work in all profiles (e.g., logging), use ``Profile.ALL``:

.. code-block:: python

   @adapter.for_(LoggerPort, profile=Profile.ALL)
   class ConsoleLogger:
       def log(self, message: str) -> None:
           print(message)

   # Works with any profile
   container = Container(profile=Profile.TEST)
   logger = container.resolve(LoggerPort)  # Works!

Multiple Profile Registration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Register an adapter for multiple profiles:

.. code-block:: python

   @adapter.for_(EmailPort, profile=[Profile.TEST, Profile.DEVELOPMENT])
   class FakeEmailAdapter:
       ...

Debugging Tips
--------------

1. **Check the error message**: It lists available adapters and their profiles
2. **Verify profile spelling**: Profiles are case-insensitive but must match
3. **Use Profile enum**: Prefer ``Profile.TEST`` over ``'test'`` to catch typos
4. **List registrations**: Use ``container.scan(package="...")`` for auto-discovery

Best Practices
--------------

1. **Every production adapter needs a test fake**: Create a fast, in-memory fake for testing
2. **Use Profile.ALL sparingly**: Only for truly universal adapters like logging
3. **Fail fast at startup**: Resolve all services at startup to catch missing adapters early
4. **Use explicit profiles**: Prefer ``Profile`` enum over strings

See Also
--------

- :doc:`/user_guide/hexagonal_architecture` - How ports and adapters work
- :doc:`/guides/scoping` - Understanding profiles and scopes
- :doc:`service-not-found` - Similar error for services
