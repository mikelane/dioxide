# dioxide Developer Experience Vision

**"Dependency injection should feel invisible when it works, and obvious when it doesn't."**

---

## ⚠️ IMPORTANT: Document Status

**This is an ASPIRATIONAL vision document** - it describes the long-term ideal developer experience for dioxide.

**For current implementation:** See **[MLP_VISION.md](MLP_VISION.md)** - the canonical design specification for what we're building NOW.

**Relationship:**
- **MLP_VISION.md** = Concrete spec for MLP (Minimum Loveable Product) - BUILD THIS FIRST
- **DX_VISION.md** = Aspirational UX goals for post-MLP - THE LONG-TERM DREAM

Many features shown in this document (async/await, configuration management, observability, CLI tools) are **explicitly out of scope** for MLP. They represent post-MLP aspirations.

**Last Updated:** 2025-11-07 (aligned with MLP_VISION.md)

---

## Purpose of This Document

This document captures the **aspirational developer experience** for dioxide - what we want developers to feel when they use this framework. It's not a feature list or roadmap, but rather a **guiding philosophy** that informs every design decision.

**Note:** Code examples may show post-MLP features. For current MLP API, always refer to [MLP_VISION.md](MLP_VISION.md).

When making choices about API design, error messages, documentation, or features, we ask:
- **Does this make the simple case simpler?**
- **Does this make the developer feel confident or confused?**
- **Would I want to use this myself?**

This document is inspired by the best parts of Spring Boot, dependency-injector, injector, Dagger, and Guice - while learning from their pain points.

---

## The Core Principles

### 1. Zero Friction for Simple Cases

**Philosophy:** The most common use case should require the least code.

**What this looks like:**

```python
from dioxide import container, component

@component
class EmailService:
    pass

@component
class UserService:
    def __init__(self, email: EmailService):
        self.email = email

# MLP API: global singleton container
container.scan("app")
user_service = container[UserService]

# That's it. No configuration, no wiring, no boilerplate.
```

**Anti-patterns to avoid:**
- ❌ Requiring explicit wiring for every dependency
- ❌ Needing configuration files for simple cases
- ❌ Annotation soup (`@Injectable @Scope @Named @Qualifier`)
- ❌ Factory boilerplate for every class

**Inspiration:**
- ✅ Spring Boot's `@Component` + component scanning
- ✅ injector's minimal API
- ✅ Python's type hints as the DI contract

---

### 2. Progressive Disclosure of Complexity

**Philosophy:** Simple things should be simple. Complex things should be possible.

**Complexity ladder:**

```python
# Level 0: Just works (90% of use cases) - MLP
@component
class Service:
    pass

# Level 1: Control lifecycle (8% of use cases) - MLP
@component.factory
class RequestHandler:
    pass

# Level 2: Profile-based implementations (1.5% of use cases) - MLP
@component.implements(EmailProvider)
@profile.production
class SendGridEmail:
    pass

# Level 3: Manual provider factories (0.5% of use cases) - Post-MLP
container.register_provider(
    AuthService,
    provider=lambda: AuthService(config.auth_url),
    scope=Scope.SINGLETON,
    on_shutdown=lambda s: s.close(),
)
```

**The key:** Each level is **opt-in**. You don't learn about Level 3 until you need it.

**Anti-patterns to avoid:**
- ❌ Exposing all advanced features in "Getting Started"
- ❌ Making simple cases require complex features
- ❌ Confusing users with options they don't need yet

**Inspiration:**
- ✅ React's "Learn Once, Write Anywhere" (simple to start, powerful when needed)
- ✅ FastAPI's progressive type hints
- ✅ pytest's simple fixtures that can become complex

---

### 3. Type Safety First

**Philosophy:** Catch errors at development time, not runtime.

**What this looks like:**

```python
from dioxide import Container, component

@component
class UserService:
    pass

container = Container()
container.scan()

# Type-safe resolution (IDE knows the type)
service: UserService = container.resolve(UserService)

# Mypy catches mistakes:
service = container.resolve("string")  # Type error!
service = container.resolve(42)        # Type error!

# Missing dependency caught at scan():
@component
class Controller:
    def __init__(self, missing: UnregisteredService):
        pass

container.scan()  # Raises: "Missing dependency: UnregisteredService"
```

**Benefits:**
1. **IDE autocomplete** shows available dependencies
2. **Mypy/Pyright** catch type mismatches before runtime
3. **Refactoring is safe** - rename a class, all usages update
4. **Self-documenting** - type hints show dependency contract

**Anti-patterns to avoid:**
- ❌ String-based dependency resolution (`container.get('user_service')`)
- ❌ Runtime-only validation (fails in production)
- ❌ Magic that defeats type checkers

