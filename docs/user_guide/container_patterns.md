# Container Patterns: Global vs Instance

This guide clarifies when to use the **global container** (`from dioxide import container`) versus
**instance containers** (`Container()`), and the testing implications of each pattern.

## TL;DR: Which Should I Use?

| Pattern | Best For | Testing Approach |
|---------|----------|------------------|
| **Instance Container** | Most applications, testing, libraries | `fresh_container()` or new `Container()` per test |
| **Global Container** | Simple scripts, CLI tools, single-file apps | `reset_global_container()` between tests |

**Default recommendation**: Use **instance containers**. They provide better isolation,
are easier to test, and prevent state leakage between components.

---

## The Two Patterns

### Pattern 1: Instance Container (Recommended)

Create a new `Container()` instance when you need it. Each instance has its own
singleton cache and registration state.

```python
from dioxide import Container, Profile

# Create a fresh container
container = Container()
container.scan(profile=Profile.PRODUCTION)

# Resolve services
user_service = container.resolve(UserService)
```

**Characteristics:**
- Each `Container()` is independent
- Singletons are scoped to the container instance
- No global state to manage
- Easy to create isolated test containers

### Pattern 2: Global Container

Import the pre-created global container singleton. Useful for simple applications
where explicit container passing is overhead.

```python
from dioxide import container, Profile

# Use the global singleton
container.scan(profile=Profile.PRODUCTION)

# Resolve services
user_service = container.resolve(UserService)
```

**Characteristics:**
- Single shared instance across your application
- Singletons persist for the process lifetime
- Requires explicit reset for test isolation
- Convenient for simple scripts and CLI tools

---

## When to Use Each Pattern

### Use Instance Container When...

1. **Building a library or package**
   - Libraries should not pollute global state
   - Users should control container lifecycle

2. **Writing tests** (strongly recommended)
   - Each test gets a fresh container with `fresh_container()`
   - No state leakage between tests
   - Parallel tests work correctly

3. **Running multiple profiles simultaneously**
   - Need both production and test containers active
   - Integration testing with mixed configurations

4. **Building a web application with request scoping**
   - Each request gets its own scoped container
   - Clean request isolation

5. **When you want explicit dependency tracking**
   - Clear ownership of the container
   - Easier to reason about lifecycle

```python
# Example: Web application with request scoping
from dioxide import Container, Profile

def create_app():
    # Application-level container
    app_container = Container()
    app_container.scan(profile=Profile.PRODUCTION)
    return app_container

# Each request can create a scoped child
async def handle_request(app_container):
    async with app_container.create_scope() as request_container:
        service = request_container.resolve(RequestHandler)
        return await service.handle()
```

### Use Global Container When...

1. **Building a simple script**
   - Single-file applications
   - Quick prototypes

2. **CLI applications**
   - Command-line tools with Click integration
   - One-shot execution with no tests

3. **When passing container explicitly is tedious**
   - Small applications where DI is simple
   - Rapid prototyping

4. **Module-level initialization patterns**
   - Legacy code integration
   - Gradual adoption of DI

```python
# Example: Simple CLI script
from dioxide import container, Profile, adapter, service
from typing import Protocol

class GreeterPort(Protocol):
    def greet(self, name: str) -> str: ...

@adapter.for_(GreeterPort, profile=Profile.PRODUCTION)
class FormalGreeter:
    def greet(self, name: str) -> str:
        return f"Good day, {name}."

@service
class CLI:
    def __init__(self, greeter: GreeterPort):
        self.greeter = greeter

    def run(self, name: str):
        print(self.greeter.greet(name))

# Simple one-liner usage
container.scan(profile=Profile.PRODUCTION)
container.resolve(CLI).run("Alice")
```

---

## Testing Patterns

Testing is where the choice between global and instance containers matters most.

### Testing with Instance Containers (Recommended)

Use `fresh_container()` from `dioxide.testing` for completely isolated tests:

```python
import pytest
from dioxide import Profile
from dioxide.testing import fresh_container

@pytest.fixture
async def container():
    """Fresh container per test - complete isolation."""
    async with fresh_container(profile=Profile.TEST) as c:
        yield c
    # Automatic cleanup

async def test_user_registration(container):
    service = container.resolve(UserService)
    email = container.resolve(EmailPort)  # Gets FakeEmailAdapter

    await service.register_user("alice@example.com", "Alice")

    # Verify using fake's captured state
    assert len(email.sent_emails) == 1
    assert email.sent_emails[0]["to"] == "alice@example.com"

async def test_another_feature(container):
    # Fresh container - email.sent_emails is empty!
    email = container.resolve(EmailPort)
    assert len(email.sent_emails) == 0  # No state from previous test
```

