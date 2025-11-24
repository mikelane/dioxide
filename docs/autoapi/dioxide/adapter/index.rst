dioxide.adapter
===============

.. py:module:: dioxide.adapter

.. autoapi-nested-parse::

   Adapter decorator for hexagonal architecture.

   The @adapter decorator enables marking concrete implementations for
   Protocol/ABC ports with explicit profile associations, supporting
   hexagonal/ports-and-adapters architecture patterns.

   .. admonition:: Example

      >>> from typing import Protocol
      >>> from dioxide import adapter
      >>>
      >>> class EmailPort(Protocol):
      ...     async def send(self, to: str, subject: str, body: str) -> None: ...
      >>>
      >>> @adapter.for_(EmailPort, profile='production')
      ... class SendGridAdapter:
      ...     async def send(self, to: str, subject: str, body: str) -> None:
      ...         # Real SendGrid implementation
      ...         pass
      >>>
      >>> @adapter.for_(EmailPort, profile='test')
      ... class FakeEmailAdapter:
      ...     def __init__(self) -> None:
      ...         self.sent_emails: list[dict[str, str]] = []
      ...
      ...     async def send(self, to: str, subject: str, body: str) -> None:
      ...         self.sent_emails.append({'to': to, 'subject': subject, 'body': body})



Attributes
----------

.. autoapisummary::

   dioxide.adapter.adapter


Classes
-------

.. autoapisummary::

   dioxide.adapter.AdapterDecorator


Module Contents
---------------

.. py:class:: AdapterDecorator

   Main decorator class with .for_() method for marking adapters.

   This decorator enables hexagonal architecture by explicitly marking
   concrete implementations (adapters) for abstract ports (Protocols/ABCs)
   with environment-specific profiles.

   The decorator requires explicit profile association to make deployment
   configuration visible at the seams.


   .. py:method:: for_(port, *, profile = '*')

      Register an adapter for a port with profile(s).

      :param port: The Protocol or ABC that this adapter implements
      :param profile: Profile name(s) - string or list of strings.
                      Normalized to lowercase for consistency.

      :returns: Decorator function that marks the class as an adapter

      :raises TypeError: If profile parameter is not provided

      .. admonition:: Example

         >>> @adapter.for_(EmailPort, profile='production')
         ... class SendGridAdapter:
         ...     pass
         >>>
         >>> @adapter.for_(EmailPort, profile=['test', 'development'])
         ... class FakeAdapter:
         ...     pass



.. py:data:: adapter
