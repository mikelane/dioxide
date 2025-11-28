dioxide.testing
===============

.. py:module:: dioxide.testing

.. autoapi-nested-parse::

   Testing utilities for dioxide.

   This module provides helpers for writing tests with dioxide, making it easy
   to create isolated test containers with fresh state.

   .. admonition:: Example

      Using the fresh_container context manager::

          from dioxide.testing import fresh_container
          from dioxide import Profile


          async def test_user_registration():
              async with fresh_container(profile=Profile.TEST) as container:
                  service = container.resolve(UserService)
                  await service.register('alice@example.com', 'Alice')

                  email = container.resolve(EmailPort)
                  assert len(email.sent_emails) == 1

      Using with pytest fixtures::

          import pytest
          from dioxide.testing import fresh_container
          from dioxide import Profile


          @pytest.fixture
          async def container():
              async with fresh_container(profile=Profile.TEST) as c:
                  yield c


          async def test_something(container):
              service = container.resolve(MyService)
              # ... test with fresh, isolated container



Functions
---------

.. autoapisummary::

   dioxide.testing.fresh_container


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
