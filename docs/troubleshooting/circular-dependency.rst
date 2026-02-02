CircularDependencyError
=======================

.. contents::
   :local:
   :depth: 2

Overview
--------

``CircularDependencyError`` is raised when ``@lifecycle`` components have circular
dependencies that prevent the container from determining initialization order.

.. important::

   This error **only applies to @lifecycle components** during ``container.start()``.
   Regular services without ``@lifecycle`` can have circular dependencies (though not
   recommended) because they're instantiated lazily.

Example Error
-------------

.. code-block:: text

   Circular Dependency: Circular dependency detected

   Context:
     - unprocessed: {<ServiceA>, <ServiceB>}

   -> See: https://dioxide.readthedocs.io/en/stable/troubleshooting/circular-dependency.html

What Causes This
----------------

A circular dependency exists when components depend on each other in a loop:

.. code-block:: text

   ServiceA -> depends on -> ServiceB -> depends on -> ServiceA

The container cannot determine which component to initialize first because each
depends on another being already initialized.

Example
-------

.. code-block:: python

   from dioxide import service, lifecycle, Container, Profile

   @service
   @lifecycle
   class ServiceA:
       def __init__(self, b: 'ServiceB'):  # Depends on B
           self.b = b

       async def initialize(self) -> None:
           ...

       async def dispose(self) -> None:
           ...

   @service
   @lifecycle
   class ServiceB:
       def __init__(self, a: ServiceA):  # Depends on A - CYCLE!
           self.a = a

       async def initialize(self) -> None:
           ...

       async def dispose(self) -> None:
           ...

   container = Container(profile=Profile.PRODUCTION)
   await container.start()  # CircularDependencyError!

Types of Circular Dependencies
------------------------------

Direct Cycle
~~~~~~~~~~~~

Two components directly depend on each other:

.. code-block:: text

   A -> B -> A

Indirect Cycle
~~~~~~~~~~~~~~

A longer chain forms a loop:

.. code-block:: text

   A -> B -> C -> D -> A

Self-Dependency
~~~~~~~~~~~~~~~

A component depends on itself (rare):

.. code-block:: text

   A -> A

Solutions
---------

1. Break Dependency with Interface
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Instead of depending on a concrete class, depend on a port (Protocol):

.. code-block:: python

   from typing import Protocol

   class CachePort(Protocol):
       def get(self, key: str) -> Any: ...

   @service
   @lifecycle
   class ServiceA:
       def __init__(self, cache: CachePort):  # Depend on abstraction
           self.cache = cache

2. Remove @lifecycle from One Component
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If only one component truly needs lifecycle management:

.. code-block:: python

   @service  # No @lifecycle - lazy initialization
   class ServiceB:
       def __init__(self, a: ServiceA):
           self.a = a

   @service
   @lifecycle  # Only this one has lifecycle
   class ServiceA:
       async def initialize(self) -> None:
           ...

3. Lazy Resolution
~~~~~~~~~~~~~~~~~~

Defer resolution to first use:

.. code-block:: python

   @service
   @lifecycle
   class ServiceA:
       def __init__(self, container: Container):
           self.container = container
           self._b = None

       @property
       def b(self) -> ServiceB:
           if self._b is None:
               self._b = self.container.resolve(ServiceB)
           return self._b

4. Extract Shared Logic
~~~~~~~~~~~~~~~~~~~~~~~

Break the cycle by extracting shared logic to a third service:

.. code-block:: python

   @service
   class SharedLogic:
       """Contains logic both A and B need."""
       ...

   @service
   @lifecycle
   class ServiceA:
       def __init__(self, shared: SharedLogic):
           self.shared = shared

   @service
   @lifecycle
   class ServiceB:
       def __init__(self, shared: SharedLogic):
           self.shared = shared

Debugging Tips
--------------

1. **Identify the cycle**: Look at the "unprocessed" set in the error message
2. **Draw a dependency graph**: Visualize dependencies on paper
3. **Find the weakest link**: Identify which dependency is least essential
4. **Check @lifecycle usage**: Not all components need lifecycle management

Why This Error Exists
---------------------

``@lifecycle`` components need to be initialized in **dependency order**:

1. Dependencies must be initialized before dependents
2. During disposal, dependents must be disposed before dependencies
3. A cycle makes this impossible - there's no valid order

Without ``@lifecycle``, services are created lazily on-demand, so cycles don't
prevent instantiation (though they can cause ``RecursionError`` at runtime).

Best Practices
--------------

1. **Avoid circular dependencies**: Design for acyclic dependency graphs
2. **Use hexagonal architecture**: Depend on abstractions (ports) at boundaries
3. **Limit @lifecycle**: Only use for components that truly need init/dispose
4. **Single Responsibility**: Components with clear responsibilities rarely cycle
5. **Integration tests**: Test that ``container.start()`` succeeds

See Also
--------

- :doc:`/guides/lifecycle-async-patterns` - Lifecycle management patterns
- :doc:`/user_guide/hexagonal_architecture` - How to break dependencies
- :doc:`captive-dependency` - Related scope error
