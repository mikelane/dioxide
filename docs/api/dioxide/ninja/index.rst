dioxide.ninja
=============

.. py:module:: dioxide.ninja

.. autoapi-nested-parse::

   Django Ninja integration for dioxide dependency injection.

   This module provides seamless integration between dioxide's dependency injection
   container and Django Ninja applications. It enables:

   - **Single function setup**: ``configure_dioxide(api, profile=...)``
   - **Request scoping**: Automatic ``ScopedContainer`` per HTTP request via middleware
   - **Clean injection**: ``inject(Type)`` resolves from current request scope
   - **Lifecycle management**: Container start/stop tied to Django configuration

   Quick Start:
       Set up dioxide in your Django Ninja app::

           from ninja import NinjaAPI
           from dioxide import Profile
           from dioxide.ninja import configure_dioxide, inject

           api = NinjaAPI()
           configure_dioxide(api, profile=Profile.PRODUCTION)


           @api.get('/users/me')
           def get_me(request):
               ctx = inject(RequestContext)
               return {'request_id': str(ctx.request_id)}


           @api.get('/users')
           def list_users(request):
               service = inject(UserService)
               return service.list_all()

       Add the middleware to your Django settings::

           MIDDLEWARE = [
               ...
               'dioxide.ninja.DioxideMiddleware',
               ...
           ]

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
           @api.get('/test')
           def test(request):
               ctx = inject(RequestContext)
               # ctx.request_id is unique per request
               # but shared if resolved multiple times within same request
               return {'request_id': ctx.request_id}

   Lifecycle Management:
       The integration handles container lifecycle automatically::

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


           # When configure_dioxide is called: container.scan() and start()
           # When request ends: scope.dispose() for REQUEST-scoped components

   Thread Safety:
       Django uses threading by default. The integration stores the scoped container
       in thread-local storage, ensuring each request gets its own scope even in
       threaded mode.

   .. note::

      Unlike FastAPI which has built-in dependency injection via ``Depends()``,
      Django Ninja uses Django's request handling model. This integration follows
      the same pattern as ``dioxide.django``, using middleware for request scoping
      and ``inject()`` for resolving dependencies inside route handlers.

   .. seealso::

      - :func:`configure_dioxide` - The main setup function
      - :class:`DioxideMiddleware` - Request scoping middleware
      - :func:`inject` - Dependency injection helper for route handlers
      - :class:`dioxide.container.Container` - The DI container
      - :class:`dioxide.container.ScopedContainer` - Request-scoped container



Classes
-------

.. autoapisummary::

   dioxide.ninja.DioxideMiddleware


Functions
---------

.. autoapisummary::

   dioxide.ninja.configure_dioxide
   dioxide.ninja.inject


Module Contents
---------------

.. py:function:: configure_dioxide(api, profile = None, container = None, packages = None)

   Configure dioxide dependency injection for a Django Ninja application.

   This function sets up the integration between dioxide and Django Ninja:

   1. Scans for components in specified packages (or all registered)
   2. Starts the container (initializing @lifecycle components)
   3. Stores the container reference for later access by middleware and inject()

   Call this during Django application startup (settings.py, apps.py ready(),
   or wherever you create your NinjaAPI instance).

   :param api: The NinjaAPI instance to configure. Currently unused but included
               for API consistency and potential future use.
   :param profile: Profile to scan with (e.g., ``Profile.PRODUCTION``). Accepts
                   either a Profile enum value or a string profile name.
   :param container: Optional Container instance. If not provided, uses the
                     global ``dioxide.container`` singleton.
   :param packages: Optional list of packages to scan for components. If not
                    provided, scans all registered components.

   :raises ImportError: If Django Ninja is not installed.

   .. admonition:: Example

      Basic setup::

          from ninja import NinjaAPI
          from dioxide import Profile
          from dioxide.ninja import configure_dioxide

          api = NinjaAPI()
          configure_dioxide(api, profile=Profile.PRODUCTION)

      With custom container::

          from dioxide import Container, Profile
          from dioxide.ninja import configure_dioxide

          my_container = Container()
          api = NinjaAPI()
          configure_dioxide(api, profile=Profile.TEST, container=my_container)

      With package scanning::

          configure_dioxide(
              api,
              profile=Profile.PRODUCTION,
              packages=['myapp.services', 'myapp.adapters'],
          )

   .. note::

      You must also add ``DioxideMiddleware`` to your Django ``MIDDLEWARE``
      setting for request scoping to work.

   .. seealso::

      - :class:`DioxideMiddleware` - Must be added to MIDDLEWARE
      - :func:`inject` - How to inject dependencies in route handlers
      - :class:`dioxide.container.ScopedContainer` - How scoping works


.. py:class:: DioxideMiddleware(get_response)

   Django middleware that creates a ScopedContainer per request.

   This middleware handles request scoping for dioxide:

   1. Creates a ``ScopedContainer`` before the view runs
   2. Stores it in thread-local storage for ``inject()`` to access
   3. Disposes the scope after the response is returned

   Usage in settings.py::

       MIDDLEWARE = [
           ...
           'dioxide.ninja.DioxideMiddleware',
           ...
       ]

   .. note::

      The middleware must be placed after any middleware that might need
      dioxide services, as it creates the scope on request entry.

   .. seealso::

      - :func:`configure_dioxide` - Must be called first
      - :func:`inject` - How to inject dependencies in route handlers
      - :class:`dioxide.container.ScopedContainer` - The scoped container


   .. py:attribute:: get_response


   .. py:method:: __call__(request)

      Process a request with dioxide scoping.

      Creates a scoped container for the request, stores it in thread-local
      storage, calls the view, and ensures cleanup on completion.

      :param request: The Django HttpRequest object.

      :returns: The HttpResponse from the view.



.. py:function:: inject(component_type)

   Resolve a component from the current request's dioxide scope.

   This function retrieves a dependency from the dioxide container for
   the current request. It automatically uses the correct scope:

   - **SINGLETON**: Resolved from parent container (shared)
   - **REQUEST**: Resolved from request scope (fresh per request)
   - **FACTORY**: New instance each resolution

   :param component_type: The type to resolve from the container

   :returns: An instance of the requested type

   :raises RuntimeError: If called outside a request context
   :raises RuntimeError: If called without ``configure_dioxide()`` being set up
   :raises ImportError: If Django Ninja is not installed

   .. admonition:: Example

      Basic usage::

          from dioxide.ninja import inject


          @api.get('/users')
          def list_users(request):
              service = inject(UserService)
              return service.list_all()

      Multiple dependencies::

          @api.get('/dashboard')
          def dashboard(request):
              users = inject(UserService)
              analytics = inject(AnalyticsService)
              return {
                  'users': users.count(),
                  'visits': analytics.total_visits(),
              }

      Request-scoped dependencies::

          from dioxide import service, Scope


          @service(scope=Scope.REQUEST)
          class RequestContext:
              def __init__(self):
                  self.request_id = str(uuid.uuid4())


          @api.get('/test')
          def test(request):
              ctx = inject(RequestContext)
              # ctx is unique per request
              return {'request_id': ctx.request_id}

   .. note::

      This function uses ``inject()`` (lowercase) to match Django's naming
      conventions and the existing ``dioxide.django`` integration. This is
      different from FastAPI's ``Inject()`` pattern because Django Ninja
      doesn't have built-in dependency injection like FastAPI's ``Depends``.

   .. seealso::

      - :func:`configure_dioxide` - Must be called first
      - :class:`DioxideMiddleware` - Must be added to MIDDLEWARE
      - :class:`dioxide.container.ScopedContainer` - How scoping works
