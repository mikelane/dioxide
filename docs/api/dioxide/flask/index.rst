dioxide.flask
=============

.. py:module:: dioxide.flask

.. autoapi-nested-parse::

   Flask integration for dioxide dependency injection.

   This module provides seamless integration between dioxide's dependency injection
   container and Flask applications. It enables:

   - **Single function setup**: ``configure_dioxide(app, profile=...)``
   - **Request scoping**: Automatic ``ScopedContainer`` per HTTP request via Flask's ``g``
   - **Clean injection**: ``inject(Type)`` resolves from current request scope
   - **Lifecycle management**: Container start/stop tied to Flask app configuration

   Quick Start:
       Set up dioxide in your Flask app::

           from flask import Flask
           from dioxide import Profile
           from dioxide.flask import configure_dioxide, inject

           app = Flask(__name__)
           configure_dioxide(app, profile=Profile.PRODUCTION)


           @app.route('/users/me')
           def get_me():
               ctx = inject(RequestContext)
               return {'request_id': str(ctx.request_id)}


           @app.route('/users')
           def list_users():
               service = inject(UserService)
               return service.list_all()

   Request Scoping:
       The integration creates a ``ScopedContainer`` for each HTTP request.
       This enables REQUEST-scoped components to be shared within a single
       request but fresh for each new request::

           from dioxide import service, Scope


           @service(scope=Scope.REQUEST)
           class RequestContext:
               def __init__(self):
                   import uuid

                   self.request_id = str(uuid.uuid4())


           # In route handlers:
           @app.route('/test')
           def test():
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
       Flask uses threading by default. The integration stores the scoped container
       in Flask's ``g`` object, which is thread-local, ensuring each request gets
       its own scope even in threaded mode.

   .. seealso::

      - :func:`configure_dioxide` - The main setup function
      - :func:`inject` - Dependency injection helper for route handlers
      - :class:`dioxide.container.Container` - The DI container
      - :class:`dioxide.container.ScopedContainer` - Request-scoped container



Functions
---------

.. autoapisummary::

   dioxide.flask.configure_dioxide
   dioxide.flask.inject


Module Contents
---------------

.. py:function:: configure_dioxide(app, profile = None, container = None, packages = None)

   Configure dioxide dependency injection for a Flask application.

   This function sets up the integration between dioxide and Flask:

   1. Scans for components in specified packages (or all registered)
   2. Starts the container (initializing @lifecycle components)
   3. Registers request hooks for per-request scoping
   4. Stores the container in app.config for later access

   :param app: The Flask application instance
   :param profile: Profile to scan with (e.g., ``Profile.PRODUCTION``). Accepts
                   either a Profile enum value or a string profile name.
   :param container: Optional Container instance. If not provided, uses the
                     global ``dioxide.container`` singleton.
   :param packages: Optional list of packages to scan for components. If not
                    provided, scans all registered components.

   :raises ImportError: If Flask is not installed.

   .. admonition:: Example

      Basic setup::

          from flask import Flask
          from dioxide import Profile
          from dioxide.flask import configure_dioxide

          app = Flask(__name__)
          configure_dioxide(app, profile=Profile.PRODUCTION)

      With custom container::

          from dioxide import Container, Profile
          from dioxide.flask import configure_dioxide

          my_container = Container()
          app = Flask(__name__)
          configure_dioxide(app, profile=Profile.TEST, container=my_container)

      With package scanning::

          configure_dioxide(
              app,
              profile=Profile.PRODUCTION,
              packages=['myapp.services', 'myapp.adapters'],
          )

      App factory pattern::

          def create_app():
              app = Flask(__name__)
              configure_dioxide(app, profile=Profile.PRODUCTION)
              return app

   .. seealso::

      - :func:`inject` - How to inject dependencies in routes
      - :class:`dioxide.container.ScopedContainer` - How scoping works


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
   :raises ImportError: If Flask is not installed

   .. admonition:: Example

      Basic usage::

          from dioxide.flask import inject


          @app.route('/users')
          def list_users():
              service = inject(UserService)
              return service.list_all()

      Multiple dependencies::

          @app.route('/dashboard')
          def dashboard():
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


          @app.route('/test')
          def test():
              ctx = inject(RequestContext)
              # ctx is unique per request
              return {'request_id': ctx.request_id}

   .. note::

      Unlike FastAPI's ``Inject()`` which returns a Depends wrapper,
      Flask's ``inject()`` directly returns the resolved instance.
      This is because Flask doesn't have a dependency injection system
      like FastAPI's Depends.

   .. seealso::

      - :func:`configure_dioxide` - Must be called first
      - :class:`dioxide.container.ScopedContainer` - How scoping works
