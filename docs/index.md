# Welcome to dioxide's documentation!

[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/github/license/mikelane/dioxide)](https://github.com/mikelane/dioxide/blob/main/LICENSE)
[![PyPI version](https://img.shields.io/pypi/v/dioxide)](https://pypi.org/project/dioxide/)

**dioxide** is a fast, Rust-backed declarative dependency injection framework for Python that makes the Dependency Inversion Principle feel inevitable.

## Key Features

* **Hexagonal Architecture**: Explicit `@adapter.for_()` and `@service` decorators
* **Profile-Based Configuration**: Different adapters for production, test, and development
* **Type-Safe**: Full mypy and pyright support with type hints
* **Rust Performance**: Fast container operations via PyO3
* **Testing Without Mocks**: Use fast fakes instead of mocking frameworks
* **Lifecycle Management**: Automatic initialization and cleanup with `@lifecycle`
* **Zero Ceremony**: Auto-injection via type hints, no manual wiring

## Quick Start

**Installation**:

```bash
pip install dioxide
```

**Basic Usage**:

```python
from typing import Protocol
from dioxide import adapter, service, Profile, container

# Define port (interface)
class EmailPort(Protocol):
    async def send(self, to: str, subject: str, body: str) -> None: ...

# Production adapter
@adapter.for_(EmailPort, profile=Profile.PRODUCTION)
class SendGridAdapter:
    async def send(self, to: str, subject: str, body: str) -> None:
        # Real SendGrid API calls
        pass

# Test adapter (fake)
@adapter.for_(EmailPort, profile=Profile.TEST)
class FakeEmailAdapter:
    def __init__(self):
        self.sent_emails = []

    async def send(self, to: str, subject: str, body: str) -> None:
        self.sent_emails.append({"to": to, "subject": subject, "body": body})

# Service depends on port (interface), not concrete adapter
@service
class UserService:
    def __init__(self, email: EmailPort):
        self.email = email

    async def register_user(self, email_addr: str, name: str):
        await self.email.send(email_addr, "Welcome!", f"Hello {name}!")

# Production: activates SendGridAdapter
container.scan("app", profile=Profile.PRODUCTION)
user_service = UserService()  # EmailPort auto-injected with SendGridAdapter

# Testing: activates FakeEmailAdapter
container.scan("app", profile=Profile.TEST)
test_service = UserService()  # EmailPort auto-injected with FakeEmailAdapter
```

## Why dioxide?

dioxide makes clean architecture the path of least resistance:

1. **Explicit Architecture**: `@adapter` for boundaries, `@service` for domain logic
2. **Type-Safe**: If mypy passes, the wiring is correct
3. **Profile-Based**: Different implementations for production vs test
4. **Testing Without Mocks**: Use fast fakes at the seams
5. **Zero Ceremony**: No manual `.bind()` or `.register()` calls

## Philosophy

**The North Star**: Make the Dependency Inversion Principle feel inevitable.

dioxide encourages:

* **Ports and Adapters**: Define ports (Protocols), implement adapters
* **Profile-Based Testing**: Swap implementations by changing profile
* **Fakes > Mocks**: Use real, fast implementations instead of mocking frameworks
* **Type Safety**: Leverage Python's type system completely

## Contents

```{toctree}
:maxdepth: 2
:caption: User Guide

user_guide/getting_started
user_guide/hexagonal_architecture
user_guide/profiles
user_guide/lifecycle
user_guide/testing_with_fakes
user_guide/framework_integration
```

```{toctree}
:maxdepth: 2
:caption: Tutorial Examples

examples/01-basic-dependency-injection
examples/02-email-service-with-profiles
examples/03-multi-tier-application
examples/04-lifecycle-management
```

```{toctree}
:maxdepth: 2
:caption: API Reference

autoapi/index
```

```{toctree}
:maxdepth: 1
:caption: Development

development/contributing
development/changelog
versioning
```

## Hexagonal Architecture Example

dioxide makes hexagonal architecture explicit through distinct decorators:

```python
from typing import Protocol
from dioxide import adapter, service, Profile

# Port (interface) - the seam
class DatabasePort(Protocol):
    async def save_user(self, user: User) -> None: ...

# Production adapter - real PostgreSQL
@adapter.for_(DatabasePort, profile=Profile.PRODUCTION)
class PostgresAdapter:
    async def save_user(self, user: User) -> None:
        # Real database operations
        pass

# Test adapter - in-memory fake
@adapter.for_(DatabasePort, profile=Profile.TEST)
class InMemoryAdapter:
    def __init__(self):
        self.users = {}

    async def save_user(self, user: User) -> None:
        self.users[user.id] = user

# Service - core domain logic
@service
class UserService:
    def __init__(self, db: DatabasePort):
        self.db = db  # Depends on port, not concrete adapter

    async def register(self, user: User):
        # Business logic
        await self.db.save_user(user)
```

## Lifecycle Management

Services and adapters can opt into lifecycle management:

```python
from dioxide import service, lifecycle

@service
@lifecycle
class Database:
    def __init__(self, config: AppConfig):
        self.config = config
        self.engine = None

    async def initialize(self) -> None:
        """Called automatically by container.start()"""
        self.engine = create_async_engine(self.config.database_url)

    async def dispose(self) -> None:
        """Called automatically by container.stop()"""
        if self.engine:
            await self.engine.dispose()

# Automatic lifecycle management
async with container:
    db = container.resolve(Database)
    # db.initialize() was called automatically
# db.dispose() called automatically on exit
```

## Testing Without Mocks

dioxide encourages using fast fakes instead of mocking frameworks:

```python
# ❌ Traditional approach - mocking
@patch('sendgrid.send')
def test_notification(mock_email):
    mock_email.return_value = True
    # Testing mock behavior, not real code

# ✅ dioxide approach - fakes
async def test_notification():
    # Arrange: Real fake implementation
    container.scan("app", profile=Profile.TEST)
    email = container.resolve(EmailPort)  # Gets FakeEmailAdapter

    # Act: Real service code
    service = UserService()
    await service.register_user("alice@example.com", "Alice")

    # Assert: Real observable outcomes
    assert len(email.sent_emails) == 1
    assert email.sent_emails[0]["to"] == "alice@example.com"
```

## Framework Integration

dioxide integrates seamlessly with popular Python frameworks:

**FastAPI**:

```python
from fastapi import FastAPI
from dioxide import container, Profile
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    container.scan("app", profile=Profile.PRODUCTION)
    async with container:
        yield

app = FastAPI(lifespan=lifespan)

@app.post("/users")
async def create_user(user: UserData):
    service = container.resolve(UserService)
    await service.register_user(user.email, user.name)
```

## Indices and tables

* {ref}`genindex`
* {ref}`modindex`
* {ref}`search`
