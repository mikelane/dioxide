dioxide.django
==============

.. py:module:: dioxide.django

.. autoapi-nested-parse::

   Django integration for dioxide dependency injection.

   This module provides seamless integration between dioxide's dependency injection
   container and Django applications. It enables:

   - **Single function setup**: ``configure_dioxide(profile=...)``
   - **Request scoping**: Automatic ``ScopedContainer`` per HTTP request via middleware
   - **Clean injection**: ``inject(Type)`` resolves from current request scope
   - **Lifecycle management**: Container start/stop tied to Django configuration

   Quick Start:
       Set up dioxide in your Django settings.py or apps.py::

           # In settings.py or your AppConfig.ready()
           from dioxide import Profile
           from dioxide.django import configure_dioxide

           configure_dioxide(profile=Profile.PRODUCTION)

       Add the middleware to settings.py::

           MIDDLEWARE = [
               ...
               'dioxide.django.DioxideMiddleware',
               ...
           ]

       Use in views::

           from dioxide.django import inject


           def my_view(request):
               service = inject(UserService)
               return JsonResponse(service.get_data())

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


           # In views:
           def my_view(request):
               ctx = inject(RequestContext)
               # ctx.request_id is unique per request
               # but shared if resolved multiple times within same request
               return JsonResponse({'request_id': ctx.request_id})

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

   .. seealso::

      - :func:`configure_dioxide` - The main setup function
      - :class:`DioxideMiddleware` - Request scoping middleware
      - :func:`inject` - Dependency injection helper for views
      - :class:`dioxide.container.Container` - The DI container
      - :class:`dioxide.container.ScopedContainer` - Request-scoped container



Classes
-------

.. autoapisummary::

   dioxide.django.DioxideMiddleware


Functions
---------

.. autoapisummary::

   dioxide.django.configure_dioxide
   dioxide.django.inject


Module Contents
---------------

.. py:function:: configure_dioxide(profile = None, container = None, packages = None)

   Configure dioxide dependency injection for a Django application.

   This function sets up the integration between dioxide and Django:

   1. Scans for components in specified packages (or all registered)
   2. Starts the container (initializing @lifecycle components)
   3. Stores the container reference for later access by middleware

   Call this in your Django settings.py, apps.py ready(), or conftest.py.

   :param profile: Profile to scan with (e.g., ``Profile.PRODUCTION``). Accepts
                   either a Profile enum value or a string profile name.
   :param container: Optional Container instance. If not provided, uses the
                     global ``dioxide.container`` singleton.
   :param packages: Optional list of packages to scan for components. If not
                    provided, scans all registered components.

   :raises ImportError: If Django is not installed.

   .. admonition:: Example

      Basic setup in settings.py::

          from dioxide import Profile
          from dioxide.django import configure_dioxide

          configure_dioxide(profile=Profile.PRODUCTION)

      In apps.py ready() method::

          from django.apps import AppConfig
          from dioxide import Profile
          from dioxide.django import configure_dioxide


          class MyAppConfig(AppConfig):
              name = 'myapp'

              def ready(self):
                  configure_dioxide(profile=Profile.PRODUCTION)

      With custom container::

          from dioxide import Container, Profile
          from dioxide.django import configure_dioxide

          my_container = Container()
          configure_dioxide(profile=Profile.TEST, container=my_container)

      With package scanning::

          configure_dioxide(
              profile=Profile.PRODUCTION,
              packages=['myapp.services', 'myapp.adapters'],
          )

   .. seealso::

      - :class:`DioxideMiddleware` - Must be added to MIDDLEWARE
      - :func:`inject` - How to inject dependencies in views
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
           'dioxide.django.DioxideMiddleware',
           ...
       ]

   .. note::

      The middleware must be placed after any middleware that might need
      dioxide services, as it creates the scope on request entry.

   .. seealso::

      - :func:`configure_dioxide` - Must be called first
      - :func:`inject` - How to inject dependencies in views
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
   :raises ImportError: If Django is not installed

   .. admonition:: Example

      Basic usage::

          from dioxide.django import inject


          def my_view(request):
              service = inject(UserService)
              return JsonResponse(service.get_data())

      Multiple dependencies::

          def dashboard_view(request):
              users = inject(UserService)
              analytics = inject(AnalyticsService)
              return JsonResponse(
                  {
                      'users': users.count(),
                      'visits': analytics.total_visits(),
                  }
              )

      Request-scoped dependencies::

          from dioxide import service, Scope


          @service(scope=Scope.REQUEST)
          class RequestContext:
              def __init__(self):
                  self.request_id = str(uuid.uuid4())


          def my_view(request):
              ctx = inject(RequestContext)
              # ctx is unique per request
              return JsonResponse({'request_id': ctx.request_id})

   .. note::

      Unlike FastAPI's ``Inject()`` which returns a Depends wrapper,
      Django's ``inject()`` directly returns the resolved instance.
      This is because Django doesn't have a dependency injection system
      like FastAPI's Depends.

   .. seealso::

      - :func:`configure_dioxide` - Must be called first
      - :class:`DioxideMiddleware` - Must be added to MIDDLEWARE
      - :class:`dioxide.container.ScopedContainer` - How scoping works
