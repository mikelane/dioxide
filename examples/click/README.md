# Click + dioxide: Hexagonal Architecture Example

This example demonstrates how to build a production-ready CLI application using **dioxide** for dependency injection with hexagonal architecture (ports and adapters pattern).

## What This Example Demonstrates

1. **Hexagonal Architecture**: Clean separation between domain logic and infrastructure
2. **Profile-Based Configuration**: Different adapters for production, development, and testing
3. **Lifecycle Management**: Proper initialization and cleanup of resources
4. **Testing with Fakes**: Fast, deterministic tests without mocks
5. **Click Integration**: Per-command scoping via `with_scope` decorator

## Quick Start

### Installation

```bash
# Clone the repository
cd examples/click

# Install dependencies
pip install -r requirements-dev.txt

# Or using uv (faster)
uv pip install -r requirements-dev.txt
```

### Running the CLI

```bash
# Development mode (in-memory database)
PROFILE=development python -m app.main users create "Alice Smith" alice@example.com

# Get help
python -m app.main --help
python -m app.main users --help

# Create a user
python -m app.main users create "Alice Smith" alice@example.com

# Get a user
python -m app.main users get 1

# List all users
python -m app.main users list
```

### Testing

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test class
pytest tests/test_cli.py::DescribeUserCommands -v
```

## Architecture Overview

### Directory Structure

```
app/
├── main.py              # Click CLI + container setup
├── domain/
│   ├── ports.py         # Port definitions (Protocols)
│   └── services.py      # Business logic (@service)
└── adapters/
    ├── logging_email.py # Development email (@adapter)
    └── fakes.py         # Test adapters (@adapter)

tests/
├── conftest.py          # Pytest configuration + fixtures
└── test_cli.py          # Fast tests using fakes
```

## How It Works

### 1. Define Ports (Interfaces)

```python
# app/domain/ports.py
from typing import Protocol

class DatabasePort(Protocol):
    def create_user(self, name: str, email: str) -> dict: ...
    def get_user(self, user_id: str) -> dict | None: ...

class EmailPort(Protocol):
    def send_welcome_email(self, to: str, name: str) -> None: ...
```

### 2. Implement Domain Services

```python
# app/domain/services.py
from dioxide import service

@service
class UserService:
    def __init__(self, db: DatabasePort, email: EmailPort):
        self.db = db
        self.email = email

    def register_user(self, name: str, email: str) -> dict:
        user = self.db.create_user(name, email)
        self.email.send_welcome_email(email, name)
        return user
```

### 3. Create Adapters for Each Profile

```python
# Test adapter (fake)
from dioxide import adapter, Profile

@adapter.for_(DatabasePort, profile=Profile.TEST)
class FakeDatabaseAdapter:
    def __init__(self):
        self.users = {}

    def create_user(self, name: str, email: str) -> dict:
        user = {"id": str(len(self.users) + 1), "name": name, "email": email}
        self.users[user["id"]] = user
        return user
```

### 4. Set Up Click with dioxide.click Integration

```python
# app/main.py
import click
from dioxide import Profile
from dioxide.click import configure_dioxide, with_scope

# Configure container
container = configure_dioxide(profile=Profile.DEVELOPMENT, packages=["app"])


@click.group()
def cli():
    """User management CLI."""
    pass


@cli.group()
def users():
    """User management commands."""
    pass


@users.command("create")
@with_scope(container)
@click.argument("name")
@click.argument("email")
def create_user(scope, name, email):
    """Create a new user."""
    service = scope.resolve(UserService)
    user = service.register_user(name, email)
    click.echo(f"Created user {user['id']}: {user['name']} <{user['email']}>")
```

## Key Differences from Flask/FastAPI Integration

| Feature | Flask/FastAPI | Click |
|---------|--------------|-------|
| Setup | Middleware/configure function | `configure_dioxide()` returns container |
| Injection | `inject(Type)` / `Inject(Type)` | `scope.resolve(Type)` in command |
| Scoping | Automatic per-request | `@with_scope(container)` decorator |
| Scope access | Via `g` object / `request.state` | First argument to command |

## CLI Commands

### Create User

```bash
python -m app.main users create "Alice Smith" alice@example.com

# Output:
# Created user 1: Alice Smith <alice@example.com>
```

### Get User

```bash
python -m app.main users get 1

# Output:
# User 1: Alice Smith <alice@example.com>

# User not found:
python -m app.main users get 999
# Error: User 999 not found
```

### List Users

```bash
python -m app.main users list

# Output:
# Users:
#   1: Alice Smith <alice@example.com>
#   2: Bob Jones <bob@example.com>
```

### Health Check

```bash
python -m app.main health

# Output:
# Status: healthy
# Profile: development
```

## Testing with Fakes

Tests use the TEST profile to get fast, deterministic fakes:

```python
# tests/test_cli.py
def test_create_user(runner, db, email):
    result = runner.invoke(cli, ["users", "create", "Alice", "alice@example.com"])

    assert result.exit_code == 0
    assert len(db.users) == 1
    assert len(email.sent_emails) == 1
```

## Typer Compatibility

Since Typer is built on Click, this integration works with Typer:

```python
import typer
import click
from dioxide.click import configure_dioxide, with_scope

container = configure_dioxide(profile=Profile.PRODUCTION)
app = typer.Typer()


@click.command()
@with_scope(container)
@click.argument("name")
def greet(scope, name):
    service = scope.resolve(GreetingService)
    typer.echo(service.greet(name))


app.command()(greet)
```

## Learn More

- [dioxide Documentation](https://github.com/mikelane/dioxide)
- [Click Documentation](https://click.palletsprojects.com/)
- [Hexagonal Architecture](https://alistair.cockburn.us/hexagonal-architecture/)
