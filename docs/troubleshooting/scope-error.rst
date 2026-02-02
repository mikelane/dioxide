ScopeError
==========

.. contents::
   :local:
   :depth: 2

Overview
--------

``ScopeError`` is raised when scope-related operations fail, most commonly:

1. Resolving a REQUEST-scoped component outside of a scope context
2. Attempting to create nested scopes (not supported)
3. Other scope lifecycle violations

Example Error
-------------

.. code-block:: text

   Scope Error: Cannot resolve RequestContext: REQUEST-scoped, requires active scope

   Context:
     - component: RequestContext
     - required_scope: REQUEST

   -> See: https://dioxide.readthedocs.io/en/stable/troubleshooting/scope-error.html

What Causes This
----------------

REQUEST-scoped components need an active scope created via ``container.create_scope()``.
Resolving them from the parent container fails.

Example
-------

.. code-block:: python

   from dioxide import service, Scope, Container, Profile

   @service(scope=Scope.REQUEST)
   class RequestContext:
       def __init__(self):
           self.request_id = generate_id()

   container = Container(profile=Profile.PRODUCTION)
   container.resolve(RequestContext)  # ScopeError! No active scope

Solution
--------

Create a scope before resolving REQUEST-scoped components:

.. code-block:: python

   async with container.create_scope() as scope:
       ctx = scope.resolve(RequestContext)  # Works!
       # ctx is unique to this scope
       print(ctx.request_id)

Where to Create Scopes
----------------------

Create scopes at application entry points:

Web Request Handler
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   @app.route("/users")
   async def list_users():
       async with container.create_scope() as scope:
           service = scope.resolve(UserService)
           return await service.list_users()

CLI Command
~~~~~~~~~~~

.. code-block:: python

   @click.command()
   async def my_command():
       async with container.create_scope() as scope:
           service = scope.resolve(DataProcessor)
           await service.run()

Background Task
~~~~~~~~~~~~~~~

.. code-block:: python

   async def process_job(job_id: str):
       async with container.create_scope() as scope:
           service = scope.resolve(JobProcessor)
           await service.process(job_id)

Nested Scopes
-------------

.. warning::

   Nested scopes are not supported. Attempting to create a scope within a scope
   will raise ``ScopeError``.

.. code-block:: python

   async with container.create_scope() as outer:
       async with outer.create_scope() as inner:  # ScopeError!
           ...

If you need isolated contexts within a scope, use separate container instances
or restructure your dependencies.

Best Practices
--------------

1. **Create scope at entry points**: Web handlers, CLI commands, background tasks
2. **One scope per request**: Don't nest scopes; use one scope per logical request
3. **Pass scope to dependencies**: Let the container inject scoped dependencies
4. **Use async context manager**: ``async with container.create_scope() as scope:``

Understanding Scopes
--------------------

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Scope
     - Behavior
   * - SINGLETON (default)
     - One instance for the container's lifetime
   * - FACTORY
     - New instance on every resolution
   * - REQUEST
     - One instance per scope, disposed when scope exits

See Also
--------

- :doc:`/guides/scoping` - Complete guide to scopes
- :doc:`captive-dependency` - Related scope error
- :doc:`/user_guide/container_patterns` - Container usage patterns
