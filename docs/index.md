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

## Find What You Need

Choose your path based on what you want to accomplish:

:::::{grid} 2
:gutter: 4

::::{grid-item-card} Just want to get started?
:class-card: sd-border-primary sd-shadow-sm
:link: user_guide/getting_started
:link-type: doc

**15 minutes to your first app**

Install dioxide, understand the core concepts, and build a working example with ports, adapters, and services.

+++
{bdg-primary}`Quickstart` {bdg-secondary}`Install` {bdg-secondary}`Tutorial`
::::

::::{grid-item-card} Evaluating dioxide for your project?
:class-card: sd-border-primary sd-shadow-sm
:link: why-dioxide
:link-type: doc

**Honest comparison & philosophy**

See how dioxide compares to dependency-injector, lagom, and other frameworks. Understand the design decisions and limitations.

+++
{bdg-primary}`Comparison` {bdg-secondary}`Philosophy` {bdg-secondary}`Tradeoffs`
::::

::::{grid-item-card} Need testing patterns?
:class-card: sd-border-primary sd-shadow-sm
:link: TESTING_GUIDE
:link-type: doc

**Fakes over mocks philosophy**

Learn why dioxide prefers fakes to mocks, how to structure test adapters, and patterns for fast, deterministic tests.

+++
{bdg-primary}`Testing` {bdg-secondary}`Fakes` {bdg-secondary}`Fixtures`
::::

::::{grid-item-card} Integrating with a framework?
:class-card: sd-border-primary sd-shadow-sm
:link: cookbook/index
:link-type: doc

**Framework integration recipes**

Copy-paste recipes for FastAPI, testing patterns, configuration, and database integration.

+++
{bdg-primary}`FastAPI` {bdg-secondary}`Testing` {bdg-secondary}`Database`
::::

::::{grid-item-card} Hit an error?
:class-card: sd-border-primary sd-shadow-sm
:link: troubleshooting/index
:link-type: doc

**Diagnose and fix common issues**

Quick diagnosis table and detailed solutions for adapter not found, circular dependencies, scope errors, and more.

+++
{bdg-primary}`Errors` {bdg-secondary}`Debugging` {bdg-secondary}`Solutions`
::::

:::::

---

## Quick Start

Install dioxide with pip:

```bash
pip install dioxide
```

Define your ports (interfaces), adapters (implementations), and services:

```python
from typing import Protocol
from dioxide import adapter, service, Profile, Container

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

# Production: auto-scans and activates SendGridAdapter
container = Container(profile=Profile.PRODUCTION)
service = container.resolve(NotificationService)
```

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
container = Container(profile=Profile.TEST)
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
    container = Container(profile=Profile.TEST)
    email = container.resolve(EmailPort)

    service = container.resolve(NotificationService)
    await service.notify_user("alice@example.com", "Hi!")

    assert len(email.sent_emails) == 1
```
::::

:::::

```{button-ref} testing/index
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
from dioxide import Container, Profile
from contextlib import asynccontextmanager

container = Container(profile=Profile.PRODUCTION)

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with container:
        yield

app = FastAPI(lifespan=lifespan)

@app.post("/users")
async def create_user(user: UserData):
    service = container.resolve(UserService)
    await service.register_user(user.email, user.name)
```

```{button-ref} cookbook/fastapi
:color: primary
:outline:
:class: sd-rounded-pill

See the FastAPI cookbook
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
:caption: Getting Started

user_guide/getting_started
why-dioxide
philosophy
```

```{toctree}
:maxdepth: 2
:hidden:
:caption: User Guide

user_guide/services-vs-adapters
user_guide/hexagonal_architecture
user_guide/container_patterns
user_guide/package_scanning
user_guide/architecture
```

```{toctree}
:maxdepth: 2
:hidden:
:caption: Testing

testing/index
testing/philosophy
testing/patterns
testing/fixtures
testing/integration
testing/troubleshooting
```

```{toctree}
:maxdepth: 2
:hidden:
:caption: Advanced Topics

guides/choosing-decorators
guides/scoping
guides/lifecycle-async-patterns
guides/decorator-order
```

```{toctree}
:maxdepth: 2
:hidden:
:caption: Cookbook

cookbook/index
cookbook/fastapi
cookbook/configuration
cookbook/database
cookbook/testing
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
:caption: Tutorials

examples/01-basic-dependency-injection
examples/02-email-service-with-profiles
examples/03-multi-tier-application
examples/04-lifecycle-management
```

```{toctree}
:maxdepth: 2
:hidden:
:caption: API Reference

api/index
```

```{toctree}
:maxdepth: 2
:hidden:
:caption: Troubleshooting

troubleshooting/index
```

```{toctree}
:maxdepth: 1
:hidden:
:caption: Migration & Versioning

migration-v1-to-v2
migration-from-dependency-injector
stability-policy
versioning
```

```{toctree}
:maxdepth: 1
:hidden:
:caption: Contributing

navigation
design-principles
design/ADR-001-container-architecture
design/ADR-002-pyo3-binding-strategy
design/ADR-003-rust-backend-decision
```
