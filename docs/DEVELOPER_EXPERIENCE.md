# Developer Experience Vision

## Goal: The Most Magically Delicious DI Experience Ever

This document captures the vision for dioxide's developer experience, learning from the best parts of existing DI frameworks while avoiding their pitfalls.

## Core Principles

### 1. Zero Configuration for Simple Cases
**Learn from**: Spring Boot's auto-configuration, Python's convention over configuration

```python
# This just works - no XML, no config files, no setup
from dioxide import Container, component

@component
class UserService:
    pass

@component
class UserController:
    def __init__(self, user_service: UserService):
        self.user_service = user_service

container = Container()
container.scan()  # Auto-discovers @component classes
controller = container.resolve(UserController)  # UserService auto-injected!
```

### 2. Type Hints Are the Source of Truth
**Avoid**: Spring's string-based dependency names, verbose XML configuration

```python
# Type hints drive everything - no string IDs, no magic strings
@component
class EmailService:
    def __init__(self, config: Config, logger: Logger):
        # Dependencies resolved by type automatically
        pass
```

### 3. Explicit When Needed, Magical When Convenient
**Learn from**: FastAPI's approach - explicit when you need control, magical otherwise

```python
# Simple case: magical auto-wiring
@component
class SimpleService:
    pass

# Complex case: explicit configuration available
@component(scope=Scope.TRANSIENT, name="special_service")
class ComplexService:
    def __init__(self, db: Database = Inject("primary_db")):
        pass
```

### 4. Clear Error Messages with Actionable Suggestions
**Avoid**: Cryptic dependency resolution errors

```python
# BAD (what other libraries do):
# Error: Cannot resolve dependency for UserService

# GOOD (what we'll do):
# ❌ Cannot resolve dependency: Database
#    Required by: UserService.__init__(db: Database)
#
#    💡 Did you forget to register Database?
#       Try: container.register_instance(Database, my_db)
#
#    🔍 Similar registered types:
#       - DatabaseConnection (similarity: 85%)
#       - DBConfig (similarity: 70%)
```

### 5. Performance That Gets Out of Your Way
**Learn from**: Rust's zero-cost abstractions

- Registration: Once at startup
- Resolution: Blazing fast (sub-microsecond for singletons)
- No runtime reflection overhead (use Rust backend)
- Type checking at container build time, not runtime

### 6. IDE Support That Feels Like Magic
**Learn from**: TypeScript's amazing tooling

```python
# Full autocomplete and type checking
@component
class UserService:
    def get_user(self) -> User: ...

# IDE knows controller.user_service is UserService
# Autocomplete works perfectly
controller = container.resolve(UserController)
user = controller.user_service.get_user()  # ← IDE autocomplete works!
```

### 7. Testing Should Be Trivial
**Avoid**: Mock frameworks that require understanding DI internals

```python
# Easy to override for testing
def test_user_controller():
    container = Container()

    # Simple override for testing
    mock_service = MockUserService()
    container.register_instance(UserService, mock_service)

    controller = container.resolve(UserController)
    assert controller.user_service is mock_service
```

### 8. Lifecycle Management Without Ceremony
**Learn from**: Spring's lifecycle hooks, avoiding complexity

```python
@component(scope=Scope.SINGLETON)
class DatabaseConnection:
    def __post_init__(self):
        """Called after all dependencies injected"""
        self.connect()

    def __cleanup__(self):
        """Called when container is destroyed"""
        self.disconnect()

# Just works - no manual lifecycle management
with Container() as container:
    container.scan()
    db = container.resolve(DatabaseConnection)
    # db.connect() already called
# db.disconnect() automatically called
```

### 9. Debugging That Tells You What's Happening
**Learn from**: FastAPI's automatic API docs

```python
# Visual dependency graph
container.visualize_dependencies()
# Creates a graph showing all registered components and their relationships

# Dependency resolution explanation
container.explain(UserController)
# Shows:
# UserController
# ├─ UserService (singleton, registered via @component)
# │  ├─ Database (instance, registered manually)
# │  └─ Logger (factory, registered via config)
# └─ Config (singleton, from environment)
```

### 10. Circular Dependencies Detected Early
**Avoid**: Runtime circular dependency explosions

```python
# Detected at container build time, not runtime
@component
class ServiceA:
    def __init__(self, b: 'ServiceB'): pass

@component
class ServiceB:
    def __init__(self, a: ServiceA): pass

container = Container()
container.scan()  # ← Raises immediately with clear error:
# ❌ Circular dependency detected:
#    ServiceA → ServiceB → ServiceA
#
#    💡 Consider using a factory or breaking the cycle:
#       - Use dependency injection on a method instead of __init__
#       - Introduce an interface to break the cycle
```

## What We're Avoiding

