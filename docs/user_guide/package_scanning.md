# Package Scanning

This guide explains how `container.scan()` works, including its behavior, side effects, and best practices for safe, performant usage.

## Overview

Package scanning is the primary mechanism for discovering `@adapter` and `@service` decorated classes in your codebase. When you call `container.scan()`, dioxide finds all decorated components and registers them for dependency injection.

```python
from dioxide import Container, Profile

container = Container()
container.scan(package="myapp", profile=Profile.PRODUCTION)
```

## How Scanning Works

### Step 1: Module Import

When you provide a `package` parameter, dioxide **imports all modules** in that package and its sub-packages. This is done recursively using Python's `pkgutil.walk_packages()`.

```python
# This:
container.scan(package="myapp.adapters")

# Internally does something like:
import myapp.adapters
import myapp.adapters.email
import myapp.adapters.database
import myapp.adapters.cache
# ... every module in the package
```

### Step 2: Decorator Execution

When modules are imported, Python executes module-level code, including decorators. The `@adapter.for_()` and `@service` decorators register classes in global registries.

```python
# myapp/adapters/email.py
from dioxide import adapter, Profile

# This decorator executes during import, registering the class
@adapter.for_(EmailPort, profile=Profile.PRODUCTION)
class SendGridAdapter:
    ...
```

### Step 3: Registry Scanning

After imports complete, dioxide scans the global registries to find:
- All `@service` decorated classes
- All `@adapter.for_()` decorated classes matching the specified profile

### Step 4: Container Registration

Finally, dioxide registers discovered components with the container, making them available for dependency resolution.

## What Gets Scanned?

| With `package=` parameter | Behavior |
|---------------------------|----------|
| `package="myapp"` | Imports `myapp`, `myapp.adapters`, `myapp.services`, etc. (recursive) |
| `package="myapp.adapters"` | Only imports `myapp.adapters` and its sub-packages |
| `package=None` (default) | **Does NOT import** - only scans already-imported modules |

### No Package Parameter (Default Behavior)

When you call `scan()` without a package parameter, dioxide scans only components from **already-imported modules**:

```python
# These modules must be imported BEFORE scan() is called
from myapp.adapters import email, database
from myapp.services import user

container = Container()
container.scan(profile=Profile.PRODUCTION)  # Finds SendGridAdapter, etc.
```

This is useful when your application framework (FastAPI, Django, etc.) already imports your modules.

### With Package Parameter

When you specify a package, dioxide **actively imports** all modules:

```python
# No prior imports needed - dioxide will import everything
container = Container()
container.scan(package="myapp", profile=Profile.PRODUCTION)
```

## Side Effects Warning

**Importing modules executes module-level code.** This can have unintended side effects.

### Module-Level Code Execution

```python
# myapp/dangerous.py
print("This runs when the module is imported!")
some_connection = connect_to_database()  # Side effect!
expensive_result = compute_something()   # Runs every import!
```

When you scan a package containing this module, all module-level code executes.

### Common Side Effects to Avoid

| Side Effect | Problem | Solution |
|-------------|---------|----------|
| Database connections | Connection created before app is ready | Use `@lifecycle` initialize |
| File I/O | Files opened/created unexpectedly | Move to class `__init__` or method |
| Network requests | Requests during startup | Defer to runtime |
| Global state mutation | Unpredictable state | Encapsulate in classes |
| Print statements | Noisy logs during tests | Remove or use logging |

### Safe Module Pattern

```python
# myapp/adapters/database.py

from dioxide import adapter, lifecycle, Profile

# NO module-level side effects here!

@adapter.for_(DatabasePort, profile=Profile.PRODUCTION)
@lifecycle
class PostgresAdapter:
    """Database adapter with proper lifecycle management."""

    def __init__(self, config: ConfigPort) -> None:
        # Save config but don't connect yet
        self.config = config
        self.connection = None

    async def initialize(self) -> None:
        """Called by container.start() - safe place for connections."""
        self.connection = await create_connection(self.config.database_url)

    async def dispose(self) -> None:
        """Called by container.stop() - cleanup connections."""
        if self.connection:
            await self.connection.close()
```

## Controlling Scan Scope

### Narrow Scanning (Recommended)

Scan only the packages containing decorated components:

```python
# Good: Scan specific packages
container.scan(package="myapp.adapters", profile=Profile.PRODUCTION)
container.scan(package="myapp.services", profile=Profile.PRODUCTION)

# Or even more specific
container.scan(package="myapp.adapters.infrastructure", profile=Profile.PRODUCTION)
```

### Wide Scanning (Use Carefully)

Scanning your entire application works but may import more than needed:

```python
# Works, but imports EVERYTHING in myapp
container.scan(package="myapp", profile=Profile.PRODUCTION)
```

### Multiple Scans

You can call `scan()` multiple times to build up registrations:

```python
container = Container()

# Scan different packages
container.scan(package="myapp.adapters.production", profile=Profile.PRODUCTION)
container.scan(package="myapp.services", profile=Profile.PRODUCTION)
container.scan(package="shared.infrastructure", profile=Profile.PRODUCTION)
```

## Security: Restricting Scannable Packages

Use `allowed_packages` to prevent arbitrary code execution via package names:

```python
# Only allow scanning your application packages
container = Container(allowed_packages=["myapp", "tests.fixtures"])

# These work:
container.scan(package="myapp.adapters")
container.scan(package="tests.fixtures.fakes")

# This raises ValueError - not in allowed list:
container.scan(package="os")  # Blocked!
container.scan(package="subprocess")  # Blocked!
```

