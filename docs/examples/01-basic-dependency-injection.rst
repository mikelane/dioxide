Tutorial 1: Basic Dependency Injection
========================================

This tutorial introduces the core concept of dependency injection with dioxide using a simple example.

What is Dependency Injection?
------------------------------

**Dependency Injection** means giving an object its dependencies from the outside, rather than having it create them itself. This makes code:

* **Easier to test** - Replace real dependencies with test fakes
* **More flexible** - Swap implementations without changing code
* **Loosely coupled** - Components don't know about each other's internals

The Problem: Tight Coupling
----------------------------

Without dependency injection, code is tightly coupled:

.. code-block:: python

   class EmailService:
       def __init__(self):
           self.smtp_client = SMTPClient("smtp.gmail.com", 587)  # Hard-coded!

       def send(self, to: str, subject: str, body: str):
           self.smtp_client.send_email(to, subject, body)

   class UserService:
       def __init__(self):
           self.email = EmailService()  # Creating its own dependency!

       def register_user(self, email: str, name: str):
           self.email.send(email, "Welcome!", f"Hello {name}")

**Problems with this approach:**

1. **Hard to test** - Can't test ``UserService`` without sending real emails
2. **Hard to change** - Switching email providers requires editing ``EmailService``
3. **Hidden dependencies** - No way to know what ``UserService`` needs without reading the code

The Solution: Dependency Injection
-----------------------------------

With dioxide, dependencies are **injected** via constructor parameters:

.. code-block:: python

   from dioxide import service

   @service
   class EmailService:
       def send(self, to: str, subject: str, body: str):
           print(f"📧 Sending email to {to}: {subject}")

   @service
   class UserService:
       def __init__(self, email: EmailService):  # Dependency injected!
           self.email = email

       def register_user(self, email_addr: str, name: str):
           self.email.send(email_addr, "Welcome!", f"Hello {name}")
           print(f"✅ User {name} registered")

**How it works:**

1. ``@service`` decorator registers classes with dioxide's container
2. Type hints (``email: EmailService``) tell dioxide what to inject
3. Container automatically creates ``EmailService`` and injects it into ``UserService``

Using the Services
------------------

**Option 1: Auto-injection (Recommended)**

Just import the ``container`` and scan your application:

.. code-block:: python

   from dioxide import container

   # Scan the current module/package for @service classes
   container.scan(__name__)

   # Now just create instances - dependencies are auto-injected!
   user_service = UserService()

   # Use the service
   user_service.register_user("alice@example.com", "Alice")

**Output:**

.. code-block:: text

   📧 Sending email to alice@example.com: Welcome!
   ✅ User Alice registered

**Option 2: Explicit Resolution**

You can also explicitly resolve services from the container:

.. code-block:: python

   from dioxide import Container

   container = Container()
   container.scan(__name__)

   # Resolve UserService from container
   user_service = container.resolve(UserService)
   user_service.register_user("bob@example.com", "Bob")

   # Or use bracket syntax
   user_service = container[UserService]

Complete Example
----------------

Here's a complete, runnable example:

.. code-block:: python

   """
   Basic Dependency Injection Example

   This example demonstrates:
   - @service decorator for automatic registration
   - Constructor injection via type hints
   - Automatic dependency resolution
   """
   from dioxide import service, Container

   @service
   class Logger:
       """Simple logging service."""

       def info(self, message: str) -> None:
           print(f"ℹ️  INFO: {message}")

       def error(self, message: str) -> None:
           print(f"❌ ERROR: {message}")

   @service
   class EmailService:
       """Email sending service with logging."""

       def __init__(self, logger: Logger):
           """Logger is automatically injected by dioxide."""
           self.logger = logger

       def send(self, to: str, subject: str, body: str) -> None:
           """Send an email (simulated)."""
           self.logger.info(f"Sending email to {to}: {subject}")
           # In real app, this would use SMTP, SendGrid, etc.
           print(f"📧 To: {to}\n   Subject: {subject}\n   Body: {body}")

   @service
   class UserService:
       """User registration service."""

       def __init__(self, email: EmailService, logger: Logger):
           """Both EmailService and Logger are auto-injected."""
           self.email = email
           self.logger = logger

       def register_user(self, email_addr: str, name: str) -> None:
           """Register a new user and send welcome email."""
           self.logger.info(f"Registering user: {name} ({email_addr})")

           # Send welcome email
           self.email.send(
               to=email_addr,
               subject="Welcome!",
               body=f"Hello {name}, welcome to our platform!"
           )

           self.logger.info(f"User {name} registered successfully")

   def main():
       """Run the example."""
       print("=" * 70)
       print("BASIC DEPENDENCY INJECTION EXAMPLE")
       print("=" * 70)

       # Set up the container
       container = Container()
       container.scan(__name__)

       # Get UserService (with all dependencies auto-injected)
       user_service = container.resolve(UserService)

       # Use the service
       user_service.register_user("alice@example.com", "Alice")
       print()
       user_service.register_user("bob@example.com", "Bob")

       print("=" * 70)
       print("KEY TAKEAWAYS:")
       print("✅ Services depend on other services via type hints")
       print("✅ No manual wiring - dioxide handles injection")
       print("✅ Dependencies are explicit in constructor")
       print("✅ Easy to understand what each service needs")
       print("=" * 70)

   if __name__ == "__main__":
       main()

