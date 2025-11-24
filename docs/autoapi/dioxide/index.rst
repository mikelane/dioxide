dioxide
=======

.. py:module:: dioxide

.. autoapi-nested-parse::

   dioxide: Fast, Rust-backed declarative dependency injection for Python.

   dioxide is a modern dependency injection framework that combines:
   - Declarative Python API with hexagonal architecture support
   - High-performance Rust-backed container implementation
   - Type-safe dependency resolution with IDE autocomplete support
   - Profile-based configuration for different environments

   Quick Start (using global singleton container):
       >>> from dioxide import container, service, adapter, Profile
       >>> from typing import Protocol
       >>>
       >>> class EmailPort(Protocol):
       ...     async def send(self, to: str, subject: str, body: str) -> None: ...
       >>>
       >>> @adapter.for_(EmailPort, profile=Profile.PRODUCTION)
       ... class SendGridAdapter:
       ...     async def send(self, to: str, subject: str, body: str) -> None:
       ...         pass  # Real implementation
       >>>
       >>> @service
       ... class UserService:
       ...     def __init__(self, email: EmailPort):
       ...         self.email = email
       >>>
       >>> container.scan(profile=Profile.PRODUCTION)
       >>> service = container.resolve(UserService)
       >>> # Or use bracket syntax:
       >>> service = container[UserService]

   Advanced: Creating separate containers for testing isolation:
       >>> from dioxide import Container
       >>>
       >>> test_container = Container()
       >>> test_container.scan(profile=Profile.TEST)
       >>> service = test_container.resolve(UserService)

   For more information, see the README and documentation.



Submodules
----------

.. toctree::
   :maxdepth: 1

   /autoapi/dioxide/adapter/index
   /autoapi/dioxide/container/index
   /autoapi/dioxide/exceptions/index
   /autoapi/dioxide/lifecycle/index
   /autoapi/dioxide/profile_enum/index
   /autoapi/dioxide/scope/index
   /autoapi/dioxide/services/index
