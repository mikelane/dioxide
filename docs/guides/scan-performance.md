# Scan Performance Best Practices

This guide covers how to use `container.scan()` efficiently for fast application startup.
For a general overview of scanning behavior, see the
[Package Scanning](../user_guide/package_scanning.md) reference.

## Understanding Scan Performance

When you call `container.scan(package="myapp")`, three things happen:

1. **Module discovery** -- dioxide walks the package tree to find all Python modules
2. **Module import** -- each discovered module is imported, executing module-level code
   including decorators
3. **Registration** -- decorated classes are matched against the active profile and
   registered with the container

Step 2 dominates scan time. Every `import` statement in every module is executed,
which means heavy module-level work cascades through your codebase.

### Typical Scan Times

| Package size | Modules | Typical scan time |
|-------------|---------|-------------------|
| Small | ~10 | 5--20 ms |
| Medium | ~50 | 20--100 ms |
| Large | ~200 | 100--500 ms |

These numbers assume modules that follow the patterns in this guide. Modules with
heavy imports or module-level I/O can be orders of magnitude slower.

## Scan Narrow, Not Wide

The single most effective optimization is scanning only the packages that contain
decorated classes.

### Recommended: Scan Specific Packages

```python
container = Container()

# Scan only the packages with @adapter and @service decorators
container.scan(package="myapp.adapters", profile=Profile.PRODUCTION)
container.scan(package="myapp.services", profile=Profile.PRODUCTION)
```

This imports only modules under `myapp/adapters/` and `myapp/services/`, skipping
anything else in your application.

### Avoid: Scanning the Entire Application

```python
# Imports EVERY module in myapp -- tests, scripts, migrations, etc.
container.scan(package="myapp", profile=Profile.PRODUCTION)
```

This works, but it imports modules that have no decorated classes, wasting time
on unnecessary imports.

### Rule of Thumb

Put your `@adapter.for_()` and `@service` decorators in dedicated packages
(`adapters/`, `services/`) and scan only those packages.

## Structuring Packages for Fast Scanning

### Separate Adapters by Profile

If production adapters have heavy dependencies (database drivers, HTTP clients),
keep them in separate modules from test adapters:

```
myapp/
├── adapters/
│   ├── __init__.py
│   ├── production/
│   │   ├── __init__.py
│   │   ├── email.py      # imports sendgrid
│   │   └── database.py   # imports asyncpg
│   └── test/
│       ├── __init__.py
│       ├── email.py       # in-memory fake, no heavy deps
│       └── database.py    # dict-based fake
└── services/
    ├── __init__.py
    └── user.py
```

Then scan by profile subdirectory:

```python
# Production -- imports sendgrid, asyncpg, etc.
container.scan(package="myapp.adapters.production", profile=Profile.PRODUCTION)

# Tests -- fast, no external dependencies
container.scan(package="myapp.adapters.test", profile=Profile.TEST)

# Services are profile-agnostic -- scan once
container.scan(package="myapp.services")
```

This prevents test runs from importing production dependencies and vice versa.

### Keep Modules Lightweight

A module that imports fast will scan fast:

```python
# myapp/adapters/production/email.py -- GOOD

from dioxide import adapter, lifecycle, Profile
from myapp.ports import EmailPort


@adapter.for_(EmailPort, profile=Profile.PRODUCTION)
@lifecycle
class SendGridAdapter:
    def __init__(self, config: ConfigPort) -> None:
        self.config = config
        self.client = None  # Created in initialize()

    async def initialize(self) -> None:
        import sendgrid  # Heavy import deferred to runtime
        self.client = sendgrid.SendGridAPIClient(self.config.api_key)

    async def send(self, to: str, subject: str, body: str) -> None:
        # Use self.client here
        ...

    async def dispose(self) -> None:
        if self.client:
            await self.client.close()
```

The key pattern: `import sendgrid` happens inside `initialize()`, not at module
level. The module can be imported quickly during scan, and the heavy dependency
loads only when the container starts.

## Common Anti-Patterns

### Module-Level Database Connections

