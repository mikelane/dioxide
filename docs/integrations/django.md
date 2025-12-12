# Django and Django REST Framework Integration

dioxide provides seamless integration with Django and Django REST Framework (DRF) through the `dioxide.django` module.

## Installation

```bash
pip install dioxide[django]
```

This installs dioxide along with Django as an optional dependency.

## Quick Start

### 1. Configure dioxide

In your Django `settings.py` or in your app's `apps.py` `ready()` method:

```python
# settings.py
from dioxide import Profile
from dioxide.django import configure_dioxide

# Configure at module level (runs when Django loads settings)
configure_dioxide(profile=Profile.PRODUCTION, packages=["myapp"])
```

Or in your app configuration:

```python
# myapp/apps.py
from django.apps import AppConfig
from dioxide import Profile
from dioxide.django import configure_dioxide


class MyAppConfig(AppConfig):
    name = "myapp"

    def ready(self):
        configure_dioxide(profile=Profile.PRODUCTION, packages=["myapp"])
```

### 2. Add Middleware

Add the dioxide middleware to your `MIDDLEWARE` setting:

```python
# settings.py
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "dioxide.django.DioxideMiddleware",  # Add dioxide middleware
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
```

### 3. Use in Views

Inject dependencies using the `inject()` function:

```python
# views.py
from django.http import JsonResponse
from dioxide.django import inject


def user_list(request):
    service = inject(UserService)
    users = service.list_all()
    return JsonResponse({"users": users})


def user_detail(request, user_id):
    service = inject(UserService)
    user = service.get_user(user_id)
    return JsonResponse(user)
```

## API Reference

### `configure_dioxide()`

```python
def configure_dioxide(
    profile: Profile | str | None = None,
    container: Container | None = None,
    packages: list[str] | None = None,
) -> None:
```

Configure dioxide dependency injection for a Django application.

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `profile` | `Profile \| str \| None` | Profile to scan with (e.g., `Profile.PRODUCTION`) |
| `container` | `Container \| None` | Optional Container instance. Uses global singleton if not provided |
| `packages` | `list[str] \| None` | Optional list of packages to scan for components |

**Example:**

```python
from dioxide import Container, Profile
from dioxide.django import configure_dioxide

# Basic usage
configure_dioxide(profile=Profile.PRODUCTION)

# With specific packages
configure_dioxide(
    profile=Profile.PRODUCTION,
    packages=["myapp.services", "myapp.adapters"],
)

# With custom container
my_container = Container()
configure_dioxide(profile=Profile.TEST, container=my_container)
```

### `DioxideMiddleware`

Django middleware that creates a `ScopedContainer` for each HTTP request.

**What it does:**

1. Creates a `ScopedContainer` before the view runs
2. Stores it in thread-local storage for `inject()` to access
3. Disposes the scope after the response is returned

**Placement:**

The middleware should be placed after session/auth middleware but before your application middleware.

### `inject()`

```python
def inject(component_type: type[T]) -> T:
```

Resolve a component from the current request's dioxide scope.

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `component_type` | `type[T]` | The type to resolve from the container |

**Returns:** An instance of the requested type.

**Raises:**
- `RuntimeError`: If called outside a request context
- `RuntimeError`: If `configure_dioxide()` was not called

**Example:**

```python
from dioxide.django import inject


def my_view(request):
    # Resolve dependencies
    user_service = inject(UserService)
    email_service = inject(EmailService)

    # Use the services
    user = user_service.get_current_user()
    email_service.send_welcome(user.email)

    return JsonResponse({"status": "ok"})
```

## Request Scoping

The middleware creates a `ScopedContainer` for each HTTP request, enabling request-scoped dependencies:

```python
from dioxide import service, Scope
import uuid


@service(scope=Scope.REQUEST)
class RequestContext:
    """Request-scoped context available throughout a single request."""

    def __init__(self):
        self.request_id = str(uuid.uuid4())
        self.start_time = time.time()


# In views - same instance within the request
def my_view(request):
    ctx = inject(RequestContext)
    # ctx.request_id is unique per request but consistent
    # across multiple inject() calls within the same request
    return JsonResponse({"request_id": ctx.request_id})


def another_view(request):
    ctx = inject(RequestContext)
    # Different request = different request_id
    return JsonResponse({"request_id": ctx.request_id})
```

### Scope Behavior

| Scope | Behavior |
|-------|----------|
| `Scope.SINGLETON` | Shared across all requests (resolved from parent container) |
| `Scope.REQUEST` | Fresh instance per HTTP request (resolved from scoped container) |
| `Scope.FACTORY` | New instance every time `inject()` is called |

## Thread Safety

Django uses threading by default. The dioxide integration handles this by storing the scoped container in thread-local storage:

- Each thread gets its own request scope
- No cross-request contamination
- Works correctly with Django's threaded request handling
- Compatible with WSGI servers like gunicorn with sync workers

## Lifecycle Management

dioxide handles component lifecycle automatically:

