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


   Component lifecycle scope.

   Defines how instances of a component are created and cached:

   - SINGLETON: One shared instance for the lifetime of the container.
     The factory is called once and the result is cached. Subsequent
     resolve() calls return the same instance.

   - FACTORY: New instance created on each resolve() call. The factory
     is invoked every time the component is requested, creating a fresh
     instance.

   .. admonition:: Example

      >>> from dioxide import Container, component, Scope
      >>>
      >>> @component  # Default: SINGLETON scope
      ... class Database:
      ...     pass
      >>>
      >>> @component(scope=Scope.FACTORY)
      ... class RequestHandler:
      ...     request_id: int = 0
      ...
      ...     def __init__(self):
      ...         RequestHandler.request_id += 1
      ...         self.id = RequestHandler.request_id
      >>>
      >>> container = Container()
      >>> container.scan()
      >>>
      >>> # Singleton: same instance every time
      >>> db1 = container.resolve(Database)
      >>> db2 = container.resolve(Database)
      >>> assert db1 is db2
      >>>
      >>> # Factory: new instance every time
      >>> handler1 = container.resolve(RequestHandler)
      >>> handler2 = container.resolve(RequestHandler)
      >>> assert handler1 is not handler2
      >>> assert handler1.id != handler2.id


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


   .. py:attribute:: REQUEST
      :value: 'request'


      New instance created per request scope.

      Similar to FACTORY but intended for request-scoped contexts like
      web frameworks where the same instance should be reused within a
      single request but fresh instances created for each new request.

      Use for:
      - Request-scoped services in web frameworks
      - Per-request database sessions
      - Request context objects
      - User authentication/authorization state per request

      Note: Request scope behavior requires integration with a request
      context provider (e.g., FastAPI dependencies, Flask request context).
      Without such integration, REQUEST scope behaves like FACTORY.
