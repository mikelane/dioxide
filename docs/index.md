# dioxide

```{rst-class} landing-hero
```

::::{div} sd-text-center sd-fs-2 sd-font-weight-bold sd-mb-3
Clean Architecture Simplified
::::

::::{div} sd-text-center sd-fs-5 sd-text-muted sd-mb-4
Declarative dependency injection for Python with type-safe wiring and built-in profiles.
::::

::::{div} sd-text-center sd-mb-5

```{button-ref} user_guide/getting_started
:color: primary
:class: sd-rounded-pill sd-px-4 sd-py-2 sd-mr-2

Get Started
```

```{button-link} https://pypi.org/project/dioxide/
:color: secondary
:outline:
:class: sd-rounded-pill sd-px-4 sd-py-2

PyPI
```

::::

::::{div} sd-text-center sd-mb-5

[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/github/license/mikelane/dioxide)](https://github.com/mikelane/dioxide/blob/main/LICENSE)
[![PyPI version](https://img.shields.io/pypi/v/dioxide)](https://pypi.org/project/dioxide/)

::::

---

## Why dioxide?

:::{card-carousel} 3

```{card} Zero Ceremony
:class-card: sd-border-0 sd-shadow-sm
:class-header: sd-bg-transparent sd-border-0 sd-text-center sd-fs-3

Auto-injection via type hints. No manual `.bind()` or `.register()` calls. Just decorate and go.
```

```{card} Built-in Profiles
:class-card: sd-border-0 sd-shadow-sm
:class-header: sd-bg-transparent sd-border-0 sd-text-center sd-fs-3

Swap implementations by environment. Production uses real services, tests use fast fakes.
```

```{card} Type Safety
:class-card: sd-border-0 sd-shadow-sm
:class-header: sd-bg-transparent sd-border-0 sd-text-center sd-fs-3

Full mypy and pyright support. If the types check, the wiring is correct.
```

:::

---

## Quick Start

Install dioxide with pip:

```bash
pip install dioxide
```

Define your ports (interfaces), adapters (implementations), and services:

```python
from typing import Protocol
from dioxide import adapter, service, Profile, container

# Define port (interface)
class EmailPort(Protocol):
    async def send(self, to: str, subject: str, body: str) -> None: ...

# Production adapter - real email service
@adapter.for_(EmailPort, profile=Profile.PRODUCTION)
class SendGridAdapter:
    async def send(self, to: str, subject: str, body: str) -> None:
        # Real SendGrid API calls
        ...

# Test adapter - fast fake for testing
@adapter.for_(EmailPort, profile=Profile.TEST)
class FakeEmailAdapter:
    def __init__(self):
        self.sent_emails = []

    async def send(self, to: str, subject: str, body: str) -> None:
        self.sent_emails.append({"to": to, "subject": subject, "body": body})

# Service depends on port, not concrete adapter
@service
class NotificationService:
    def __init__(self, email: EmailPort):
        self.email = email

    async def notify_user(self, user_email: str, message: str):
        await self.email.send(user_email, "Notification", message)

# Production: activates SendGridAdapter
container.scan("myapp", profile=Profile.PRODUCTION)
service = container.resolve(NotificationService)
```

---

## Key Features

:::::{grid} 2
:gutter: 3

::::{grid-item-card} Hexagonal Architecture
:class-card: sd-border-0 sd-shadow-sm

Explicit `@adapter.for_()` and `@service` decorators make your architecture visible. Ports define boundaries, adapters implement them.

```python
@adapter.for_(DatabasePort, profile=Profile.TEST)
class InMemoryDatabase:
    ...
```
::::

::::{grid-item-card} Profile-Based Testing
:class-card: sd-border-0 sd-shadow-sm

Different implementations for different environments. No mocking frameworks needed.

```python
# Test uses FakeEmailAdapter automatically
container.scan("app", profile=Profile.TEST)
```
::::

::::{grid-item-card} Lifecycle Management
:class-card: sd-border-0 sd-shadow-sm

Opt-in initialization and cleanup with `@lifecycle`. Resources are managed in dependency order.

```python
@service
@lifecycle
class Database:
    async def initialize(self) -> None: ...
    async def dispose(self) -> None: ...
```
::::

::::{grid-item-card} Rust Performance
:class-card: sd-border-0 sd-shadow-sm

Fast container operations via PyO3. Sub-microsecond dependency resolution for production-grade performance.

```python
# Resolution is blazing fast
service = container.resolve(MyService)
```
::::

::::{grid-item-card} Request Scoping
:class-card: sd-border-0 sd-shadow-sm

Isolate dependencies per request, task, or command. Works for web, CLI, Celery, and any bounded context.

```python
async with container.create_scope() as scope:
    ctx = scope.resolve(RequestContext)
```
::::

:::::

---

## Testing Without Mocks

dioxide encourages using fast fakes instead of mocking frameworks:

:::::{grid} 2
:gutter: 3

::::{grid-item}
**Traditional Approach**

```python
# Mocking - tests mock behavior, not real code
@patch('sendgrid.send')
def test_notification(mock_email):
    mock_email.return_value = True
    # Testing mock behavior...
```
::::

::::{grid-item}
**dioxide Approach**

```python
# Fakes - real implementations, real behavior
async def test_notification():
    container.scan("app", profile=Profile.TEST)
    email = container.resolve(EmailPort)

    service = container.resolve(NotificationService)
    await service.notify_user("alice@example.com", "Hi!")

    assert len(email.sent_emails) == 1
```
::::

:::::

```{button-ref} user_guide/testing_with_fakes
:color: primary
:outline:
:class: sd-rounded-pill

Learn more about testing with fakes
```

---

## Framework Integration

dioxide integrates seamlessly with popular Python frameworks:

```python
from fastapi import FastAPI
from dioxide import container, Profile
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    container.scan("myapp", profile=Profile.PRODUCTION)
    async with container:
        yield

app = FastAPI(lifespan=lifespan)

@app.post("/users")
async def create_user(user: UserData):
    service = container.resolve(UserService)
    await service.register_user(user.email, user.name)
```

```{button-ref} user_guide/getting_started
:color: primary
:outline:
:class: sd-rounded-pill

See the Getting Started guide
```

---

## Ready to Get Started?

::::{div} sd-text-center sd-py-4

```{button-ref} user_guide/getting_started
:color: primary
:class: sd-rounded-pill sd-px-5 sd-py-2 sd-fs-5

Read the User Guide
```

::::

---

```{toctree}
:maxdepth: 2
:hidden:
:caption: Overview

why-dioxide
```

```{toctree}
:maxdepth: 2
:hidden:
:caption: User Guide

user_guide/getting_started
user_guide/hexagonal_architecture
user_guide/architecture
user_guide/testing_with_fakes
```

```{toctree}
:maxdepth: 2
:hidden:
:caption: Tutorial Examples

examples/01-basic-dependency-injection
examples/02-email-service-with-profiles
examples/03-multi-tier-application
examples/04-lifecycle-management
```

```{toctree}
:maxdepth: 2
:hidden:
:caption: Guides

guides/scoping
```

```{toctree}
:maxdepth: 2
:hidden:
:caption: Framework Integrations

integrations/django
```

```{toctree}
:maxdepth: 2
:hidden:
:caption: Cookbook

cookbook/index
```

```{toctree}
:maxdepth: 2
:hidden:
:caption: API Reference

api/index
```

```{toctree}
:maxdepth: 1
:hidden:
:caption: Development

versioning
TESTING_GUIDE
```
