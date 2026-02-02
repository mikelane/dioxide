CaptiveDependencyError
======================

.. contents::
   :local:
   :depth: 2

Overview
--------

``CaptiveDependencyError`` is raised during ``container.scan()`` when a SINGLETON
component depends on a REQUEST-scoped component.

This is called a "captive dependency" because the REQUEST component would be
"captured" by the SINGLETON and never refreshed, defeating the purpose of
request scoping.

Example Error
-------------

.. code-block:: text

   Captive Dependency: Captive dependency: GlobalService (SINGLETON) -> RequestContext (REQUEST)
     SINGLETON cannot depend on REQUEST-scoped components

   Context:
     - parent: GlobalService
     - parent_scope: SINGLETON
     - child: RequestContext
     - child_scope: REQUEST

   -> See: https://dioxide.readthedocs.io/en/stable/troubleshooting/captive-dependency.html

Why This Is a Problem
---------------------

- **SINGLETON** lives for the container's lifetime (application lifetime)
- **REQUEST** should be fresh for each request/scope
- If SINGLETON holds REQUEST, the **same REQUEST instance is reused forever**
- This violates the REQUEST scope contract and causes subtle bugs

Example
-------

.. code-block:: python

   from dioxide import service, Scope, Container, Profile

   @service(scope=Scope.REQUEST)
   class RequestContext:
       def __init__(self):
           self.request_id = generate_id()  # Should be unique per request

   @service  # SINGLETON (default)
   class GlobalService:
       def __init__(self, ctx: RequestContext):  # BAD: SINGLETON -> REQUEST
           self.ctx = ctx  # This REQUEST instance is captured forever!

   container = Container(profile=Profile.PRODUCTION)
   # CaptiveDependencyError raised during scan!

Valid vs Invalid Scope Dependencies
-----------------------------------

.. list-table::
   :header-rows: 1
   :widths: 40 20 40

   * - Dependency
     - Valid?
     - Reason
   * - SINGLETON -> SINGLETON
     - Yes
     - Same lifetime
   * - SINGLETON -> FACTORY
     - Yes
     - Creates new instance each time
   * - **SINGLETON -> REQUEST**
     - **No**
     - **Captive dependency**
   * - REQUEST -> SINGLETON
     - Yes
     - Shorter uses longer
   * - REQUEST -> REQUEST
     - Yes
     - Same scope
   * - REQUEST -> FACTORY
     - Yes
     - Creates new instance each time
   * - FACTORY -> any
     - Yes
     - Always creates new

Solutions
---------

1. Change Parent to REQUEST Scope
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Make the parent service REQUEST-scoped too:

.. code-block:: python

   @service(scope=Scope.REQUEST)  # Changed to REQUEST
   class RequestService:
       def __init__(self, ctx: RequestContext):
           self.ctx = ctx  # Now both are REQUEST-scoped

2. Change Child to SINGLETON Scope
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If the child doesn't truly need request scope:

.. code-block:: python

   @service  # Changed to SINGLETON (default)
   class SharedContext:
       """Doesn't actually need per-request state."""
       ...

3. Use Factory/Provider Pattern
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Get fresh instances when needed:

.. code-block:: python

   @service  # SINGLETON
   class GlobalService:
       def __init__(self, container: Container):
           self.container = container

       def get_context(self) -> RequestContext:
           """Get fresh context from current scope."""
           # Caller must be in a scope for this to work
           return self.container.resolve(RequestContext)

4. Inject a Factory
~~~~~~~~~~~~~~~~~~~

Inject a callable that creates the dependency:

.. code-block:: python

   from typing import Callable

   @service  # SINGLETON
   class GlobalService:
       def __init__(self, context_factory: Callable[[], RequestContext]):
           self.context_factory = context_factory

       def process(self):
           ctx = self.context_factory()  # Fresh instance each call
           ...

Best Practices
--------------

1. **Review scope assignments**: Ensure scopes match component lifetimes
2. **Fail fast**: Error at ``scan()`` time prevents runtime surprises
3. **Draw dependency graph**: Visualize scope relationships
4. **Default to REQUEST for request-specific data**: User context, request ID, etc.
5. **Use SINGLETON for truly shared state**: Config, connection pools, caches

Debugging Tips
--------------

1. **Check the error context**: It shows parent and child scopes
2. **Review scope assignments**: Is the parent really SINGLETON? Is the child really REQUEST?
3. **Consider if REQUEST is needed**: Maybe FACTORY would work instead
4. **Consider if SINGLETON is needed**: Maybe REQUEST would work for the parent

See Also
--------

- :doc:`/guides/scoping` - Complete guide to scopes
- :doc:`scope-error` - Related scope error
- :doc:`/user_guide/container_patterns` - Container usage patterns