**Or use the built-in pytest fixtures:**

```python
# conftest.py
pytest_plugins = ['dioxide.testing']

# test_my_service.py
async def test_with_fixture(dioxide_container):
    dioxide_container.scan(profile=Profile.TEST)
    service = dioxide_container.resolve(MyService)
    # ... test with fresh container
```

**Available fixtures:**
- `dioxide_container` - Fresh container per test (function-scoped)
- `fresh_container_fixture` - Alias for `dioxide_container`
- `dioxide_container_session` - Shared container across tests (session-scoped)

### Testing with Global Container (If You Must)

If you're using the global container pattern, you MUST reset it between tests:

```python
import pytest
from dioxide import container, reset_global_container, Profile

@pytest.fixture(autouse=True)
def isolated_container():
    """Reset global container before and after each test."""
    reset_global_container()  # Start fresh
    container.scan(profile=Profile.TEST)
    yield
    reset_global_container()  # Clean up

def test_user_registration():
    service = container.resolve(UserService)
    # ... test code ...

def test_another_feature():
    # Global container was reset - state is clean
    service = container.resolve(UserService)
    # ... test code ...
```

**Warning**: The global container pattern has significant testing pitfalls:

1. **State leakage**: Forgetting to reset causes flaky tests
2. **Parallel test issues**: Multiple tests accessing global state can race
3. **Hard to debug**: Failures depend on test execution order
4. **Fixture order matters**: `autouse=True` must run before other fixtures

---

## Mixing Patterns

In larger applications, you might use both patterns:

```python
from dioxide import container, Container, Profile

# Global container for production app startup
container.scan(profile=Profile.PRODUCTION)

# Instance container for isolated test scenarios
def create_test_container():
    test_container = Container()
    test_container.scan(profile=Profile.TEST)
    return test_container
```

**This is valid but be careful:**
- Don't resolve from both containers expecting shared singletons
- Each container has its own singleton cache
- Clear documentation helps team members understand which to use where

---

## Migration Guide

### From Global to Instance Pattern

If you're currently using the global container and want to switch to instance containers:

**Before (global):**
```python
# app.py
from dioxide import container, Profile

container.scan(profile=Profile.PRODUCTION)

# other_module.py
from dioxide import container

def do_something():
    service = container.resolve(SomeService)
    # ...
```

**After (instance):**
```python
# app.py
from dioxide import Container, Profile

def create_container(profile: Profile = Profile.PRODUCTION) -> Container:
    c = Container()
    c.scan(profile=profile)
    return c

# Create once at startup
app_container = create_container()

# other_module.py
def do_something(container: Container):
    service = container.resolve(SomeService)
    # ...

# Or use dependency injection to get the container
```

### From Instance to Global Pattern

If you have simple needs and instance passing is tedious:

**Before (instance):**
```python
# Every function needs the container
def handle_request(container):
    service = container.resolve(SomeService)
    # ...

def another_function(container):
    other = container.resolve(OtherService)
    # ...
```

**After (global):**
```python
from dioxide import container, Profile

# Scan once at startup
container.scan(profile=Profile.PRODUCTION)

# Use anywhere
def handle_request():
    service = container.resolve(SomeService)
    # ...

def another_function():
    other = container.resolve(OtherService)
    # ...
```

---

## Summary

| Aspect | Instance Container | Global Container |
|--------|-------------------|------------------|
| **Creation** | `Container()` | `from dioxide import container` |
| **Isolation** | Complete per instance | Shared process-wide |
| **Testing** | `fresh_container()` | `reset_global_container()` |
| **Singletons** | Per container instance | Per process |
| **Recommended for** | Libraries, web apps, tests | Scripts, CLIs, prototypes |
| **Pitfalls** | Must pass container explicitly | State leakage, test flakiness |

**When in doubt, use instance containers.** They're safer, more explicit, and easier
to test. The global container is a convenience for simple cases where the overhead
of passing containers around isn't worth it.

---

## See Also

- {doc}`/docs/TESTING_GUIDE` - Comprehensive testing patterns
- {func}`dioxide.testing.fresh_container` - Context manager for test isolation
- {func}`dioxide.reset_global_container` - Reset global container state
- {doc}`getting_started` - Introduction to dioxide
