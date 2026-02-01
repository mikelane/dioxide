Framework Integration Testing
=============================

This page shows how to test dioxide-based applications with popular Python frameworks.

FastAPI Integration
-------------------

dioxide integrates seamlessly with FastAPI for testing.

Basic Test Setup
~~~~~~~~~~~~~~~~

.. code-block:: python

   import pytest
   from fastapi import FastAPI
   from fastapi.testclient import TestClient
   from httpx import AsyncClient, ASGITransport
   from dioxide import Container, Profile
   from dioxide.testing import fresh_container

   @pytest.fixture
   async def app():
       """Create FastAPI app with test profile."""
       from myapp.main import create_app

       async with fresh_container(profile=Profile.TEST) as container:
           app = create_app(container)
           yield app

   @pytest.fixture
   async def client(app):
       """Async test client for FastAPI."""
       async with AsyncClient(
           transport=ASGITransport(app=app),
           base_url="http://test"
       ) as client:
           yield client

Testing Endpoints
~~~~~~~~~~~~~~~~~

.. code-block:: python

   async def test_create_user(client, app):
       """Test user creation endpoint."""
       response = await client.post(
           "/users",
           json={"name": "Alice", "email": "alice@example.com"}
       )

       assert response.status_code == 201
       data = response.json()
       assert data["name"] == "Alice"

   async def test_welcome_email_sent(client, app):
       """Test that welcome email is sent on registration."""
       # Get the fake email adapter from the container
       container = app.state.container
       email = container.resolve(EmailPort)

       # Make request
       await client.post(
           "/users",
           json={"name": "Alice", "email": "alice@example.com"}
       )

       # Verify email was sent
       assert len(email.sent_emails) == 1
       assert email.sent_emails[0]["to"] == "alice@example.com"

Using DioxideMiddleware
~~~~~~~~~~~~~~~~~~~~~~~

If you're using ``DioxideMiddleware``, testing is straightforward:

.. code-block:: python

   from fastapi import FastAPI
   from dioxide.fastapi import DioxideMiddleware, Inject
   import pytest
   from httpx import AsyncClient, ASGITransport

   @pytest.fixture
   def app():
       """Create app with test profile middleware."""
       app = FastAPI()
       app.add_middleware(
           DioxideMiddleware,
           profile=Profile.TEST,
           packages=["myapp"]
       )

       @app.get("/users/{user_id}")
       async def get_user(
           user_id: int,
           service: UserService = Inject(UserService)
       ):
           return await service.get_user(user_id)

       return app

   @pytest.fixture
   async def client(app):
       async with AsyncClient(
           transport=ASGITransport(app=app),
           base_url="http://test"
       ) as client:
           yield client

   async def test_get_user(client):
       response = await client.get("/users/1")
       assert response.status_code == 200

----

Flask Integration
-----------------

Testing Flask applications with dioxide.

Basic Test Setup
~~~~~~~~~~~~~~~~

.. code-block:: python

   import pytest
   from flask import Flask
   from dioxide import Container, Profile

   @pytest.fixture
   def app():
       """Create Flask app with test profile."""
       app = Flask(__name__)
       container = Container()
       container.scan(profile=Profile.TEST)
       app.container = container

       @app.route("/users", methods=["POST"])
       def create_user():
           service = app.container.resolve(UserService)
           # ...

       return app

   @pytest.fixture
   def client(app):
       """Flask test client."""
       return app.test_client()

Testing Endpoints
~~~~~~~~~~~~~~~~~

.. code-block:: python

   def test_create_user(client, app):
       """Test user creation."""
       response = client.post(
           "/users",
           json={"name": "Alice", "email": "alice@example.com"}
       )

       assert response.status_code == 201

       # Verify email was sent
       email = app.container.resolve(EmailPort)
       assert len(email.sent_emails) == 1

----

Django Integration
------------------

Testing Django applications with dioxide.

Basic Test Setup
~~~~~~~~~~~~~~~~

.. code-block:: python

   import pytest
   from django.test import Client, override_settings
   from dioxide import Profile
   from dioxide.django import configure_dioxide

   @pytest.fixture(autouse=True)
   def setup_dioxide():
       """Configure dioxide with test profile for each test."""
       configure_dioxide(profile=Profile.TEST, packages=["myapp"])
       yield
       # Cleanup is automatic

   @pytest.fixture
   def client():
       return Client()

Testing Views
~~~~~~~~~~~~~