```python
# BAD: Connection created during import
import asyncpg

connection = asyncpg.connect("postgresql://...")  # Runs during scan()!

@adapter.for_(DatabasePort, profile=Profile.PRODUCTION)
class PostgresAdapter:
    def query(self, sql: str):
        return connection.execute(sql)
```

```python
# GOOD: Use @lifecycle for deferred initialization
from dioxide import adapter, lifecycle, Profile


@adapter.for_(DatabasePort, profile=Profile.PRODUCTION)
@lifecycle
class PostgresAdapter:
    def __init__(self, config: ConfigPort) -> None:
        self.config = config
        self.connection = None

    async def initialize(self) -> None:
        import asyncpg
        self.connection = await asyncpg.connect(self.config.database_url)

    async def dispose(self) -> None:
        if self.connection:
            await self.connection.close()
```

### Heavy Top-Level Imports

```python
# BAD: Imports ML framework at module level (slow)
import tensorflow as tf  # Takes seconds to import
import numpy as np
import pandas as pd

from dioxide import adapter, Profile


@adapter.for_(ModelPort, profile=Profile.PRODUCTION)
class TensorFlowModel:
    def predict(self, data):
        return self.model.predict(tf.constant(data))
```

```python
# GOOD: Defer heavy imports to method or initialize()
from dioxide import adapter, lifecycle, Profile


@adapter.for_(ModelPort, profile=Profile.PRODUCTION)
@lifecycle
class TensorFlowModel:
    async def initialize(self) -> None:
        import tensorflow as tf
        self.model = tf.saved_model.load("model_path")

    def predict(self, data):
        import tensorflow as tf
        return self.model.predict(tf.constant(data))
```

### Global State Initialization

```python
# BAD: Global state computed during import
from dioxide import adapter, Profile

VALID_REGIONS = fetch_regions_from_api()  # Network call at import time!
CACHE = build_expensive_cache()           # CPU-intensive at import time!

@adapter.for_(RegionPort, profile=Profile.PRODUCTION)
class RegionService:
    ...
```

```python
# GOOD: Compute state lazily or in initialize()
from dioxide import adapter, lifecycle, Profile


@adapter.for_(RegionPort, profile=Profile.PRODUCTION)
@lifecycle
class RegionService:
    async def initialize(self) -> None:
        self.valid_regions = await fetch_regions_from_api()
        self.cache = build_expensive_cache()
```

## Debugging Slow Scans

### Profiling Import Time

Python 3.11+ has built-in import profiling. Use it to find which modules are slow:

```bash
python -X importtime -c "
from dioxide import Container, Profile
container = Container()
container.scan(package='myapp', profile=Profile.PRODUCTION)
" 2> import_profile.log
```

The output shows import time for every module, sorted by self-time. Look for
modules that take more than a few milliseconds.

### Manual Timing

Add timing around your scan calls to measure startup impact:

```python
import time

start = time.perf_counter()
container.scan(package="myapp.adapters", profile=Profile.PRODUCTION)
adapter_time = time.perf_counter() - start

start = time.perf_counter()
container.scan(package="myapp.services", profile=Profile.PRODUCTION)
service_time = time.perf_counter() - start

print(f"Adapter scan: {adapter_time*1000:.1f}ms")
print(f"Service scan: {service_time*1000:.1f}ms")
```

### Identifying the Bottleneck

| Symptom | Likely cause | Solution |
|---------|-------------|----------|
| Scan takes > 1s | Heavy module-level imports | Defer imports to `initialize()` |
| Scan time grows linearly | Too many modules scanned | Narrow scan to adapter/service packages |
| Scan time jumps after adding a module | New module has side effects | Check for module-level I/O or computation |
| Tests are slow to start | Scanning production adapters in tests | Separate prod/test adapter packages |

## Framework Integration Tips

### FastAPI: Use the Lifespan Pattern

FastAPI imports your route modules, which can trigger decorator execution. Let
FastAPI handle module discovery and use scan without a package parameter:

```python
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from dioxide import Container, Profile

# Import routes -- this also imports adapters/services referenced by routes
from myapp import routes  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    container = Container()
    # No package= needed -- modules are already imported by FastAPI
    container.scan(profile=Profile.PRODUCTION)
    async with container:
        app.state.container = container
        yield


app = FastAPI(lifespan=lifespan)
```

### Flask: Use the Factory Pattern

```python
from dioxide import Container, Profile


def create_app(profile: Profile = Profile.PRODUCTION) -> Flask:
    app = Flask(__name__)

    container = Container()
    container.scan(package="myapp.adapters", profile=profile)
    container.scan(package="myapp.services")

    app.container = container
    return app
```

### CLI: Scan Only What You Need

CLI applications benefit the most from narrow scanning because startup time
directly impacts user experience:

```python
import click
from dioxide import Container, Profile


@click.command()
def main():
    container = Container(allowed_packages=["myapp"])
    # Only scan the adapters this command needs
    container.scan(package="myapp.adapters.cli", profile=Profile.PRODUCTION)
    container.scan(package="myapp.services")

    service = container.resolve(TaskService)
    service.run()
```

### Celery: Scan in Worker Init

```python
from celery import Celery
from dioxide import Container, Profile
from dioxide.celery import configure_dioxide

app = Celery("myapp")
configure_dioxide(
    app,
    profile=Profile.PRODUCTION,
    packages=["myapp.adapters", "myapp.services"],
)
```

## Using `allowed_packages` for Security

When package names come from configuration or environment variables, restrict
which packages can be scanned:

```python
import os
from dioxide import Container

scan_target = os.environ.get("APP_SCAN_PACKAGE", "myapp")

# Without allowed_packages -- an attacker could set APP_SCAN_PACKAGE=os
# and execute arbitrary code during scan
container = Container()
container.scan(package=scan_target)  # DANGEROUS

# With allowed_packages -- only myapp.* and tests.* are allowed
container = Container(allowed_packages=["myapp", "tests"])
container.scan(package=scan_target)  # Safe: ValueError if not in list
```

`allowed_packages` uses simple string prefix matching: `"myapp"` allows
`"myapp"`, `"myapp.adapters"`, and `"myapp.adapters.email"`, but blocks
`"other.myapp"`. Note that `"myapp"` also allows `"myapplication"` because
it is a string prefix. For precise package boundaries, include the dot:
`"myapp."` (though this excludes the `"myapp"` package itself, so use
`["myapp", "myapp."]` or simply `["myapp."]` if you only scan sub-packages).

## Scan Without a Package Parameter

When you call `scan()` without `package=`, dioxide discovers only classes from
**already-imported modules**. No new modules are imported.

```python
# These imports trigger decorator execution
from myapp.adapters.email import SendGridAdapter  # noqa: F401
from myapp.services.user import UserService  # noqa: F401

container = Container()
container.scan(profile=Profile.PRODUCTION)
# Only SendGridAdapter and UserService are registered
```

This is the fastest scan mode because it skips module discovery entirely. Use it
when your framework or application structure already imports the necessary modules.

## Multiple Scan Calls

You can call `scan()` multiple times to build up registrations incrementally:

```python
container = Container()

# Scan adapters first
container.scan(package="myapp.adapters.infrastructure", profile=Profile.PRODUCTION)

# Then services
container.scan(package="myapp.services", profile=Profile.PRODUCTION)

# Add shared utilities
container.scan(package="shared.di_components", profile=Profile.PRODUCTION)
```

Each call adds to the container's registrations without clearing previous ones.
Already-registered types are silently skipped.

## Quick Reference: Performance Checklist

1. **Scan specific packages**, not your entire application
2. **Separate adapters by profile** so tests don't import production dependencies
3. **Defer heavy imports** to `initialize()` or methods, not module level
4. **Avoid module-level I/O** -- no database connections, API calls, or file reads at import time
5. **Use `@lifecycle`** for components that need initialization or cleanup
6. **Use `allowed_packages`** when scan targets come from external input
7. **Profile imports** with `python -X importtime` when scan feels slow
8. **Let frameworks import modules** and use `scan()` without `package=` where possible