**Inspiration:**
- ✅ Dagger's compile-time validation
- ✅ FastAPI's type-driven validation
- ✅ Rust's type system (catch bugs at compile time)

---

### 4. Performance by Default

**Philosophy:** DI should never be the bottleneck.

**Performance targets:**

| Operation | Target | Why |
|-----------|--------|-----|
| `container.scan()` with 100 components | <10ms | App startup shouldn't wait |
| `container.resolve(Singleton)` | <10μs | Negligible overhead |
| `container.resolve(Transient)` | <100μs | Fast enough for request handlers |
| Memory overhead | <1MB for 1000 components | Minimal footprint |

**Implementation strategy:**
- Rust-backed container for graph operations
- Lazy initialization (defer work until first resolve)
- Compile-time optimizations where possible
- Benchmark-driven development

**Anti-patterns to avoid:**
- ❌ Slow startup (Spring Boot's classpath scanning)
- ❌ Runtime reflection overhead (Java's annotation processing)
- ❌ Memory leaks from circular references

**Inspiration:**
- ✅ Rust's zero-cost abstractions
- ✅ FastAPI's async performance
- ✅ Go's fast compilation and startup

---

### 5. Debuggability and Introspection

**Philosophy:** When something goes wrong, make it obvious how to fix it.

**What this looks like:**

```python
# Inspect what's registered
container.list_components()
# Output:
# [
#   Component(type=UserService, scope=SINGLETON, dependencies=[EmailService]),
#   Component(type=EmailService, scope=SINGLETON, dependencies=[]),
# ]

# Visualize dependency graph
container.visualize()
# Opens interactive graph in browser showing:
# - All components
# - Dependency relationships
# - Lifecycle scopes
# - Circular dependencies (highlighted)

# Check if something is registered
container.has(UserService)  # True
container.has(UnregisteredService)  # False

# Get component info
info = container.info(UserService)
# Output:
# ComponentInfo(
#   type=UserService,
#   scope=SINGLETON,
#   dependencies=[EmailService],
#   registered_at="container.scan() line 45 in main.py",
#   instantiated=True,
#   instance_id=0x7f8b3c,
# )

# Debug mode with tracing
container = Container(debug=True)
container.scan()
# Output:
# [DEBUG] Scanning for @component decorated classes...
# [DEBUG] Found: UserService (SINGLETON)
# [DEBUG] Found: EmailService (SINGLETON)
# [DEBUG] Resolving dependencies for UserService...
# [DEBUG] Resolving EmailService... (cached)
# [DEBUG] Instantiating UserService(email=EmailService@0x7f8b3c)
```

**Benefits:**
1. **Visual graph** helps understand complex dependencies
2. **Debug mode** shows exactly what's happening
3. **Introspection API** enables custom tooling
4. **Error messages** point to exact problem

**Anti-patterns to avoid:**
- ❌ Black box behavior (no way to see inside)
- ❌ Generic errors ("Something went wrong")
- ❌ Requiring external tools to debug

**Inspiration:**
- ✅ FastAPI's automatic OpenAPI docs
- ✅ React DevTools (component inspector)
- ✅ Spring Boot Actuator (health checks, metrics)

---

### 6. Testability Without Compromise

**Philosophy:** Testing code that uses DI should be easier than testing without it.

**What this looks like:**

```python
# Production code
@component
class UserService:
    def __init__(self, db: Database, email: EmailService):
        self.db = db
        self.email = email

    def create_user(self, name: str) -> User:
        user = self.db.create(name)
        self.email.send_welcome(user)
        return user

# Test code (Option 1: Override dependencies)
def test_create_user():
    container = Container()
    container.scan()

    # Override specific dependencies with mocks
    mock_db = MockDatabase()
    mock_email = MockEmailService()

    container.override(Database, mock_db)
    container.override(EmailService, mock_email)

    service = container.resolve(UserService)
    user = service.create_user("Alice")

    assert mock_db.created_user("Alice")
    assert mock_email.sent_welcome(user)

# Test code (Option 2: Isolated container)
def test_create_user_isolated():
    with IsolatedContainer() as container:
        container.register_instance(Database, MockDatabase())
        container.register_instance(EmailService, MockEmailService())
        container.register_singleton(UserService, UserService)

        service = container.resolve(UserService)
        user = service.create_user("Alice")

        assert user.name == "Alice"

# Test code (Option 3: Direct instantiation)
def test_create_user_direct():
    # No DI framework needed for simple tests
    service = UserService(
        db=MockDatabase(),
        email=MockEmailService()
    )
    user = service.create_user("Alice")
    assert user.name == "Alice"
```

**Key features for testability:**
1. **Override dependencies** for specific tests
2. **Isolated containers** prevent test pollution
3. **No framework lock-in** - can instantiate classes directly
4. **pytest fixtures** integrate seamlessly
5. **Mock-friendly** - works with unittest.mock, pytest-mock, etc.

**Anti-patterns to avoid:**
- ❌ Global state that pollutes tests
- ❌ Framework-specific mocking (can't use standard tools)
- ❌ Requiring full container setup for unit tests
- ❌ Difficult to override individual dependencies

**Inspiration:**
- ✅ pytest's fixture system
- ✅ dependency-injector's override mechanism
- ✅ Spring Boot's `@TestConfiguration`

---

### 7. Error Messages That Teach

**Philosophy:** Every error is a teaching opportunity.

**What this looks like:**

**Example 1: Missing dependency**
```
DependencyNotRegisteredError: UserService requires EmailService, but EmailService is not registered.

How to fix:
  1. Decorate EmailService with @component:
     @component
     class EmailService:
         pass

  2. Or register it manually:
     container.register_singleton(EmailService, EmailService)

  3. Or make it optional:
     def __init__(self, email: EmailService | None = None):
         self.email = email

Dependency chain:
  UserController → UserService → EmailService (missing)
```

**Example 2: Circular dependency**
```
CircularDependencyError: Detected circular dependency:
  ServiceA → ServiceB → ServiceC → ServiceA

This creates an infinite loop. To fix:
  1. Introduce an interface to break the cycle
  2. Use lazy initialization (resolve on first use)
  3. Refactor to remove the circular dependency

More info: https://dioxide.dev/docs/circular-dependencies
```

**Example 3: Type mismatch**
```
TypeError: resolve() expected type[T], got 'string'

You wrote:
  container.resolve("UserService")

Did you mean:
  container.resolve(UserService)

Note: dioxide uses types, not strings, for type-safe resolution.
```

**Characteristics of great error messages:**
1. **What went wrong** (clear, specific)
2. **Why it's wrong** (context, explanation)
3. **How to fix it** (2-3 concrete solutions)
4. **Where it happened** (file, line number, dependency chain)
5. **Learn more** (link to docs)

**Anti-patterns to avoid:**
- ❌ Generic errors: `KeyError: 'UserService'`
- ❌ Stack traces without context
- ❌ Technical jargon without explanation
- ❌ No suggestions for fixing

**Inspiration:**
- ✅ Rust's compiler errors (detailed, helpful)
- ✅ Elm's error messages (friendly, educational)
- ✅ Rails' error pages (actionable, contextual)

---

### 8. Clear Mental Model

**Philosophy:** Developers should understand how it works, not just how to use it.

**The dioxide mental model:**

```
┌─────────────────────────────────────────┐
│  1. DECLARE COMPONENTS                  │
│     @component decorates classes        │
│     Type hints declare dependencies     │
└───────────────┬─────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────┐
│  2. SCAN AND BUILD GRAPH                │
│     container.scan() discovers          │
│     Creates dependency graph            │
│     Validates (no missing, no cycles)   │
└───────────────┬─────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────┐
│  3. RESOLVE INSTANCES                   │
│     container.resolve(Type)             │
│     Walks graph, creates instances      │
│     Caches singletons, creates factories│
└─────────────────────────────────────────┘
```

**Key concepts:**
1. **Components** are classes decorated with `@component`
2. **Dependencies** are declared via type hints
3. **Scanning** builds a dependency graph from components
4. **Resolution** creates instances by walking the graph
5. **Scopes** control lifecycle (singleton vs transient)

**Teaching materials:**
- **Interactive tutorial** walks through each step
- **Visual diagrams** show dependency graphs
- **Debug mode** traces what's happening
- **Comparison guide** explains vs. other DI frameworks

**Anti-patterns to avoid:**
- ❌ "Magic" that users don't understand
- ❌ Too many abstractions (context, injector, provider, factory)
- ❌ Unclear lifecycle (when is it created? cached?)
- ❌ Hidden configuration (where are defaults?)

**Inspiration:**
- ✅ React's component model (easy to explain)
- ✅ FastAPI's request flow (clear, linear)
- ✅ Django's ORM (intuitive mental model)

---

## The Joyful Moments

A beautiful DX creates **joyful moments** - times when the framework delights you:

### Moment 1: "It just works"

```python
@component
class UserService:
    def __init__(self, db: Database, cache: Cache, email: Email):
        self.db, self.cache, self.email = db, cache, email

container.scan()
service = container.resolve(UserService)

# All dependencies auto-injected! No configuration!
```

**Feeling:** "Wow, that was easy."

---

### Moment 2: "The error message saved me"

```
DependencyNotRegisteredError: UserService requires Database, but Database is not registered.

Did you forget to add @component to Database?

File: app/services/user.py, line 15
```

**Feeling:** "It told me exactly what to fix."

---

### Moment 3: "Testing is trivial"

```python
def test_user_service(container):
    container.override(Database, MockDatabase())
    service = container.resolve(UserService)
    # Test away!
```

**Feeling:** "I can test this easily."

---

### Moment 4: "I can see what's happening"

```python
container.visualize()
# Opens browser with interactive dependency graph
```

**Feeling:** "Now I understand how this fits together."

---

### Moment 5: "It's so fast"

```python
# Startup with 1000 components: <100ms
# Resolve singleton: <10μs
# Resolve transient: <100μs
```

**Feeling:** "DI isn't slowing me down."

---

### Moment 6: "I can refactor fearlessly"

```python
# Rename Database to DatabaseConnection
# IDE updates all usages
# Type checker verifies everything still works
```

**Feeling:** "I trust this to work."

---

## The Anti-Patterns (What to Avoid)

These are patterns from other frameworks that create **frustration**, not joy:

### ❌ Annotation Soup (Spring Boot)

```java
@Component
@Scope("prototype")
@Lazy
@Primary
@Conditional(OnProperty="feature.enabled")
@Profile("production")
public class MyService {
    @Autowired
    @Qualifier("primary")
    private Database database;
}
```

**Problem:** Too many annotations, unclear precedence, hard to read

**dioxide approach:** Minimal decorators, progressive disclosure

---

### ❌ String-Based Resolution (Many frameworks)

```python
container.get('user_service')  # No type safety
container.get('emailService')  # Typo? Runtime error!
```

**Problem:** No IDE support, no type checking, brittle

**dioxide approach:** Type-based resolution with full type safety

---

### ❌ Verbose Wiring (dependency-injector)

```python
container = Container()
container.wire(modules=[app.services])
container.wire(modules=[app.controllers])
container.wire(packages=[app.utils])
container.providers.database.override(MockDatabase())
```

**Problem:** Too much boilerplate for simple cases

**dioxide approach:** `container.scan()` discovers automatically

---

### ❌ Magic Without Explanation (Spring Boot)

```java
@SpringBootApplication
public class App {
    // How does this work? Where are components registered?
    // What's the scan order? Can I customize it?
}
```

**Problem:** Works until it doesn't, then hard to debug

**dioxide approach:** Clear mental model, debug mode, introspection

---

### ❌ Global State Pollution (Many frameworks)

```python
# Test 1
@component
class Service:
    pass

# Test 2
@component  # Same class, different test!
class Service:
    pass  # Wait, which one is registered?
```

**Problem:** Tests interfere with each other

**dioxide approach:** Isolated containers, explicit scope

---

### ❌ Framework Lock-In (Many frameworks)

```python
# Can only test with framework-specific mocking
# Can't instantiate classes directly
# Forced to use framework patterns everywhere
```

**Problem:** Hard to migrate, hard to test without framework

**dioxide approach:** Classes are just classes, can instantiate directly

---

## The Emotional Journey

Great DX creates an **emotional arc** as developers learn the framework:

### Stage 1: "I'll give it a try" (First 5 minutes)

**Goal:** Instant success

**Experience:**
- Clear README with working example
- Copy-paste code, it runs
- "That was easy!"

**Keys to success:**
- README Quick Start actually works
- Example code is realistic (not "Hello World")
- Installation is one command
- Error messages guide if stuck

---

### Stage 2: "I'm building something real" (First day)

**Goal:** Confidence to build

**Experience:**
- Examples cover common patterns
- IDE autocomplete helps discover APIs
- Type checker catches mistakes before running
- "I understand how this works"

**Keys to success:**
- Good examples in `examples/` directory
- Type safety prevents common mistakes
- Documentation is searchable
- Can find answers quickly

---

### Stage 3: "I need to do something advanced" (First week)

**Goal:** Progressive power

**Experience:**
- Documentation shows advanced patterns
- Can customize without fighting framework
- "It's flexible when I need it to be"

**Keys to success:**
- Advanced docs are separate from beginner docs
- Extension points are clear
- Can opt-in to complexity
- Don't need to learn everything upfront

---

### Stage 4: "Something went wrong" (Inevitable)

**Goal:** Quick recovery

**Experience:**
- Error message explains the problem
- Debug mode shows what's happening
- "Oh, I see what I did wrong"

**Keys to success:**
- Error messages that teach
- Debug/introspection tools
- Searchable error messages
- Active community for help

---

### Stage 5: "I'm recommending this to my team" (First month)

**Goal:** Advocacy

**Experience:**
- Onboarding new team members is easy
- Framework doesn't slow us down
- "This is better than what we had"

**Keys to success:**
- Performance doesn't degrade at scale
- Testing is easy
- Good IDE integration
- Migration guides from other frameworks

---

## The Design Questions

When making design decisions, we ask:

### API Design

1. **Is this the simplest API for this use case?**
   - Can we remove a parameter?
   - Can we infer this from context?
   - Do we need this method, or is there a better way?

2. **Does this compose well?**
   - Can features be combined?
   - Do they interact cleanly?
   - Are there surprising interactions?

3. **Is this consistent with the rest of the API?**
   - Same naming patterns?
   - Same parameter order?
   - Same return types?

### Error Messages

1. **Would a beginner understand this error?**
   - No jargon?
   - Clear explanation?
   - Actionable advice?

2. **Does this error teach the mental model?**
   - Explains why it's wrong?
   - Shows correct pattern?
   - Links to docs?

### Documentation

1. **Can a developer get started in 5 minutes?**
   - Working example in README?
   - One-command install?
   - No prerequisites?

2. **Can they find answers quickly?**
   - Good search?
   - Clear structure?
   - Examples for common tasks?

### Features

1. **Does this solve a real problem?**
   - Do users actually need this?
   - Or is it hypothetical?

2. **Can we solve this without adding complexity?**
   - Library vs. framework feature?
   - Can users build this themselves?
   - Is there a simpler solution?

---

## Success Metrics

We measure success by **developer satisfaction**, not just technical metrics:

### Quantitative Metrics

| Metric | Target | Why |
|--------|--------|-----|
| Time to first working code | <5 minutes | Instant success |
| GitHub stars growth | 10+/day after 1.0 | Community adoption |
| PyPI downloads | 10k+/month after 1.0 | Real usage |
| Issue response time | <48 hours | Active maintainers |
| Documentation rating | 8+/10 | Docs are helpful |

### Qualitative Metrics

| Metric | How to measure |
|--------|----------------|
| "It just works" moments | User testimonials, tweets |
| Error message quality | User feedback, issue analysis |
| Onboarding friction | Watch new users, count blockers |
| Test ease | Survey users about testing |
| Framework feel | "Joy" vs. "Frustration" sentiment |

### Community Health

| Metric | Target |
|--------|--------|
| Contributors | 20+ by 1.0 |
| Active discussions | 10+/week |
| Questions answered | 90% within 24h |
| Positive sentiment | 80%+ |

---

## The North Star

**"Using dioxide should feel like the framework reads your mind."**

When a developer writes:
```python
@component
class UserService:
    def __init__(self, db: Database):
        self.db = db
```

They should think: **"Of course that's how it works."**

Not:
- ❌ "How do I configure this?"
- ❌ "Where's the documentation?"
- ❌ "Why isn't this working?"

But rather:
- ✅ "It just works."
- ✅ "Exactly what I expected."
- ✅ "This is obvious."

---

## Conclusion

dioxide aspires to be **the DI framework that developers recommend to their friends** because:

1. **It's fast** - No startup penalty, blazing resolution
2. **It's simple** - One decorator, one scan, one resolve
3. **It's safe** - Type-checked, validated, tested
4. **It's debuggable** - See what's happening, understand why
5. **It's testable** - Override, isolate, mock
6. **It's joyful** - Delights instead of frustrates

When developers use dioxide, they should feel:
- **Confident** - I trust this to work
- **Empowered** - I can build anything
- **Productive** - I'm moving fast
- **Delighted** - This is actually nice to use

**That's the vision. That's what we're building.**

---

## Post-MLP Features (Aspirational)

The following sections describe features that are **explicitly out of scope** for the MLP. They represent the long-term aspirational vision for dioxide.

**For MLP scope:** See [MLP_VISION.md - What We're NOT Building](MLP_VISION.md#what-were-not-building)

---

## 9. Async/Await Native Support ⚠️ POST-MLP

**Philosophy:** Modern Python is async. DI should embrace it, not fight it.

**What this looks like:**

```python
from dioxide import Container, component

@component
class AsyncDatabase:
    async def connect(self):
        # Async initialization
        await asyncio.sleep(0)  # Simulating connection

@component
class AsyncUserService:
    def __init__(self, db: AsyncDatabase):
        self.db = db

    async def get_user(self, user_id: int):
        return await self.db.query(f"SELECT * FROM users WHERE id = {user_id}")

# Async resolution
container = Container()
container.scan()

# Works with both sync and async code
service = container.resolve(AsyncUserService)  # Sync constructor
result = await service.get_user(123)  # Async method

# Async lifecycle hooks
@component(
    on_startup=lambda s: s.connect(),
    on_shutdown=lambda s: s.disconnect()
)
class DatabasePool:
    async def connect(self):
        # Async startup
        pass

    async def disconnect(self):
        # Async cleanup
        pass

# Container-level async lifecycle
async with container.lifespan():
    # All on_startup hooks run
    service = container.resolve(UserService)
    # ... use services ...
# All on_shutdown hooks run automatically
```

**Key features:**
1. **Async constructors supported** - `async def __init__` works
2. **Async lifecycle hooks** - `on_startup`, `on_shutdown` can be async
3. **Async context manager** - `async with container.lifespan():`
4. **Mixed sync/async** - Sync components can depend on async, vice versa
5. **AsyncIO-aware resolution** - Detects event loop, handles gracefully

**Anti-patterns to avoid:**
- ❌ Forcing all constructors to be sync (blocks async init)
- ❌ No async lifecycle support (can't cleanup async resources)
- ❌ Deadlocks when mixing sync/async
- ❌ Running event loop in DI framework (user controls loop)

**Inspiration:**
- ✅ FastAPI's async dependency injection
- ✅ asyncio's context managers
- ✅ Starlette's lifespan protocol

---

## 10. Configuration Management Excellence ⚠️ POST-MLP

**Philosophy:** Configuration is a dependency. Treat it as such.

**What this looks like:**

```python
from dioxide import Container, component, config

# Option 1: Type-safe config classes
@config
class DatabaseConfig:
    host: str = "localhost"
    port: int = 5432
    database: str = "myapp"

    @classmethod
    def from_env(cls):
        return cls(
            host=os.getenv("DB_HOST", cls.host),
            port=int(os.getenv("DB_PORT", cls.port)),
            database=os.getenv("DB_NAME", cls.database),
        )

@component
class Database:
    def __init__(self, config: DatabaseConfig):
        self.config = config
        # Use config.host, config.port, etc.

container = Container()
container.register_config(DatabaseConfig.from_env())
container.scan()

# Option 2: Environment-based injection
@component
class EmailService:
    def __init__(
        self,
        api_key: str = config.env("SENDGRID_API_KEY"),
        from_email: str = config.env("FROM_EMAIL", default="noreply@example.com"),
    ):
        self.api_key = api_key
        self.from_email = from_email

# Option 3: Config file integration
container = Container()
container.load_config("config/production.toml")  # or .yaml, .json, .env
container.scan()

# Option 4: Secret management
@component
class PaymentService:
    def __init__(
        self,
        api_key: str = config.secret("stripe/api_key"),  # From secret store
        webhook_secret: str = config.secret("stripe/webhook_secret"),
    ):
        self.api_key = api_key
        self.webhook_secret = webhook_secret

# Integrations:
container.load_config_from_aws_secrets_manager()
container.load_config_from_vault()
container.load_config_from_azure_keyvault()
```

**Key features:**
1. **Type-safe config classes** - Define schema with types
2. **Environment variable injection** - `config.env()` helper
3. **Config file loading** - TOML, YAML, JSON, .env support
4. **Secret management integration** - AWS, Vault, Azure, etc.
5. **Default values** - Sensible defaults with overrides
6. **Validation** - Config validated at startup, not runtime

**Anti-patterns to avoid:**
- ❌ Global config singletons (`Config.get('db.host')`)
- ❌ String keys everywhere (no type safety)
- ❌ Late validation (fails in production)
- ❌ Mixing config and code (`if os.getenv(...)` everywhere)

**Inspiration:**
- ✅ Pydantic's settings management
- ✅ Twelve-factor app methodology
- ✅ Spring Boot's `@ConfigurationProperties`

---

## 11. Framework Integration Patterns ⚠️ POST-MLP

**Philosophy:** dioxide should integrate seamlessly with existing frameworks, not replace them.

### FastAPI Integration

```python
from fastapi import FastAPI, Depends
from dioxide import Container, component

@component
class UserService:
    def __init__(self, db: Database):
        self.db = db

app = FastAPI()
container = Container()
container.scan()

# Pattern 1: Dependency injection via Depends
def get_user_service() -> UserService:
    return container.resolve(UserService)

@app.get("/users/{user_id}")
async def get_user(
    user_id: int,
    service: UserService = Depends(get_user_service)
):
    return service.get_user(user_id)

# Pattern 2: Automatic integration (future)
from dioxide.integrations.fastapi import use_dioxide

use_dioxide(app, container)

@app.get("/users/{user_id}")
async def get_user(user_id: int, service: UserService):
    # service auto-resolved via dioxide
    return service.get_user(user_id)
```

### Flask Integration

```python
from flask import Flask
from dioxide import Container, component
from dioxide.integrations.flask import FlaskDI

app = Flask(__name__)
container = Container()
container.scan()

# Integrate with Flask
di = FlaskDI(app, container)

@app.route("/users/<int:user_id>")
@di.inject  # Auto-inject from container
def get_user(user_id: int, service: UserService):
    return service.get_user(user_id)
```

### Django Integration

```python
# settings.py
INSTALLED_APPS = [
    'dioxide.integrations.django',
    # ... other apps
]

# views.py
from dioxide import component
from dioxide.integrations.django import inject

@component
class UserService:
    def __init__(self, db: Database):
        self.db = db

@inject
def user_view(request, service: UserService):
    users = service.get_all_users()
    return render(request, 'users.html', {'users': users})
```

**Key features:**
1. **Non-invasive** - Works alongside framework DI
2. **Type-safe** - Preserves type hints
3. **Async-aware** - Handles async views/routes
4. **Minimal boilerplate** - One decorator or helper
5. **Framework conventions** - Respects each framework's patterns

**Anti-patterns to avoid:**
- ❌ Replacing framework DI entirely (too invasive)
- ❌ Breaking framework conventions
- ❌ Requiring dioxide-specific wrappers everywhere
- ❌ Not working with framework middleware/plugins

---

## 12. Production Readiness ⚠️ POST-MLP

**Philosophy:** DX includes production experience, not just development.

### Lifecycle Management

```python
@component(
    on_startup=lambda s: s.connect(),
    on_shutdown=lambda s: s.disconnect(),
)
class DatabasePool:
    async def connect(self):
        self.pool = await create_pool()
        print("Database connected")

    async def disconnect(self):
        await self.pool.close()
        print("Database disconnected")

# Graceful startup/shutdown
container = Container()
container.scan()

async def main():
    async with container.lifespan():
        # All on_startup hooks run in dependency order
        app = container.resolve(Application)
        await app.run()
    # All on_shutdown hooks run in reverse order

# Handle signals gracefully
import signal

def handle_shutdown(signum, frame):
    container.shutdown()  # Runs all on_shutdown hooks
    sys.exit(0)

signal.signal(signal.SIGTERM, handle_shutdown)
signal.signal(signal.SIGINT, handle_shutdown)
```

### Health Checks

```python
from dioxide import Container, component

@component
class Database:
    async def health_check(self):
        try:
            await self.execute("SELECT 1")
            return True
        except:
            return False

container = Container()
container.scan()

# Built-in health check endpoint
@app.get("/health")
async def health():
    return await container.health_check()
    # Returns:
    # {
    #   "status": "healthy",
    #   "components": {
    #     "Database": "healthy",
    #     "CacheService": "healthy",
    #     "EmailService": "degraded"
    #   }
    # }
```

### Observability

```python
from dioxide import Container, component
from dioxide.observability import trace, metrics

@component
class UserService:
    def __init__(self, db: Database):
        self.db = db

    @trace  # Automatic OpenTelemetry tracing
    @metrics  # Automatic metrics (calls, latency, errors)
    def get_user(self, user_id: int):
        return self.db.query(f"SELECT * FROM users WHERE id = {user_id}")

# Container-level observability
container = Container(
    trace=True,  # Trace all resolutions
    metrics=True,  # Track resolution times
)

# View metrics
container.metrics()
# Output:
# {
#   "resolutions": {
#     "UserService": {"count": 1234, "avg_time_us": 5.2},
#     "Database": {"count": 1, "avg_time_us": 150.0}
#   },
#   "cache_hits": 98.5,
#   "cache_misses": 1.5
# }
```

**Key features:**
1. **Lifecycle hooks** - Startup, shutdown, graceful termination
2. **Health checks** - Built-in component health monitoring
3. **Observability** - Tracing, metrics, logging integration
4. **Graceful degradation** - Handle component failures
5. **Production debugging** - Runtime introspection without restart

**Anti-patterns to avoid:**
- ❌ No cleanup hooks (resource leaks)
- ❌ Silent failures (components fail, app continues)
- ❌ No production visibility (black box)
- ❌ Difficult to debug in production

**Inspiration:**
- ✅ Spring Boot Actuator (health, metrics, info)
- ✅ Kubernetes liveness/readiness probes
- ✅ OpenTelemetry standard observability

---

## 13. Developer Tooling ⚠️ POST-MLP

**Philosophy:** Great DX includes great tools.

### IDE Integration

**Features:**
- **Autocomplete** for `container.resolve(...)` shows all registered components
- **Go to definition** from `@component` to registration site
- **Find usages** shows where component is resolved
- **Inline hints** show dependency chains
- **Refactoring support** rename class, all DI references update

**VS Code Extension:**
```json
{
  "dioxide.showDependencyHints": true,
  "dioxide.validateOnSave": true,
  "dioxide.highlightComponents": true
}
```

**PyCharm Plugin:**
- Right-click class → "Show Dependency Graph"
- Gutter icons showing component registration status
- Quick-fix suggestions for missing dependencies

### CLI Tools

```bash
# Visualize dependency graph
dioxide graph --output graph.html

# Validate container setup
dioxide validate src/

# List all components
dioxide list

# Find circular dependencies
dioxide check-cycles

# Benchmark resolution performance
dioxide bench

# Generate migration from dependency-injector
dioxide migrate --from dependency-injector --input containers.py
```

### Development Server Integration

```python
# Hot reload support
container = Container(watch=True)  # Reloads on file changes

# Development warnings
container = Container(mode="development")
# Warns about:
# - Slow resolutions (>100ms)
# - Large dependency graphs (>10 deep)
# - Circular dependencies
# - Missing lifecycle hooks
```

**Key features:**
1. **IDE plugins** - VS Code, PyCharm, neovim
2. **CLI tools** - graph, validate, migrate, bench
3. **Hot reload** - Dev server auto-updates
4. **Development warnings** - Catch issues early
5. **Migration tools** - Automated migration from other frameworks

---

## 14. Real-World Patterns ⚠️ POST-MLP

**Philosophy:** Provide guidance for common patterns developers actually use.

### Multi-Tenant Applications

```python
from dioxide import Container, component, Scope

@component(scope=Scope.REQUEST)  # New instance per request
class TenantContext:
    def __init__(self):
        self.tenant_id = None

    def set_tenant(self, tenant_id: str):
        self.tenant_id = tenant_id

@component
class TenantDatabase:
    def __init__(self, context: TenantContext, pool: ConnectionPool):
        self.context = context
        self.pool = pool

    def query(self, sql: str):
        # Use context.tenant_id to route query
        connection = self.pool.get_connection(self.context.tenant_id)
        return connection.execute(sql)

# Per-request container scope
@app.middleware("http")
async def tenant_middleware(request, call_next):
    tenant_id = request.headers.get("X-Tenant-ID")
    with container.request_scope() as request_container:
        context = request_container.resolve(TenantContext)
        context.set_tenant(tenant_id)
        request.state.container = request_container
        return await call_next(request)
```

### Feature Flags

```python
from dioxide import Container, component

@component(when=lambda: feature_enabled("new_search"))
class NewSearchService:
    pass

@component(when=lambda: not feature_enabled("new_search"))
class LegacySearchService:
    pass

# Container resolves based on feature flag
container = Container()
container.scan()
search = container.resolve(SearchService)  # Gets correct implementation
```

### Plugin Systems

```python
from dioxide import Container, component

class Plugin(ABC):
    @abstractmethod
    def process(self, data): ...

@component(tags=["plugin"])
class PluginA(Plugin):
    def process(self, data):
        return f"PluginA: {data}"

@component(tags=["plugin"])
class PluginB(Plugin):
    def process(self, data):
        return f"PluginB: {data}"

# Resolve all plugins
container = Container()
container.scan()
plugins = container.resolve_all(tag="plugin")
for plugin in plugins:
    plugin.process("data")
```

### Repository Pattern

```python
from dioxide import Container, component

@component
class UserRepository:
    def __init__(self, db: Database):
        self.db = db

    def find_by_id(self, user_id: int) -> User:
        return self.db.query_one("SELECT * FROM users WHERE id = ?", user_id)

@component
class UserService:
    def __init__(self, repo: UserRepository):
        self.repo = repo

    def get_user(self, user_id: int) -> User:
        return self.repo.find_by_id(user_id)

# Clean separation: Service → Repository → Database
```

**Key patterns:**
1. **Multi-tenant** - Request-scoped context, tenant routing
2. **Feature flags** - Conditional component registration
3. **Plugin systems** - Tag-based resolution, dynamic discovery
4. **Repository pattern** - Clean layered architecture
5. **CQRS** - Separate read/write models with shared DI

---

## Using This Document

**For product decisions:** Ask "Does this align with the vision?"

**For API design:** Ask "Does this create a joyful moment?"

**For documentation:** Ask "Does this teach the mental model?"

**For features:** Ask "Does this solve a real problem without adding complexity?"

**For bug fixes:** Ask "How can we prevent this category of bugs entirely?"

**For releases:** Ask "Are we moving toward or away from the vision?"

---

**This is a living document.** As we learn from users, we'll update this vision to reflect what actually creates joy in practice.

**Version:** 1.2
**Last Updated:** 2025-11-07
**Owner:** Product & Technical Lead
**Next Review:** After 0.0.2-alpha MLP realignment

**Changelog:**
- v1.2 (2025-11-07): Aligned with MLP_VISION.md, added document status warnings, marked post-MLP sections, updated code examples to use MLP API (global singleton container, `@component.factory`, `@profile`)
- v1.1 (2025-01-30): Added sections on async/await support, configuration management, framework integrations (FastAPI/Flask/Django), production readiness (lifecycle, health checks, observability), developer tooling (IDE/CLI), and real-world patterns (multi-tenant, feature flags, plugins, repository)
