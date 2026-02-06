Testing with dioxide
====================

This section documents dioxide's core testing philosophy and provides comprehensive
patterns for writing fast, reliable tests.

.. note::

   dioxide encourages **fakes over mocks**. Use fast, real implementations at
   architectural boundaries instead of mocking frameworks.

   The result: Tests that are fast, clear, and test real behavior.

Why This Matters
----------------

Traditional Python testing relies heavily on mocking frameworks (``unittest.mock``,
``pytest-mock``). While mocks have their place, they create problems:

- **Brittle tests** - Tests break when implementation changes
- **False confidence** - Tests pass but real code fails
- **Obscured intent** - What are we actually testing?
- **Complexity** - Mock setup becomes harder than the code being tested

dioxide takes a different approach: **use real implementations that are fast and
deterministic**. These are called "fakes".

The dioxide Philosophy
----------------------

   **Testing is architecture.** Good architecture makes testing easy without mocks.

dioxide encourages :doc:`hexagonal architecture </user_guide/hexagonal_architecture>`
(ports-and-adapters), which creates natural seams for testing. Instead of mocking,
you write simple fake implementations at these seams.

Quick Example
-------------

.. code-block:: python

   from dioxide import Container, Profile, adapter, service
   from dioxide.testing import fresh_container
   from typing import Protocol

   # Port (interface)
   class EmailPort(Protocol):
       async def send(self, to: str, subject: str, body: str) -> None: ...

   # Fake adapter for testing
   @adapter.for_(EmailPort, profile=Profile.TEST)
   class FakeEmailAdapter:
       def __init__(self):
           self.sent_emails = []

       async def send(self, to: str, subject: str, body: str) -> None:
           self.sent_emails.append({"to": to, "subject": subject, "body": body})

   # Test with fresh container
   async def test_email_sent():
       async with fresh_container(profile=Profile.TEST) as container:
           service = container.resolve(NotificationService)
           await service.notify("alice@example.com", "Hello!")

           email = container.resolve(EmailPort)
           assert len(email.sent_emails) == 1
           assert email.sent_emails[0]["to"] == "alice@example.com"

Documentation Sections
----------------------

.. toctree::
   :maxdepth: 2

   philosophy
   mock-vs-fake
   fakes-in-production
   writing-fakes
   patterns
   fixtures
   integration
   faq
   troubleshooting

API Reference
-------------

- :doc:`/api/dioxide/testing/index` - Testing utilities API
- :doc:`/api/dioxide/container/index` - Container API
- :doc:`/api/dioxide/profile_enum/index` - Profile enum

External Resources
------------------

- `Martin Fowler: Mocks Aren't Stubs <https://martinfowler.com/articles/mocksArentStubs.html>`_
- `Test Doubles (Meszaros) <http://xunitpatterns.com/Test%20Double.html>`_
- `Hexagonal Architecture <https://alistair.cockburn.us/hexagonal-architecture/>`_
