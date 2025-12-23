dioxide.fastapi
===============

.. py:module:: dioxide.fastapi

.. autoapi-nested-parse::

   FastAPI integration for dioxide dependency injection.

   This module provides seamless integration between dioxide's dependency injection
   container and FastAPI applications. It enables:

   - **Single middleware setup**: ``app.add_middleware(DioxideMiddleware, profile=...)``
   - **Request scoping**: Automatic ``ScopedContainer`` per HTTP request
   - **Clean injection**: ``Inject(Type)`` wrapper for FastAPI's ``Depends()``
   - **Lifecycle management**: Container start/stop with FastAPI lifespan

   Quick Start:
       Set up dioxide in your FastAPI app::

           from fastapi import FastAPI
           from dioxide import Profile
           from dioxide.fastapi import DioxideMiddleware, Inject

           app = FastAPI()
           app.add_middleware(DioxideMiddleware, profile=Profile.PRODUCTION)


           @app.get('/users/me')
           async def get_me(ctx: RequestContext = Inject(RequestContext)):
               return {'request_id': str(ctx.request_id)}


           @app.get('/users')
           async def list_users(service: UserService = Inject(UserService)):
               return await service.list_all()

   Request Scoping:
       The middleware creates a ``ScopedContainer`` for each HTTP request.
       This enables REQUEST-scoped components to be shared within a single
       request but fresh for each new request::

           from dioxide import service, Scope


           @service(scope=Scope.REQUEST)
           class RequestContext:
               def __init__(self):
                   import uuid

                   self.request_id = str(uuid.uuid4())


           # In route handlers:
           @app.get('/test')
           async def test(ctx: RequestContext = Inject(RequestContext)):
               # ctx.request_id is unique per request
               # but shared if resolved multiple times within same request
               return {'request_id': ctx.request_id}

   Lifecycle Management:
       The middleware handles container lifecycle automatically::

           from dioxide import adapter, lifecycle, Profile


           @adapter.for_(DatabasePort, profile=Profile.PRODUCTION)
           @lifecycle
           class PostgresAdapter:
               async def initialize(self) -> None:
                   self.engine = create_engine(...)
                   print('Database connected')

               async def dispose(self) -> None:
                   await self.engine.dispose()
                   print('Database disconnected')


           # When FastAPI starts: container.start() initializes adapters
           # When FastAPI stops: container.stop() disposes adapters

   .. seealso::

      - :class:`DioxideMiddleware` - The main integration middleware
      - :func:`Inject` - Dependency injection helper for route handlers
      - :class:`dioxide.container.Container` - The DI container
      - :class:`dioxide.container.ScopedContainer` - Request-scoped container



Classes
-------

.. autoapisummary::

   dioxide.fastapi.DioxideMiddleware


Functions
---------

.. autoapisummary::

   dioxide.fastapi.Inject


Module Contents
---------------

.. py:class:: DioxideMiddleware(app, profile = None, container = None, packages = None)

   ASGI middleware that integrates dioxide with FastAPI.

   This middleware handles both:

   1. **Lifecycle management**: Container ``start()``/``stop()`` via ASGI lifespan
   2. **Request scoping**: Creates ``ScopedContainer`` per HTTP request

   The middleware intercepts ASGI events:

   - ``lifespan``: Scans components and starts/stops the container
   - ``http``: Creates a scoped container for each request

   Usage:
       Basic setup with profile::

           from fastapi import FastAPI
           from dioxide import Profile
           from dioxide.fastapi import DioxideMiddleware

           app = FastAPI()
           app.add_middleware(DioxideMiddleware, profile=Profile.PRODUCTION)

       With custom container::

           from dioxide import Container, Profile
           from dioxide.fastapi import DioxideMiddleware

           my_container = Container()
           app = FastAPI()
           app.add_middleware(
               DioxideMiddleware,
               container=my_container,
               profile=Profile.TEST,
           )

       With package scanning::

           app.add_middleware(
               DioxideMiddleware,
               profile=Profile.PRODUCTION,
               packages=['myapp.services', 'myapp.adapters'],
           )

   :param app: The ASGI application to wrap
   :param profile: Profile to scan with (e.g., ``Profile.PRODUCTION``)
   :param container: Optional Container instance. If not provided, uses
                     the global ``dioxide.container`` singleton.
   :param packages: Optional list of packages to scan for components.

   .. seealso::

      - :func:`Inject` - How to inject dependencies in routes
      - :class:`dioxide.container.ScopedContainer` - The scoped container


   .. py:attribute:: app


   .. py:attribute:: profile
      :value: None



   .. py:attribute:: container


   .. py:attribute:: packages
      :value: None



   .. py:method:: __call__(scope, receive, send)
      :async:


      Process an ASGI request.

      Handles three ASGI scope types:

      - ``lifespan``: Manages container startup/shutdown
      - ``http``: Creates ScopedContainer per request
      - Other types: Passes through unchanged

      :param scope: ASGI scope dictionary
      :param receive: ASGI receive callable
      :param send: ASGI send callable



.. py:function:: Inject(component_type)

   Create a FastAPI dependency that resolves from dioxide container.

   This function wraps FastAPI's ``Depends()`` to resolve dependencies
   from the dioxide container. It automatically uses the correct scope:

   - **SINGLETON**: Resolved from parent container (shared)
   - **REQUEST**: Resolved from request scope (fresh per request)
   - **FACTORY**: New instance each resolution

   :param component_type: The type to resolve from the container

   :returns: A FastAPI ``Depends()`` object that resolves the component

   .. admonition:: Example

      Basic usage::

          from dioxide.fastapi import Inject


          @app.get('/users')
          async def list_users(service: UserService = Inject(UserService)):
              return await service.list_all()

      Multiple dependencies::

          @app.get('/dashboard')
          async def dashboard(
              users: UserService = Inject(UserService),
              analytics: AnalyticsService = Inject(AnalyticsService),
          ):
              return {
                  'users': await users.count(),
                  'visits': await analytics.total_visits(),
              }

      Request-scoped dependencies::

          from dioxide import service, Scope


          @service(scope=Scope.REQUEST)
          class RequestContext:
              def __init__(self):
                  self.request_id = str(uuid.uuid4())


          @app.get('/test')
          async def test(ctx: RequestContext = Inject(RequestContext)):
              # ctx is unique per request
              return {'request_id': ctx.request_id}

   :raises RuntimeError: If called without ``DioxideMiddleware`` being configured

   .. note::

      The function name is capitalized (``Inject``) to match the convention
      of FastAPI's ``Depends``, ``Query``, ``Body``, etc.

   .. seealso::

      - :class:`DioxideMiddleware` - Must be added first
      - :class:`dioxide.container.ScopedContainer` - How scoping works
