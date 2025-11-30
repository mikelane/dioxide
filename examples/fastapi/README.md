# FastAPI + dioxide: Hexagonal Architecture Example

This example demonstrates how to build a production-ready FastAPI application using **dioxide** for dependency injection with hexagonal architecture (ports and adapters pattern).

## What This Example Demonstrates

1. **Hexagonal Architecture**: Clean separation between domain logic and infrastructure
2. **Profile-Based Configuration**: Different adapters for production, development, and testing
3. **Lifecycle Management**: Proper initialization and cleanup of resources
4. **Testing with Fakes**: Fast, deterministic tests without mocks
5. **FastAPI Integration**: Container lifecycle integrated with FastAPI lifespan

## Quick Start

### Installation

```bash
# Clone the repository
cd examples/fastapi

# Install dependencies
pip install -r requirements-dev.txt

# Or using uv (faster)
uv pip install -r requirements-dev.txt
```

### Running the Application

```bash
# Development mode (logging email adapter, in-memory database)
PROFILE=development uvicorn app.main:app --reload

# Production mode (SendGrid + PostgreSQL - requires configuration)
PROFILE=production DATABASE_URL=postgresql://... SENDGRID_API_KEY=... uvicorn app.main:app

# Test mode (for running tests)
PROFILE=test pytest
```

### Testing

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test class
pytest tests/test_api.py::DescribeUserCreation -v
```

## Architecture Overview

### Hexagonal Architecture Layers

```
┌─────────────────────────────────────────────────────────────┐
│                    HTTP Layer (FastAPI)                      │
│                  app/main.py - API routes                    │
└────────────────────────────┬────────────────────────────────┘
                             │
                             │ Depends on
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                     Domain Layer (Pure)                      │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Services (app/domain/services.py)                     │ │
│  │  - UserService: Business logic                         │ │
│  │  - No framework dependencies                           │ │
│  │  - Depends only on ports (interfaces)                  │ │
│  └────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Ports (app/domain/ports.py)                           │ │
│  │  - ConfigPort: Protocol for configuration              │ │
│  │  - DatabasePort: Protocol for data persistence         │ │
│  │  - EmailPort: Protocol for email sending               │ │
│  └────────────────────────────────────────────────────────┘ │
└────────────────────────────┬────────────────────────────────┘
                             │
                             │ Implemented by
                             ▼
┌─────────────────────────────────────────────────────────────┐
│              Adapter Layer (Profile-Specific)                │
│  ┌─────────────────────┬─────────────────┬────────────────┐ │
│  │   Production        │  Development    │     Test       │ │
│  │  (PRODUCTION)       │ (DEVELOPMENT)   │    (TEST)      │ │
│  ├─────────────────────┼─────────────────┼────────────────┤ │
│  │ PostgresAdapter     │ PostgresAdapter │ FakeDatabase   │ │
│  │ SendGridAdapter     │ LoggingEmail    │ FakeEmail      │ │
│  └─────────────────────┴─────────────────┴────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Directory Structure

```
app/
├── main.py              # FastAPI app + container setup
├── domain/
│   ├── ports.py        # Port definitions (Protocols) including ConfigPort
│   └── services.py     # Business logic (@service)
└── adapters/
    ├── config.py       # Configuration adapters (demonstrates constructor injection)
    ├── postgres.py     # Production database (@adapter + @lifecycle, injects ConfigPort)
    ├── sendgrid.py     # Production email (@adapter, injects ConfigPort)
    ├── logging_email.py # Development email (@adapter, no dependencies)
    └── fakes.py        # Test adapters (@adapter)

tests/
├── conftest.py         # Pytest configuration + fixtures
└── test_api.py         # Fast tests using fakes
```

## How It Works

### 1. Define Ports (Interfaces)

Ports are pure protocol definitions - no implementation details:

```python
# app/domain/ports.py
from typing import Protocol

class DatabasePort(Protocol):
    async def create_user(self, name: str, email: str) -> dict: ...
    async def get_user(self, user_id: str) -> dict | None: ...

class EmailPort(Protocol):
    async def send_welcome_email(self, to: str, name: str) -> None: ...
```

### 2. Implement Domain Services

Services contain business logic and depend only on ports:

```python
# app/domain/services.py
from dioxide import service

@service
class UserService:
    def __init__(self, db: DatabasePort, email: EmailPort):
        self.db = db
        self.email = email

    async def register_user(self, name: str, email: str) -> dict:
        # Business logic - doesn't know which adapters are active
        user = await self.db.create_user(name, email)
        await self.email.send_welcome_email(email, name)
        return user
```

### 3. Create Adapters for Each Profile

Adapters implement ports with profile-specific behavior:

```python
# Production adapter
from dioxide import adapter, lifecycle, Profile

@adapter.for_(DatabasePort, profile=Profile.PRODUCTION)
@lifecycle
class PostgresAdapter:
    async def initialize(self):
        # Connect to PostgreSQL
        self.pool = await asyncpg.create_pool(...)

    async def dispose(self):
        # Close connection pool
        await self.pool.close()

    async def create_user(self, name: str, email: str) -> dict:
        # Real database insert
        ...

# Test adapter (fake)
@adapter.for_(DatabasePort, profile=Profile.TEST)
class FakeDatabaseAdapter:
    def __init__(self):
        self.users = {}  # In-memory storage

    async def create_user(self, name: str, email: str) -> dict:
        # Fast, deterministic, no I/O
        user = {"id": str(len(self.users) + 1), "name": name, "email": email}
        self.users[user["id"]] = user
        return user
```

### 4. Set Up FastAPI with dioxide.fastapi Integration

The `dioxide.fastapi` module provides one-line integration:

```python
# app/main.py
from dioxide import Profile
from dioxide.fastapi import DioxideMiddleware, Inject

app = FastAPI()

# One-line setup - handles lifecycle, middleware, and scanning
profile = Profile(os.getenv("PROFILE", "development"))
app.add_middleware(DioxideMiddleware, profile=profile, packages=["app"])

@app.post("/users")
async def create_user(
    request: CreateUserRequest,
    service: UserService = Inject(UserService)  # Clean injection!
):
    return await service.register_user(request.name, request.email)
```

This automatically:
- Scans for components in the specified packages
- Sets up container lifecycle with FastAPI lifespan
- Adds middleware for REQUEST-scoped components
- Initializes `@lifecycle` adapters on startup
- Disposes `@lifecycle` adapters on shutdown

### 5. Write Fast Tests Using Fakes

Tests use the TEST profile to get fast, deterministic fakes:

```python
# tests/test_api.py
def test_create_user(client, db, email):
    # Make HTTP request
    response = client.post("/users", json={"name": "Alice", "email": "alice@example.com"})

    # Verify response
    assert response.status_code == 201

    # Verify fake state (no database query, instant)
    assert len(db.users) == 1
    assert len(email.sent_emails) == 1
```

## Key Features

### Profile-Based Configuration

Different environments use different adapters:

| Profile | Config | Database | Email | Use Case |
|---------|--------|----------|-------|----------|
| `production` | Env vars | PostgreSQL | SendGrid | Real production deployment |
| `development` | Defaults + env | In-memory | Console logging | Local development |
| `test` | In-memory fake | In-memory fake | Recording fake | Automated testing |
| `ci` | Defaults + env | In-memory | Console logging | CI/CD pipelines |

**Constructor Injection**: PostgresAdapter and SendGridAdapter inject ConfigPort to get their settings. This is cleaner than reading `os.environ` directly because tests can provide fake config.

### Lifecycle Management

Adapters that need initialization/cleanup use `@lifecycle`:

```python
@adapter.for_(DatabasePort, profile=Profile.PRODUCTION)
@lifecycle
class PostgresAdapter:
    async def initialize(self):
        # Called on container start
        self.pool = await asyncpg.create_pool(...)

    async def dispose(self):
        # Called on container stop
        await self.pool.close()
```

The `DioxideMiddleware` automatically integrates the container lifecycle with FastAPI:

```
App Start → lifespan.__aenter__ → container.start() → initialize() on adapters → Ready
App Stop  → lifespan.__aexit__  → container.stop()  → dispose() on adapters → Shutdown
```

### Constructor Dependency Injection

Adapters can depend on other adapters or services through constructor injection. dioxide automatically resolves and injects dependencies based on type hints.

**Example: Config Adapter Pattern**

This example uses a `ConfigPort` that other adapters depend on:

```python
# app/domain/ports.py
class ConfigPort(Protocol):
    def get(self, key: str, default: str = "") -> str: ...

# app/adapters/config.py - Configuration adapter
@adapter.for_(ConfigPort, profile=Profile.PRODUCTION)
class EnvConfigAdapter:
    def get(self, key: str, default: str = "") -> str:
        return os.environ.get(key, default)

@adapter.for_(ConfigPort, profile=Profile.TEST)
class FakeConfigAdapter:
    def __init__(self):
        self.values = {"SENDGRID_API_KEY": "test-key"}

    def get(self, key: str, default: str = "") -> str:
        return self.values.get(key, default)

# app/adapters/sendgrid.py - Depends on ConfigPort
@adapter.for_(EmailPort, profile=Profile.PRODUCTION)
class SendGridAdapter:
    def __init__(self, config: ConfigPort) -> None:  # <-- Auto-injected!
        self.api_key = config.get("SENDGRID_API_KEY")
```

**How it works:**

1. When `SendGridAdapter` is resolved, dioxide sees it needs `ConfigPort`
2. dioxide looks up `ConfigPort` in the container
3. For PRODUCTION profile, it finds `EnvConfigAdapter`
4. Creates `EnvConfigAdapter` and passes it to `SendGridAdapter.__init__`

**Key insight:** The dependency (`ConfigPort`) must be registered in the container. Use:
- `@adapter.for_(Port, profile=...)` for infrastructure dependencies
- `@service` for domain logic dependencies
- `container.register_singleton()` for external types

**Test fakes often have no dependencies:**

```python
@adapter.for_(EmailPort, profile=Profile.TEST)
class FakeEmailAdapter:
    def __init__(self):  # No dependencies needed!
        self.sent_emails = []
```

### Testing with Fakes (Not Mocks)

This example uses **fakes** instead of mocks:

**Fakes** (what we use):
- Real implementations with shortcuts (in-memory instead of database)
- Test actual behavior, not implementation details
- No mocking framework needed
- Reusable across many tests
- Fast and deterministic

**Mocks** (what we avoid):
- Behavior verification objects
- Test implementation details (which methods were called)
- Require mocking framework
- Brittle - break when refactoring
- Harder to understand

Example fake:

```python
@adapter.for_(EmailPort, profile=Profile.TEST)
class FakeEmailAdapter:
    def __init__(self):
        self.sent_emails = []  # Real storage, just in-memory

    async def send_welcome_email(self, to: str, name: str):
        # Real implementation - just records instead of sending
        self.sent_emails.append({"to": to, "name": name, "type": "welcome"})

    def was_welcome_email_sent_to(self, email: str) -> bool:
        # Convenience method for tests
        return any(e["to"] == email and e["type"] == "welcome" for e in self.sent_emails)
```

## API Endpoints

### Create User

```bash
POST /users
Content-Type: application/json

{
    "name": "Alice Smith",
    "email": "alice@example.com"
}

# Response: 201 Created
{
    "id": "1",
    "name": "Alice Smith",
    "email": "alice@example.com"
}
```

### Get User

```bash
GET /users/1

# Response: 200 OK
{
    "id": "1",
    "name": "Alice Smith",
    "email": "alice@example.com"
}
```

### List Users

```bash
GET /users

# Response: 200 OK
[
    {
        "id": "1",
        "name": "Alice Smith",
        "email": "alice@example.com"
    },
    {
        "id": "2",
        "name": "Bob Jones",
        "email": "bob@example.com"
    }
]
```

### Health Check

```bash
GET /health

# Response: 200 OK
{
    "status": "healthy",
    "profile": "development"
}
```

## Common Tasks

### Running in Different Profiles

```bash
# Development (logging email, in-memory DB)
PROFILE=development uvicorn app.main:app --reload

# Production (real database and email)
PROFILE=production \
  DATABASE_URL=postgresql://user:pass@localhost/db \
  SENDGRID_API_KEY=SG.xxx... \
  SENDGRID_FROM_EMAIL=noreply@example.com \
  uvicorn app.main:app --host 0.0.0.0 --port 8000

# Test (fakes for testing)
PROFILE=test pytest
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=term-missing

# Run specific test
pytest tests/test_api.py::DescribeUserCreation::it_creates_a_user_and_sends_welcome_email -v

# Run tests and see print statements
pytest -s
```