```python
from dioxide import adapter, lifecycle, Profile
from typing import Protocol


class DatabasePort(Protocol):
    def query(self, sql: str) -> list: ...


@adapter.for_(DatabasePort, profile=Profile.PRODUCTION)
@lifecycle
class PostgresAdapter:
    """Database adapter with lifecycle management."""

    async def initialize(self) -> None:
        """Called when configure_dioxide() starts the container."""
        self.pool = await asyncpg.create_pool(DATABASE_URL)
        print("Database pool created")

    async def dispose(self) -> None:
        """Called on application shutdown."""
        await self.pool.close()
        print("Database pool closed")

    def query(self, sql: str) -> list:
        # Use self.pool for queries
        ...
```

**Lifecycle timeline:**

1. `configure_dioxide()` is called during Django startup
2. Container scans packages and starts (runs `initialize()` on `@lifecycle` components)
3. Each request creates a `ScopedContainer` via middleware
4. Request ends: scope is disposed (cleans up REQUEST-scoped `@lifecycle` components)
5. Application shutdown: container stops (runs `dispose()` on SINGLETON `@lifecycle` components)

## Django REST Framework

dioxide integrates seamlessly with Django REST Framework. Use the same `inject()` function in any DRF view type.

### Function-Based Views with @api_view

```python
from rest_framework.decorators import api_view
from rest_framework.response import Response
from dioxide.django import inject


@api_view(["GET"])
def user_list(request):
    service = inject(UserService)
    users = service.list_all()
    return Response(users)


@api_view(["GET", "POST"])
def user_detail(request, pk):
    service = inject(UserService)

    if request.method == "GET":
        user = service.get_user(pk)
        return Response(user)

    elif request.method == "POST":
        user = service.create_user(request.data)
        return Response(user, status=201)
```

### Class-Based APIViews

```python
from rest_framework.views import APIView
from rest_framework.response import Response
from dioxide.django import inject


class UserListView(APIView):
    def get(self, request):
        service = inject(UserService)
        users = service.list_all()
        return Response(users)

    def post(self, request):
        service = inject(UserService)
        user = service.create_user(request.data)
        return Response(user, status=201)


class UserDetailView(APIView):
    def get(self, request, pk):
        service = inject(UserService)
        user = service.get_user(pk)
        return Response(user)

    def put(self, request, pk):
        service = inject(UserService)
        user = service.update_user(pk, request.data)
        return Response(user)

    def delete(self, request, pk):
        service = inject(UserService)
        service.delete_user(pk)
        return Response(status=204)
```

### ViewSets

```python
from rest_framework import viewsets
from rest_framework.response import Response
from dioxide.django import inject


class UserViewSet(viewsets.ViewSet):
    def list(self, request):
        service = inject(UserService)
        users = service.list_all()
        return Response(users)

    def create(self, request):
        service = inject(UserService)
        user = service.create_user(request.data)
        return Response(user, status=201)

    def retrieve(self, request, pk=None):
        service = inject(UserService)
        user = service.get_user(pk)
        return Response(user)

    def update(self, request, pk=None):
        service = inject(UserService)
        user = service.update_user(pk, request.data)
        return Response(user)

    def destroy(self, request, pk=None):
        service = inject(UserService)
        service.delete_user(pk)
        return Response(status=204)
```

### Generic Views and Mixins

For generic views that require more customization:

```python
from rest_framework import generics
from rest_framework.response import Response
from dioxide.django import inject


class UserListCreateView(generics.ListCreateAPIView):
    def get_queryset(self):
        service = inject(UserService)
        return service.list_all()

    def perform_create(self, serializer):
        service = inject(UserService)
        service.create_user(serializer.validated_data)
```

## Complete Example

Here's a complete example showing a Django application with dioxide integration:

### Project Structure

```
myproject/
├── myproject/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── myapp/
│   ├── __init__.py
│   ├── apps.py
│   ├── ports.py
│   ├── adapters.py
│   ├── services.py
│   ├── views.py
│   └── urls.py
└── manage.py
```

### ports.py - Define Interfaces

```python
from typing import Protocol


class UserRepository(Protocol):
    """Port for user data access."""

    def get_all(self) -> list[dict]:
        ...

    def get_by_id(self, user_id: str) -> dict | None:
        ...

    def save(self, user: dict) -> dict:
        ...


class EmailPort(Protocol):
    """Port for sending emails."""

    def send(self, to: str, subject: str, body: str) -> None:
        ...
```

### adapters.py - Implement Interfaces