Running the Example
-------------------

Save the example to a file (e.g., ``basic_di.py``) and run it:

.. code-block:: bash

   python basic_di.py

**Expected Output:**

.. code-block:: text

   ======================================================================
   BASIC DEPENDENCY INJECTION EXAMPLE
   ======================================================================
   ℹ️  INFO: Registering user: Alice (alice@example.com)
   ℹ️  INFO: Sending email to alice@example.com: Welcome!
   📧 To: alice@example.com
      Subject: Welcome!
      Body: Hello Alice, welcome to our platform!
   ℹ️  INFO: User Alice registered successfully

   ℹ️  INFO: Registering user: Bob (bob@example.com)
   ℹ️  INFO: Sending email to bob@example.com: Welcome!
   📧 To: bob@example.com
      Subject: Welcome!
      Body: Hello Bob, welcome to our platform!
   ℹ️  INFO: User Bob registered successfully
   ======================================================================
   KEY TAKEAWAYS:
   ✅ Services depend on other services via type hints
   ✅ No manual wiring - dioxide handles injection
   ✅ Dependencies are explicit in constructor
   ✅ Easy to understand what each service needs
   ======================================================================

Key Concepts
------------

``@service`` Decorator
~~~~~~~~~~~~~~~~~~~~~~

The ``@service`` decorator tells dioxide:

* This class should be managed by the container
* Create **one instance** (singleton) per container
* Auto-inject dependencies based on constructor type hints

**Singleton behavior**: By default, ``@service`` classes are singletons. The container creates one instance and reuses it:

.. code-block:: python

   container = Container()
   container.scan(__name__)

   service1 = container.resolve(UserService)
   service2 = container.resolve(UserService)

   assert service1 is service2  # Same instance!

Type Hints for Injection
~~~~~~~~~~~~~~~~~~~~~~~~~

dioxide uses Python's type hints to know what to inject:

.. code-block:: python

   @service
   class UserService:
       def __init__(self, email: EmailService):  # Type hint here!
           self.email = email

**Important**: dioxide only injects parameters that have type hints. Parameters without type hints must be provided manually:

.. code-block:: python

   @service
   class UserService:
       def __init__(self, email: EmailService, debug: bool = False):
           self.email = email  # Injected by dioxide
           self.debug = debug  # Must be provided manually

Container Scanning
~~~~~~~~~~~~~~~~~~

``container.scan(__name__)`` tells dioxide:

* Look in the specified module/package
* Find all classes decorated with ``@service`` (or ``@adapter``)
* Register them in the container

You can scan entire packages:

.. code-block:: python

   # Scan a specific package
   container.scan("myapp.services")

   # Scan multiple packages
   container.scan("myapp.services")
   container.scan("myapp.adapters")

Next Steps
----------

This tutorial showed basic dependency injection without profiles or ports. In the next tutorial, we'll learn:

* **Ports and Adapters** - Define interfaces (ports) with multiple implementations (adapters)
* **Profiles** - Use different implementations for production vs testing
* **Testing without Mocks** - Use fast fakes instead of mocking frameworks

Continue to: :doc:`02-email-service-with-profiles`
