dioxide.exceptions
==================

.. py:module:: dioxide.exceptions

.. autoapi-nested-parse::

   Custom exception classes for dioxide dependency injection errors.

   This module defines descriptive exception classes that provide helpful, actionable
   error messages when dependency resolution fails. These exceptions replace generic
   KeyError exceptions with detailed information about what went wrong and how to fix it.



Exceptions
----------

.. autoapisummary::

   dioxide.exceptions.AdapterNotFoundError
   dioxide.exceptions.ServiceNotFoundError
   dioxide.exceptions.CircularDependencyError


Module Contents
---------------

.. py:exception:: AdapterNotFoundError

   Bases: :py:obj:`Exception`


   Raised when no adapter is registered for a port.

   This error occurs when trying to resolve a Protocol/ABC (port) but no
   concrete implementation (adapter) is registered for the current profile.

   The error message includes:
   - The port type that couldn't be resolved
   - The active profile
   - List of available adapters (if any) for other profiles
   - Hint for how to register an adapter

   .. admonition:: Example

      >>> from dioxide import Container, Profile, adapter
      >>> from typing import Protocol
      >>>
      >>> class EmailPort(Protocol):
      ...     async def send(self, to: str, subject: str, body: str) -> None: ...
      >>>
      >>> @adapter.for_(EmailPort, profile=Profile.PRODUCTION)
      ... class SendGridAdapter:
      ...     async def send(self, to: str, subject: str, body: str) -> None:
      ...         pass
      >>>
      >>> container = Container()
      >>> container.scan(profile=Profile.TEST)  # No TEST adapter
      >>>
      >>> try:
      ...     container.resolve(EmailPort)
      ... except AdapterNotFoundError as e:
      ...     print(e)  # Shows available adapters and profile mismatch


.. py:exception:: ServiceNotFoundError

   Bases: :py:obj:`Exception`


   Raised when a service or component cannot be resolved.

   This error occurs when:
   1. Trying to resolve an unregistered type
   2. A service depends on an unresolvable dependency
   3. The dependency chain is broken

   The error message includes:
   - The service/component type that failed to resolve
   - The missing dependency (if applicable)
   - The active profile
   - List of available types in the container
   - Hint for how to register the service

   .. admonition:: Example

      >>> from dioxide import Container, service
      >>>
      >>> @service
      >>> class UserService:
      ...     def __init__(self, db: DatabasePort):  # DatabasePort not registered
      ...         self.db = db
      >>>
      >>> container = Container()
      >>> container.scan(profile='test')
      >>>
      >>> try:
      ...     container.resolve(UserService)
      ... except ServiceNotFoundError as e:
      ...     print(e)  # Shows missing DatabasePort dependency


.. py:exception:: CircularDependencyError

   Bases: :py:obj:`Exception`


   Raised when circular dependencies are detected during lifecycle initialization.

   This error occurs when @lifecycle components have circular dependencies
   that cannot be resolved through topological sorting.

   .. admonition:: Example

      >>> from dioxide import Container, service, lifecycle
      >>>
      >>> # This would cause a circular dependency error
      >>> # A depends on B, B depends on C, C depends on A
      >>>
      >>> container = Container()
      >>> try:
      ...     await container.start()
      ... except CircularDependencyError as e:
      ...     print(e)  # Shows which components are involved in the cycle
