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
   dioxide.testing.fresh_container_fixture
   dioxide.testing.dioxide_container_session


Module Contents
---------------

.. py:function:: fresh_container(profile = None, package = None)
   :async:


   Create a fresh, isolated container for testing.

   This context manager creates a new Container instance, scans for components,
   manages lifecycle (start/stop), and ensures complete isolation between tests.

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


.. py:function:: fresh_container_fixture()

   Alternative fixture with name matching the context manager.

   This fixture behaves like ``dioxide_container``, providing a fresh
   Container for each test. The name matches the ``fresh_container``
   context manager for consistency.

   :Yields: A fresh Container instance.

   Example::

       async def test_isolated(fresh_container_fixture):
           fresh_container_fixture.scan(profile=Profile.TEST)
           # Guaranteed fresh container, no state leakage
           pass


.. py:function:: dioxide_container_session()

   Provide a shared Container for the entire test session.

   This session-scoped fixture creates a single Container instance that is
   shared across all tests in the session. Use this for performance when
   tests can safely share container state.

   WARNING: Session-scoped containers share state between tests. Only use
   this when you understand the implications and tests are designed to
   handle shared state.

   :Yields: A shared Container instance for the session.

   Example::

       # In conftest.py - scan once at session start
       @pytest.fixture(scope='session', autouse=True)
       def setup_session_container(dioxide_container_session):
           dioxide_container_session.scan(profile=Profile.TEST)


       # In tests - just use the pre-scanned container
       async def test_shared_container(dioxide_container_session):
           service = dioxide_container_session.resolve(SharedService)
           # ... use shared container
