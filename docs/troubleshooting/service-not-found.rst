ServiceNotFoundError
====================

.. contents::
   :local:
   :depth: 2

Overview
--------

``ServiceNotFoundError`` is raised when you try to resolve a service or component that:

1. Is not registered in the container (missing ``@service`` decorator), OR
2. Has dependencies that cannot be resolved, OR
3. Was not imported before ``container.scan()`` was called

Unlike :doc:`adapter-not-found` (for ports), this error applies to concrete classes
marked with ``@service``.

Example Error
-------------

.. code-block:: text

   Service Not Found: Cannot resolve UserService in profile 'production'
     Missing dependency: email: EmailPort (no adapter registered)

   Context:
     - service: UserService
     - profile: production
     - failed_dependency: {'param_name': 'email', 'param_type': 'EmailPort', 'reason': 'no adapter registered'}

   -> See: https://dioxide.readthedocs.io/en/stable/troubleshooting/service-not-found.html

Common Causes
-------------

Missing @service Decorator
~~~~~~~~~~~~~~~~~~~~~~~~~~

The class is not decorated, so it's not registered in the container.

.. code-block:: python

   # Missing @service decorator!
   class UserService:
       def create_user(self, name: str):
           ...

   container = Container(profile=Profile.PRODUCTION)
   container.resolve(UserService)  # ServiceNotFoundError!

**Solution**: Add the ``@service`` decorator:

.. code-block:: python

   from dioxide import service

   @service
   class UserService:
       def create_user(self, name: str):
           ...

Unresolvable Dependency
~~~~~~~~~~~~~~~~~~~~~~~

The service has a dependency that isn't registered.

.. code-block:: python

   @service
   class UserService:
       def __init__(self, db: DatabasePort):  # DatabasePort not registered!
           self.db = db

   container = Container(profile=Profile.PRODUCTION)
   container.resolve(UserService)  # ServiceNotFoundError (shows DatabasePort missing)

**Solution**: Register an adapter for the missing dependency:

.. code-block:: python

   @adapter.for_(DatabasePort, profile=Profile.PRODUCTION)
   class PostgresAdapter:
       async def query(self, sql: str) -> list[dict]:
           ...

Service Module Not Imported
~~~~~~~~~~~~~~~~~~~~~~~~~~~

The service module wasn't imported before scanning.

.. code-block:: python

   # myapp/services/user.py
   @service
   class UserService:
       ...

   # myapp/main.py
   # Forgot to import myapp.services.user!
   container = Container(profile=Profile.PRODUCTION)
   container.resolve(UserService)  # ServiceNotFoundError!

**Solution**: Import the module or use package scanning:

.. code-block:: python

   # Option 1: Explicit import
   import myapp.services.user

   # Option 2: Package scanning (recommended)
   container = Container(profile=Profile.PRODUCTION)
   container.scan(package="myapp.services")

Missing Type Hints
~~~~~~~~~~~~~~~~~~

Constructor parameters must have type hints for injection to work.

.. code-block:: python

   @service
   class UserService:
       def __init__(self, db):  # Missing type hint!
           self.db = db

**Solution**: Add type hints to all constructor parameters:

.. code-block:: python

   @service
   class UserService:
       def __init__(self, db: DatabasePort):  # Type hint added
           self.db = db

Solutions
---------

Debugging Multiple Dependencies
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When a service has multiple dependencies, try resolving each one individually:

.. code-block:: python

   @service
   class NotificationService:
       def __init__(self, email: EmailPort, sms: SMSPort, db: DatabasePort):
           ...

   # If resolution fails, check each dependency:
   try:
       container.resolve(EmailPort)  # Check if EmailPort works
   except Exception as e:
       print(f"EmailPort failed: {e}")

   try:
       container.resolve(SMSPort)  # Check if SMSPort works
   except Exception as e:
       print(f"SMSPort failed: {e}")

Using Forward References
~~~~~~~~~~~~~~~~~~~~~~~~

For circular imports, use string quotes for forward references:

.. code-block:: python

   @service
   class ServiceA:
       def __init__(self, b: 'ServiceB'):  # Forward reference
           self.b = b

   @service
   class ServiceB:
       def __init__(self, a: ServiceA):
           self.a = a

.. warning::

   While forward references help with import cycles, circular dependencies between
   ``@lifecycle`` components will still cause :doc:`circular-dependency` errors.

Debugging Tips
--------------

1. **Check the error context**: It shows which specific dependency failed
2. **Verify decorators**: Ensure ``@service`` is present on all services
3. **Check imports**: Ensure service modules are imported before scanning
4. **Check type hints**: All constructor parameters need type annotations
5. **Profile mismatch**: If a dependency is a port, check its adapter profile

Best Practices
--------------

1. **Fail fast at startup**: Resolve all services at startup to catch missing registrations
2. **Use package scanning**: ``container.scan(package="myapp")`` auto-imports modules
3. **Integration tests**: Test that all services resolve in each profile
4. **Type hints everywhere**: Constructor parameters must have type annotations

Difference from AdapterNotFoundError
------------------------------------

.. list-table::
   :header-rows: 1
   :widths: 50 50

   * - ServiceNotFoundError
     - AdapterNotFoundError
   * - For concrete classes with ``@service``
     - For ports (Protocol/ABC)
   * - Missing ``@service`` decorator
     - Missing ``@adapter.for_()`` decorator
   * - Unresolvable dependencies
     - Profile mismatch

See Also
--------

- :doc:`adapter-not-found` - Error for missing port adapters
- :doc:`/user_guide/getting_started` - How to register services
- :doc:`/user_guide/hexagonal_architecture` - Architecture patterns