.. code-block:: python

   def test_user_list(client):
       """Test user list view."""
       response = client.get("/users/")

       assert response.status_code == 200

   def test_create_user(client):
       """Test user creation."""
       from dioxide.django import inject

       response = client.post(
           "/users/",
           data={"name": "Alice", "email": "alice@example.com"},
           content_type="application/json"
       )

       assert response.status_code == 201

       # Verify side effects
       email = inject(EmailPort)
       assert len(email.sent_emails) == 1

----

Celery Integration
------------------

Testing Celery tasks with dioxide.

Basic Test Setup
~~~~~~~~~~~~~~~~

.. code-block:: python

   import pytest
   from celery import Celery
   from dioxide import Container, Profile

   @pytest.fixture
   def celery_app():
       """Create Celery app with test config."""
       app = Celery("test")
       app.config_from_object({
           "task_always_eager": True,  # Execute tasks synchronously
           "task_eager_propagates": True,  # Propagate exceptions
       })
       return app

   @pytest.fixture
   def container():
       """Container with test fakes."""
       c = Container()
       c.scan(profile=Profile.TEST)
       return c

Testing Tasks
~~~~~~~~~~~~~

.. code-block:: python

   from myapp.tasks import process_order

   def test_process_order(container, celery_app):
       """Test order processing task."""
       # Seed test data
       orders = container.resolve(OrderRepository)
       orders.seed({"id": 1, "status": "pending", "total": 100.00})

       # Run task (synchronously due to task_always_eager)
       result = process_order.delay(order_id=1)

       # Verify order was processed
       order = orders.find_by_id(1)
       assert order["status"] == "completed"

       # Verify email was sent
       email = container.resolve(EmailPort)
       assert len(email.sent_emails) == 1

----

Click CLI Integration
---------------------

Testing Click CLI commands with dioxide.

Basic Test Setup
~~~~~~~~~~~~~~~~

.. code-block:: python

   import pytest
   from click.testing import CliRunner
   from dioxide import Container, Profile

   @pytest.fixture
   def runner():
       """Click test runner."""
       return CliRunner()

   @pytest.fixture
   def container():
       """Container with test fakes."""
       c = Container()
       c.scan(profile=Profile.TEST)
       return c

Testing Commands
~~~~~~~~~~~~~~~~

.. code-block:: python

   from myapp.cli import cli

   def test_send_newsletter(runner, container):
       """Test newsletter command."""
       # Seed test data
       users = container.resolve(UserRepository)
       users.seed(
           {"id": 1, "email": "alice@example.com", "subscribed": True},
           {"id": 2, "email": "bob@example.com", "subscribed": True},
       )

       # Run command
       result = runner.invoke(cli, ["send-newsletter", "--subject", "Hello!"])

       assert result.exit_code == 0

       # Verify emails were sent
       email = container.resolve(EmailPort)
       assert len(email.sent_emails) == 2

----

General Testing Tips
--------------------

Test Isolation
~~~~~~~~~~~~~~

Always use fresh containers for test isolation:

.. code-block:: python

   @pytest.fixture
   async def container():
       """Fresh container per test."""
       async with fresh_container(profile=Profile.TEST) as c:
           yield c

Seeding Test Data
~~~~~~~~~~~~~~~~~

Use fake adapter methods to seed test data:

.. code-block:: python

   @pytest.fixture
   def seeded_users(container):
       """Seed users for tests that need them."""
       users = container.resolve(UserRepository)
       users.seed(
           {"id": 1, "email": "alice@example.com"},
           {"id": 2, "email": "bob@example.com"},
       )
       return users

Verifying Side Effects
~~~~~~~~~~~~~~~~~~~~~~

Access fakes directly to verify side effects:

.. code-block:: python

   async def test_sends_email(container):
       service = container.resolve(UserService)
       await service.register("alice@example.com", "Alice")

       # Get fake adapter and verify
       email = container.resolve(EmailPort)
       assert len(email.sent_emails) == 1
       assert email.sent_emails[0]["to"] == "alice@example.com"

.. seealso::

   - :doc:`fixtures` - Test fixtures and container patterns
   - :doc:`patterns` - Common fake implementation patterns
   - :doc:`/api/dioxide/fastapi/index` - FastAPI integration API
   - :doc:`/api/dioxide/flask/index` - Flask integration API
   - :doc:`/api/dioxide/celery/index` - Celery integration API
   - :doc:`/api/dioxide/click/index` - Click integration API
