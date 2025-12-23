dioxide.celery
==============

.. py:module:: dioxide.celery

.. autoapi-nested-parse::

   Celery integration for dioxide dependency injection.

   This module provides seamless integration between dioxide's dependency injection
   container and Celery background tasks. It enables:

   - **Single function setup**: ``configure_dioxide(app, profile=...)``
   - **Task scoping**: Automatic ``ScopedContainer`` per task execution via ``scoped_task``
   - **Lifecycle management**: Container start/stop tied to Celery app configuration

   Quick Start:
       Set up dioxide in your Celery app::

           from celery import Celery
           from dioxide import Profile
           from dioxide.celery import configure_dioxide, scoped_task

           app = Celery('tasks')
           configure_dioxide(app, profile=Profile.PRODUCTION)


           @scoped_task(app)
           def process_order(scope, order_id: str) -> dict:
               service = scope.resolve(OrderService)
               return service.process(order_id)


           # Execute task
           result = process_order.delay('order-123')

   Task Scoping:
       The integration creates a ``ScopedContainer`` for each task execution.
       This enables REQUEST-scoped components to be fresh for each task::

           from dioxide import service, Scope


           @service(scope=Scope.REQUEST)
           class TaskContext:
               def __init__(self):
                   import uuid

                   self.task_id = str(uuid.uuid4())


           # In task handlers:
           @scoped_task(app)
           def my_task(scope) -> str:
               ctx = scope.resolve(TaskContext)
               # ctx.task_id is unique per task execution
               return ctx.task_id

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
           # When task ends: scope.dispose() for REQUEST-scoped components

   Thread Safety:
       Celery uses processes/threads for task execution. The integration creates
       a fresh scope per task execution, ensuring each task gets its own isolated
       REQUEST-scoped dependencies. SINGLETON-scoped components are shared across
       tasks within the same worker process.

   .. seealso::

      - :func:`configure_dioxide` - The main setup function
      - :func:`scoped_task` - Decorator for task scoping
      - :class:`dioxide.container.Container` - The DI container
      - :class:`dioxide.container.ScopedContainer` - Task-scoped container



Functions
---------

.. autoapisummary::

   dioxide.celery.configure_dioxide
   dioxide.celery.scoped_task


Module Contents
---------------

.. py:function:: configure_dioxide(app, profile = None, container = None, packages = None)

   Configure dioxide dependency injection for a Celery application.

   This function sets up the integration between dioxide and Celery:

   1. Scans for components in specified packages (or all registered)
   2. Starts the container (initializing @lifecycle components)
   3. Stores the container reference on the Celery app

   :param app: The Celery application instance
   :param profile: Profile to scan with (e.g., ``Profile.PRODUCTION``). Accepts
                   either a Profile enum value or a string profile name.
   :param container: Optional Container instance. If not provided, uses the
                     global ``dioxide.container`` singleton.
   :param packages: Optional list of packages to scan for components. If not
                    provided, scans all registered components.

   :raises ImportError: If Celery is not installed.

   .. admonition:: Example

      Basic setup::

          from celery import Celery
          from dioxide import Profile
          from dioxide.celery import configure_dioxide

          app = Celery('tasks')
          configure_dioxide(app, profile=Profile.PRODUCTION)

      With custom container::

          from dioxide import Container, Profile
          from dioxide.celery import configure_dioxide

          my_container = Container()
          app = Celery('tasks')
          configure_dioxide(app, profile=Profile.TEST, container=my_container)

      With package scanning::

          configure_dioxide(
              app,
              profile=Profile.PRODUCTION,
              packages=['myapp.services', 'myapp.adapters'],
          )

   .. seealso::

      - :func:`scoped_task` - How to create scoped tasks
      - :class:`dioxide.container.ScopedContainer` - How scoping works


.. py:function:: scoped_task(app, **task_options)

   Decorator to create a Celery task with dioxide scoping.

   Creates a Celery task that automatically receives a ScopedContainer
   as its first argument. The scope is created before task execution
   and disposed after completion (including on errors).

   :param app: The Celery application instance (must be configured with configure_dioxide)
   :param \*\*task_options: Additional options to pass to Celery's @app.task decorator
                            (e.g., name, bind, queue, etc.)

   :returns: A decorator function that wraps the task with scoping.

   .. admonition:: Example

      Basic usage::

          from dioxide.celery import configure_dioxide, scoped_task

          app = Celery('tasks')
          configure_dioxide(app, profile=Profile.PRODUCTION)


          @scoped_task(app)
          def process_order(scope, order_id: str) -> dict:
              service = scope.resolve(OrderService)
              return service.process(order_id)


          # Execute task
          result = process_order.delay('order-123')

      With Celery task options::

          @scoped_task(app, name='custom.task.name', queue='high-priority')
          def important_task(scope) -> None:
              pass

      Async task::

          @scoped_task(app)
          async def async_task(scope) -> str:
              ctx = scope.resolve(TaskContext)
              await asyncio.sleep(0.1)
              return ctx.task_id

   .. note::

      - The scope is always injected as the FIRST argument
      - REQUEST-scoped components are fresh per task execution
      - SINGLETON-scoped components are shared across tasks in the same worker
      - @lifecycle components with REQUEST scope are disposed after task completion

   .. seealso::

      - :func:`configure_dioxide` - Must be called first
      - :class:`dioxide.container.ScopedContainer` - How scoping works
