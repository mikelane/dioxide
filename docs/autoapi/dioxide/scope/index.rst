dioxide.scope
=============

.. py:module:: dioxide.scope

.. autoapi-nested-parse::

   Dependency injection scopes.

   This module defines the lifecycle scopes available for components in the
   dependency injection container.



Classes
-------

.. autoapisummary::

   dioxide.scope.Scope


Module Contents
---------------

.. py:class:: Scope

   Bases: :py:obj:`str`, :py:obj:`enum.Enum`


   Initialize self.  See help(type(self)) for accurate signature.


   .. py:attribute:: SINGLETON
      :value: 'singleton'


      One shared instance for the lifetime of the container.

      The component factory is called once and the result is cached.
      All subsequent resolve() calls return the same instance.

      Use for:
      - Database connections
      - Configuration objects
      - Services with shared state
      - Expensive-to-create objects


   .. py:attribute:: FACTORY
      :value: 'factory'


      New instance created on each resolve() call.

      The component factory is invoked every time the component is
      requested, creating a fresh instance.

      Use for:
      - Request handlers
      - Transient data objects
      - Stateful components that shouldn't be shared
      - Objects with per-request lifecycle