### Why This Matters

If package names come from external input (config files, environment variables), an attacker could potentially execute arbitrary code:

```python
# DANGEROUS: User input controls what gets imported
package = os.environ.get("SCAN_PACKAGE", "myapp")
container.scan(package=package)  # Could import malicious code!

# SAFE: Restrict to known packages
container = Container(allowed_packages=["myapp"])
container.scan(package=package)  # ValueError if package not in list
```

### Allowed Packages Matching

The check uses prefix matching:

```python
Container(allowed_packages=["myapp"])

# Matches:
"myapp" -> OK
"myapp.adapters" -> OK
"myapp.adapters.email" -> OK

# Does NOT match:
"myapplication" -> Blocked (not a prefix match)
"other.myapp" -> Blocked
```

## Performance Considerations

### Startup Time

Package scanning imports modules, which takes time. Larger packages = longer startup.

| Approach | Startup Time | Use Case |
|----------|-------------|----------|
| Narrow scan (`myapp.adapters`) | Fast | Most applications |
| Wide scan (`myapp`) | Slower | Simple apps, convenience |
| No package scan (pre-imported) | Fastest | Framework handles imports |

### Benchmarks

Typical scanning performance (depends on package size):

- Small package (10 modules): ~5-20ms
- Medium package (50 modules): ~20-100ms
- Large package (200+ modules): ~100-500ms

### Optimization Tips

1. **Scan narrow packages**: `myapp.adapters` not `myapp`
2. **Avoid heavy imports**: Keep modules lightweight
3. **Defer expensive operations**: Use `@lifecycle` for initialization
4. **Pre-import in frameworks**: Let FastAPI/Django handle imports

## Explicit Registration Alternative

For maximum control, register components manually without scanning:

```python
from dioxide import Container, Profile

container = Container()

# Register instance directly
container.register_instance(ConfigPort, my_config)

# Register singleton factory (called once, cached)
container.register_singleton(DatabasePort, lambda: PostgresAdapter())

# Register factory (new instance each time)
container.register_factory(RequestHandler, lambda: RequestHandlerImpl())

# Now resolve - no scan() needed
service = container.resolve(UserService)
```

### When to Use Explicit Registration

| Use Case | Recommended Approach |
|----------|---------------------|
| Most applications | `scan()` with decorators |
| Third-party classes | `register_instance()` or `register_singleton()` |
| Conditional registration | Explicit registration |
| Testing with specific fakes | `register_instance()` |
| Maximum startup performance | Pre-import + explicit registration |

## Best Practices Summary

1. **Scan narrow packages**: Target specific directories, not entire app
2. **Avoid module-level side effects**: No I/O, connections, or state mutations at module level
3. **Use `@lifecycle`**: For components needing initialization/cleanup
4. **Use `allowed_packages`**: When package names come from external sources
5. **Scan early**: During application startup, not during request handling
6. **Prefer decorators**: `@adapter.for_()` and `@service` are clearer than explicit registration

## Common Patterns

### FastAPI Application

```python
from fastapi import FastAPI
from dioxide import Container, Profile

app = FastAPI()

@app.on_event("startup")
async def startup():
    container = Container()
    container.scan(package="myapp.adapters", profile=Profile.PRODUCTION)
    container.scan(package="myapp.services", profile=Profile.PRODUCTION)
    await container.start()
    app.state.container = container

@app.on_event("shutdown")
async def shutdown():
    await app.state.container.stop()
```

### Testing with Fresh Container

```python
import pytest
from dioxide import Container, Profile

@pytest.fixture
async def container():
    """Fresh container per test with test profile."""
    c = Container()
    c.scan(package="myapp", profile=Profile.TEST)
    async with c:
        yield c
```

### CLI Application

```python
import click
from dioxide import Container, Profile

@click.command()
def main():
    container = Container(allowed_packages=["myapp"])
    container.scan(package="myapp", profile=Profile.PRODUCTION)

    service = container.resolve(UserService)
    service.run()

if __name__ == "__main__":
    main()
```

## Troubleshooting

### "Module not found" During Scan

```
ImportError: Package 'myapp.adapters' not found
```

**Cause**: The package path is incorrect or the package is not installed.

**Solution**: Verify the package exists and is importable:
```python
import myapp.adapters  # Does this work?
```

### Components Not Being Discovered

**Cause**: Modules not imported before `scan()` (when not using `package=`).

**Solution**: Either:
1. Add `package="myapp"` to explicitly import modules
2. Ensure modules are imported elsewhere before `scan()` is called

### "Ambiguous adapter registration" Error

```
ValueError: Ambiguous adapter registration for port EmailPort for profile 'production':
multiple adapters found (SendGridAdapter, MailgunAdapter)
```

**Cause**: Two adapters registered for the same port and profile.

**Solution**: Use different profiles or consolidate to one adapter:
```python
@adapter.for_(EmailPort, profile=Profile.PRODUCTION)
class SendGridAdapter: ...  # Use this one

# Remove or change profile:
@adapter.for_(EmailPort, profile=Profile.STAGING)  # Different profile
class MailgunAdapter: ...
```

### Package Blocked by allowed_packages

```
ValueError: Package 'os' is not in allowed_packages list. Allowed prefixes: ['myapp']
```

**Cause**: Trying to scan a package not in the allowed list.

**Solution**: Add the package to `allowed_packages` or remove the restriction:
```python
# Add to allowed list
Container(allowed_packages=["myapp", "thirdparty"])

# Or remove restriction (if safe)
Container()  # No allowed_packages = no restriction
```
