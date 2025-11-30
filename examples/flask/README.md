# Flask + dioxide: Hexagonal Architecture Example

This example demonstrates how to build a production-ready Flask application using **dioxide** for dependency injection with hexagonal architecture (ports and adapters pattern).

## What This Example Demonstrates

1. **Hexagonal Architecture**: Clean separation between domain logic and infrastructure
2. **Profile-Based Configuration**: Different adapters for production, development, and testing
3. **Lifecycle Management**: Proper initialization and cleanup of resources
4. **Testing with Fakes**: Fast, deterministic tests without mocks
5. **Flask Integration**: Container lifecycle integrated with Flask app configuration

## Quick Start

### Installation

```bash
# Clone the repository
cd examples/flask

# Install dependencies
pip install -r requirements-dev.txt

# Or using uv (faster)
uv pip install -r requirements-dev.txt
```

### Running the Application

```bash
# Development mode (logging email adapter, in-memory database)
PROFILE=development flask --app app.main:app run --reload

# Production mode (real database and email)
PROFILE=production DATABASE_URL=postgresql://... SENDGRID_API_KEY=... flask --app app.main:app run

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

### Directory Structure

```
app/
├── main.py              # Flask app + container setup
├── domain/
│   ├── ports.py         # Port definitions (Protocols)
│   └── services.py      # Business logic (@service)
└── adapters/
    ├── logging_email.py # Development email (@adapter)
    └── fakes.py         # Test adapters (@adapter)

tests/
├── conftest.py          # Pytest configuration + fixtures
└── test_api.py          # Fast tests using fakes
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

### 4. Set Up Flask with dioxide.flask Integration

```python
# app/main.py
from flask import Flask, jsonify, request
from dioxide import Profile
from dioxide.flask import configure_dioxide, inject

app = Flask(__name__)

# Get profile from environment
profile = Profile(os.getenv("PROFILE", "development"))
configure_dioxide(app, profile=profile, packages=["app"])

@app.route("/users", methods=["POST"])
def create_user():
    service = inject(UserService)
    data = request.get_json()
    user = service.register_user(data["name"], data["email"])
    return jsonify(user), 201
```

## Key Differences from FastAPI Integration

| Feature | FastAPI | Flask |
|---------|---------|-------|
| Setup | `app.add_middleware(DioxideMiddleware, ...)` | `configure_dioxide(app, ...)` |
| Injection | `Inject(Type)` returns FastAPI `Depends` | `inject(Type)` returns instance directly |
| Async | Native async/await | Sync (uses `asyncio.run()` wrapper) |
| Request scope | Via ASGI middleware | Via Flask `g` object |

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

## Testing with Fakes

Tests use the TEST profile to get fast, deterministic fakes:

```python
# tests/test_api.py
def test_create_user(client, db, email):
    response = client.post("/users", json={"name": "Alice", "email": "alice@example.com"})

    assert response.status_code == 201
    assert len(db.users) == 1
    assert len(email.sent_emails) == 1
```

## Learn More

- [dioxide Documentation](https://github.com/mikelane/dioxide)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [Hexagonal Architecture](https://alistair.cockburn.us/hexagonal-architecture/)
