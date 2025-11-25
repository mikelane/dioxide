dioxide.lifecycle
=================

.. py:module:: dioxide.lifecycle

.. autoapi-nested-parse::

   Lifecycle management decorator for dioxide components.

   The @lifecycle decorator enables opt-in lifecycle management for components
   that need initialization and cleanup.



Attributes
----------

.. autoapisummary::

   dioxide.lifecycle.T


Functions
---------

.. autoapisummary::

   dioxide.lifecycle.lifecycle


Module Contents
---------------

.. py:data:: T

.. py:function:: lifecycle(cls)

   Mark a class as having lifecycle management.

   Components decorated with @lifecycle must implement:
   - async def initialize(self) -> None: Called at container startup
   - async def dispose(self) -> None: Called at container shutdown

   :param cls: The class to mark for lifecycle management

   :returns: The class with _dioxide_lifecycle attribute set

   :raises TypeError: If the class does not implement initialize() method

   .. admonition:: Example

      >>> @service
      ... @lifecycle
      ... class Database:
      ...     async def initialize(self) -> None:
      ...         self.engine = create_async_engine(...)
      ...
      ...     async def dispose(self) -> None:
      ...         await self.engine.dispose()
