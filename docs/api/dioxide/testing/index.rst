dioxide.testing
===============

.. py:module:: dioxide.testing

.. autoapi-nested-parse::

   Testing utilities for dioxide.

   This module provides helpers for writing tests with dioxide, making it easy
   to create isolated test containers with fresh state.

   Instance containers (created via ``Container()`` or ``fresh_container()``) are the
   **recommended pattern for testing**. Each container instance has its own singleton
   cache, ensuring complete test isolation without state leakage.

   For guidance on when to use instance containers vs the global container, see
   the Container Patterns guide: :doc:`/docs/user_guide/container_patterns`

   Pytest Plugin Usage:
       Add the following to your ``conftest.py`` to enable dioxide pytest fixtures::

           pytest_plugins = ['dioxide.testing']

       This makes the following fixtures available:

       - ``dioxide_container``: Fresh container per test (function-scoped)
       - ``fresh_container_fixture``: Alias for dioxide_container
       - ``dioxide_container_session``: Shared container across tests (session-scoped)

   Example using fixtures (recommended)::

       # conftest.py
       pytest_plugins = ['dioxide.testing']


       # test_my_service.py
       async def test_something(dioxide_container):
           dioxide_container.scan(profile=Profile.TEST)
           service = dioxide_container.resolve(MyService)
           # ... test with fresh, isolated container

   Example using fresh_container context manager::

       from dioxide.testing import fresh_container
       from dioxide import Profile


       async def test_user_registration():
           async with fresh_container(profile=Profile.TEST) as container:
               service = container.resolve(UserService)
               await service.register('alice@example.com', 'Alice')

               email = container.resolve(EmailPort)
               assert len(email.sent_emails) == 1



Functions
---------

.. autoapisummary::

   dioxide.testing.fresh_container
   dioxide.testing.dioxide_container


Module Contents
---------------

.. py:function:: fresh_container(profile = None, package = None)
   :async:


   Create a fresh, isolated container for testing.

   This context manager creates a new Container instance, scans for components,
   manages lifecycle (start/stop), and ensures complete isolation between tests.

   This function does NOT require pytest to be installed.

   :param profile: Profile to scan with (e.g., Profile.TEST). If None, scans all profiles.
   :param package: Optional package to scan. If None, scans all registered components.

   :Yields: A fresh Container instance with lifecycle management.

   .. admonition:: Example

      async with fresh_container(profile=Profile.TEST) as container:
          service = container.resolve(UserService)
          # ... test with isolated container
      # Container automatically cleaned up


.. py:function:: dioxide_container()

   Provide a fresh, isolated Container for each test.

   This fixture creates a new Container instance for each test function,
   ensuring complete isolation between tests. The container is NOT
   pre-scanned - you should call ``container.scan(profile=...)`` in your
   test to register components with the desired profile.

   :Yields: A fresh Container instance.

   Example::

       async def test_user_service(dioxide_container):
           dioxide_container.scan(profile=Profile.TEST)
           service = dioxide_container.resolve(UserService)
           result = await service.register_user('Alice', 'alice@example.com')
           assert result['name'] == 'Alice'
