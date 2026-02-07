Troubleshooting
===============

This section covers common errors you may encounter when using dioxide and how to resolve them.

.. tip::

   dioxide is designed to **fail fast** - errors are caught at startup, not at runtime.
   This means you'll see these errors during development, not in production.

Errors
------

.. toctree::
   :maxdepth: 1

   adapter-not-found
   service-not-found
   circular-dependency
   scope-error
   captive-dependency

Warnings
--------

.. toctree::
   :maxdepth: 1

   side-effect-warning

Quick Diagnosis
---------------

Use this table to identify your error:

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - Error Message
     - Likely Cause
   * - "No adapter for X in profile 'Y'"
     - Missing ``@adapter.for_(X, profile=Y)`` decorator
   * - "Cannot resolve X in profile 'Y'"
     - Missing ``@service`` decorator or unregistered dependency
   * - "Circular dependency detected"
     - Two or more ``@lifecycle`` components depend on each other
   * - "REQUEST-scoped, requires active scope"
     - Resolving REQUEST component without ``container.create_scope()``
   * - "Captive dependency: X (SINGLETON) -> Y (REQUEST)"
     - SINGLETON depending on shorter-lived REQUEST component
   * - "SideEffectWarning: Module 'X' contains potential side effects"
     - Module-level function calls detected during ``scan(strict=True)``

General Troubleshooting Steps
-----------------------------

1. **Check your decorators**

   - Services need ``@service``
   - Adapters need ``@adapter.for_(Port, profile=...)``
   - Lifecycle components need ``@lifecycle``

2. **Check your profile**

   - Verify ``Container(profile=...)`` matches your adapter profiles
   - Use ``Profile.ALL`` for universal adapters

3. **Check import order**

   - Decorators execute at import time
   - Ensure modules are imported before container scans

4. **Check type hints**

   - Constructor parameters must have type hints
   - Type hints must reference registered types

5. **Use explicit package scanning**

   .. code-block:: python

      container = Container(profile=Profile.PRODUCTION)
      container.scan(package="myapp.adapters")

Getting Help
------------

If you're still stuck:

1. Check the `GitHub Issues <https://github.com/mikelane/dioxide/issues>`_ for similar problems
2. Open a new issue with:

   - The full error message
   - Minimal code to reproduce
   - Your dioxide version (``pip show dioxide``)