```python
from dioxide import adapter, Profile
from .ports import UserRepository, EmailPort


@adapter.for_(UserRepository, profile=Profile.PRODUCTION)
class DjangoUserRepository:
    """Production repository using Django ORM."""

    def get_all(self) -> list[dict]:
        from django.contrib.auth.models import User

        return list(User.objects.values("id", "username", "email"))

    def get_by_id(self, user_id: str) -> dict | None:
        from django.contrib.auth.models import User

        try:
            user = User.objects.get(id=user_id)
            return {"id": user.id, "username": user.username, "email": user.email}
        except User.DoesNotExist:
            return None

    def save(self, user: dict) -> dict:
        from django.contrib.auth.models import User

        db_user = User.objects.create_user(**user)
        return {"id": db_user.id, "username": db_user.username, "email": db_user.email}


@adapter.for_(UserRepository, profile=Profile.TEST)
class FakeUserRepository:
    """In-memory repository for testing."""

    def __init__(self):
        self.users: dict[str, dict] = {}

    def get_all(self) -> list[dict]:
        return list(self.users.values())

    def get_by_id(self, user_id: str) -> dict | None:
        return self.users.get(user_id)

    def save(self, user: dict) -> dict:
        import uuid

        user_id = str(uuid.uuid4())
        user["id"] = user_id
        self.users[user_id] = user
        return user


@adapter.for_(EmailPort, profile=Profile.PRODUCTION)
class SmtpEmailAdapter:
    """Production email adapter using SMTP."""

    def send(self, to: str, subject: str, body: str) -> None:
        from django.core.mail import send_mail

        send_mail(subject, body, "noreply@example.com", [to])


@adapter.for_(EmailPort, profile=Profile.TEST)
class FakeEmailAdapter:
    """Fake email adapter for testing."""

    def __init__(self):
        self.sent_emails: list[dict] = []

    def send(self, to: str, subject: str, body: str) -> None:
        self.sent_emails.append({"to": to, "subject": subject, "body": body})
```

### services.py - Business Logic

```python
from dioxide import service
from .ports import UserRepository, EmailPort


@service
class UserService:
    """User management service."""

    def __init__(self, repo: UserRepository, email: EmailPort):
        self.repo = repo
        self.email = email

    def list_all(self) -> list[dict]:
        return self.repo.get_all()

    def get_user(self, user_id: str) -> dict | None:
        return self.repo.get_by_id(user_id)

    def create_user(self, user_data: dict) -> dict:
        user = self.repo.save(user_data)
        self.email.send(
            to=user["email"],
            subject="Welcome!",
            body=f"Hello {user['username']}, welcome to our platform!",
        )
        return user
```

### apps.py - Configure dioxide

```python
from django.apps import AppConfig


class MyAppConfig(AppConfig):
    name = "myapp"

    def ready(self):
        from dioxide import Profile
        from dioxide.django import configure_dioxide

        configure_dioxide(profile=Profile.PRODUCTION, packages=["myapp"])
```

### views.py - Use inject()

```python
from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
from dioxide.django import inject
from .services import UserService


# Django function-based view
def user_list_django(request):
    service = inject(UserService)
    users = service.list_all()
    return JsonResponse({"users": users})


# DRF function-based view
@api_view(["GET", "POST"])
def user_list_drf(request):
    service = inject(UserService)

    if request.method == "GET":
        users = service.list_all()
        return Response(users)

    elif request.method == "POST":
        user = service.create_user(request.data)
        return Response(user, status=201)
```

### settings.py - Add Middleware

```python
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "dioxide.django.DioxideMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
```

## Testing

Testing Django views with dioxide is straightforward using the test profile:

```python
# tests/test_views.py
import pytest
from django.test import TestCase, Client
from dioxide import Container, Profile
from dioxide.django import configure_dioxide


class UserViewTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Configure with TEST profile for fakes
        configure_dioxide(profile=Profile.TEST, packages=["myapp"])

    def test_user_list_returns_empty_initially(self):
        client = Client()
        response = client.get("/api/users/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    def test_create_user_sends_welcome_email(self):
        from myapp.adapters import FakeEmailAdapter
        from myapp.ports import EmailPort
        from dioxide import container

        # Get the fake email adapter
        email = container.resolve(EmailPort)

        client = Client()
        response = client.post(
            "/api/users/",
            data={"username": "alice", "email": "alice@example.com"},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 201)

        # Verify email was "sent"
        self.assertEqual(len(email.sent_emails), 1)
        self.assertEqual(email.sent_emails[0]["to"], "alice@example.com")
```

## Troubleshooting

### "dioxide container not configured"

This error occurs when `inject()` is called but `configure_dioxide()` was never run.

**Solution:** Ensure `configure_dioxide()` is called during Django startup, either in `settings.py` or in your app's `apps.py` `ready()` method.

### "inject() called outside of request context"

This error occurs when `inject()` is called outside of an HTTP request (e.g., in a management command or Celery task).

**Solution:** For non-request contexts, use the container directly:

```python
from dioxide import container

# In a management command
def handle(self, *args, **options):
    service = container.resolve(UserService)
    service.do_something()
```

### Middleware Order Issues

If dependencies are not being injected correctly, ensure `DioxideMiddleware` is placed correctly in your middleware stack. It should be:

- After `SessionMiddleware` and `AuthenticationMiddleware` (if your services need access to user/session)
- Before any middleware that might use dioxide services

## See Also

- [Scoping Guide](../guides/scoping.md) - Detailed guide on request scoping
- [Testing Guide](../TESTING_GUIDE.md) - Testing patterns with fakes
- [FastAPI Integration](../user_guide/getting_started.md#fastapi-integration) - Similar integration for FastAPI