### Code Quality

```bash
# Format code
ruff format app/ tests/

# Lint
ruff check app/ tests/

# Type check
mypy app/
```

## Extending the Example

### Adding a New Port

1. Define the port in `app/domain/ports.py`:

```python
class CachePort(Protocol):
    async def get(self, key: str) -> str | None: ...
    async def set(self, key: str, value: str, ttl: int = 3600) -> None: ...
```

2. Create adapters for each profile:

```python
# Production: Redis
@adapter.for_(CachePort, profile=Profile.PRODUCTION)
class RedisAdapter:
    ...

# Test: In-memory
@adapter.for_(CachePort, profile=Profile.TEST)
class FakeCacheAdapter:
    def __init__(self):
        self.cache = {}
```

3. Inject into services:

```python
@service
class UserService:
    def __init__(self, db: DatabasePort, email: EmailPort, cache: CachePort):
        ...
```

### Adding a New Endpoint

1. Add method to service:

```python
@service
class UserService:
    async def update_user(self, user_id: str, name: str) -> dict:
        user = await self.db.get_user(user_id)
        if not user:
            raise ValueError("User not found")
        user["name"] = name
        await self.db.update_user(user)
        return user
```

2. Add route to FastAPI:

```python
from dioxide.fastapi import Inject

@app.put("/users/{user_id}")
async def update_user(
    user_id: str,
    request: UpdateUserRequest,
    service: UserService = Inject(UserService)
):
    return await service.update_user(user_id, request.name)
```

3. Add tests:

```python
def test_update_user(client):
    # Create user
    response = client.post("/users", json={"name": "Alice", "email": "alice@example.com"})
    user_id = response.json()["id"]

    # Update user
    response = client.put(f"/users/{user_id}", json={"name": "Alice Updated"})
    assert response.status_code == 200
    assert response.json()["name"] == "Alice Updated"
```

## Troubleshooting

### "Module 'app' has no attribute 'domain'"

Make sure you're running from the `examples/fastapi` directory:

```bash
cd examples/fastapi
pytest
```

### Tests failing with "Container not initialized"

Ensure `PROFILE=test` is set before importing the app. This is handled in `conftest.py`:

```python
import os
os.environ["PROFILE"] = "test"
from app.main import app

# With dioxide.fastapi, container is stored in app.state
container = app.state.dioxide_container
```

### "No adapter found for port"

Check that:
1. Adapter is decorated with `@adapter.for_(Port, profile=...)`
2. Adapter file is imported (or in `app` package so `container.scan()` finds it)
3. Profile matches (e.g., `PROFILE=test` matches `profile=Profile.TEST`)

### Lifecycle methods not called

Ensure:
1. Adapter has `@lifecycle` decorator
2. `DioxideMiddleware` was added to the app (sets up lifespan automatically)
3. Methods are named `initialize()` and `dispose()`
4. Methods are async (`async def`)

## Production Deployment

### Environment Variables

Required for production:

```bash
PROFILE=production
DATABASE_URL=postgresql://user:password@host:port/database
SENDGRID_API_KEY=SG.your_api_key_here
SENDGRID_FROM_EMAIL=noreply@yourdomain.com
```

### Docker Example

```dockerfile
FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/

ENV PROFILE=production

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Database Setup (PostgreSQL)

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

Then update `PostgresAdapter` to use real asyncpg queries.

## Key Takeaways

1. **Hexagonal architecture** makes your code testable and portable
2. **Ports** (interfaces) define what adapters must implement
3. **Profile-based configuration** selects adapters per environment
4. **Fakes** make tests fast and deterministic without mocks
5. **Lifecycle management** ensures clean resource initialization/cleanup
6. **Domain layer** stays pure - no framework dependencies
7. **Tests run in milliseconds** because fakes do no I/O

## Learn More

- [dioxide Documentation](https://github.com/mikelane/dioxide)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Hexagonal Architecture](https://alistair.cockburn.us/hexagonal-architecture/)
- [Ports and Adapters Pattern](https://en.wikipedia.org/wiki/Hexagonal_architecture_(software))

## License

This example is part of the dioxide project and is provided as-is for educational purposes.