### From Spring/Spring Boot
- ❌ XML configuration hell
- ❌ Annotation soup (@Autowired, @Component, @Bean, @Configuration, @ComponentScan...)
- ❌ Cryptic BeanCreationException errors
- ❌ Magic that's hard to debug (classpath scanning surprises)
- ✅ Keep: Auto-configuration, convention over configuration

### From Google Guice
- ❌ Module boilerplate
- ❌ Binding DSL that's hard to read
- ❌ Provider<T> everywhere
- ✅ Keep: Type-safe dependency injection

### From dependency_injector (Python)
- ❌ Container.config.from_yaml() - configuration as code, not files
- ❌ Complex provider hierarchies
- ❌ String-based dependency names
- ✅ Keep: Pythonic API

### From inject (Python)
- ❌ Global state and implicit configuration
- ❌ Magic decorators that hide behavior
- ✅ Keep: Simple API

## The Magical Parts

### 1. Automatic Scanning
```python
# Finds all @component classes in your package
container.scan("myapp")

# Smart defaults - scans current package
container.scan()
```

### 2. Environment-Aware Configuration
```python
@component
class Config:
    database_url: str = from_env("DATABASE_URL")
    debug: bool = from_env("DEBUG", default=False, type=bool)

# No need to manually wire config - it just works
```

### 3. Interface-Based Registration
```python
# Register by interface/protocol
class UserRepository(Protocol):
    def get_user(self, id: int) -> User: ...

@component(implements=UserRepository)
class PostgresUserRepository:
    def get_user(self, id: int) -> User: ...

# Resolve by interface - decoupled from implementation
repo = container.resolve(UserRepository)  # Gets PostgresUserRepository
```

### 4. Named Dependencies
```python
@component(name="primary")
class PrimaryDatabase:
    pass

@component(name="replica")
class ReplicaDatabase:
    pass

@component
class DataService:
    def __init__(
        self,
        primary: Database = Inject("primary"),
        replica: Database = Inject("replica")
    ):
        pass
```

### 5. Conditional Registration
```python
@component(when=lambda: os.getenv("ENABLE_CACHE") == "true")
class RedisCache:
    pass

@component(when=lambda: os.getenv("ENABLE_CACHE") != "true")
class NoOpCache:
    pass

# Automatically picks the right one based on environment
```

### 6. Profiles
```python
@component(profiles=["dev", "test"])
class MockEmailService:
    pass

@component(profiles=["prod"])
class RealEmailService:
    pass

# Activate profile at runtime
container = Container(profile="dev")  # Gets MockEmailService
```

### 7. Decorators for Cross-Cutting Concerns
```python
@component
@transactional  # Automatically wraps methods in transactions
@cached  # Automatically caches method results
@logged  # Automatically logs method calls
class UserService:
    pass
```

## Performance Targets

- Container creation: <1ms for 100 components
- Component resolution (singleton): <10μs
- Component resolution (transient): <100μs
- Dependency graph validation: <10ms for 1000 components
- Memory overhead: <1MB for typical application

## Documentation Philosophy

- README has a working example in the first 30 seconds
- Every feature has a 3-line example
- Error messages link to docs
- Recipes for common patterns
- Migration guides from popular frameworks

## Developer Feedback Loop

```python
# When you make a mistake, you know immediately
container = Container()

# Missing dependency?
# ❌ Error during container.scan() with clear fix

# Circular dependency?
# ❌ Error during container.scan() with suggestion

# Type mismatch?
# ❌ Caught by mypy/pyright before runtime

# Wrong scope?
# 💡 Warning: UserService is TRANSIENT but injected into SINGLETON
#    This will create a new UserService for EVERY resolution.
#    Did you mean scope=Scope.SINGLETON?
```

## Guiding Questions for Every Feature

Before adding any feature, ask:

1. **Does this make the simple case simpler?** If no, reconsider.
2. **Does this make the complex case possible?** If no, wait for real use case.
3. **Will a developer understand this in 30 seconds?** If no, simplify.
4. **Does the error message help fix the problem?** If no, improve messaging.
5. **Does this require reading docs?** If yes, make it more obvious.
6. **Would Spring Boot do this?** If yes, consider the opposite.
7. **Would FastAPI do this?** If yes, strongly consider it.

## Measuring Success

We'll know we've succeeded when:

- Developers say "That just worked!"
- The first GitHub issue is "How is this so fast?"
- Migration from other DI frameworks takes <1 hour
- New team members are productive in <30 minutes
- Common DI patterns require zero boilerplate
- Error messages are screenshot and shared as examples of good UX

## Next Steps

1. Implement @component decorator with auto-discovery
2. Add automatic dependency resolution from type hints
3. Create amazing error messages with suggestions
4. Build dependency graph visualization
5. Add lifecycle hooks (@post_init, @cleanup)
6. Support named dependencies
7. Add profiles and conditional registration
8. Create comprehensive examples and recipes
