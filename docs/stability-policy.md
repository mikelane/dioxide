# API Stability Policy

dioxide is committed to providing a stable, predictable API that you can depend on for
long-term projects. This document defines what "stable" means, what can change, and how
we handle breaking changes.

## Semantic Versioning Commitment

dioxide follows [Semantic Versioning 2.0.0](https://semver.org/):

- **MAJOR** (X.0.0): Breaking changes to the public API. Requires migration.
- **MINOR** (0.X.0): New features that are backwards compatible. Safe to upgrade.
- **PATCH** (0.0.X): Bug fixes only. Safe to upgrade.

Pre-release versions (alpha, beta, rc) may contain breaking changes within the
pre-release series. Use pinned versions for pre-releases.

## Public API Definition

The **public API** consists of everything exported from `dioxide` and `dioxide.testing`
that does **not** start with an underscore.

### What Is Public

Any symbol listed in `dioxide.__all__` without a leading underscore is public:

| Symbol | Module | Description |
|--------|--------|-------------|
| `@service` | `dioxide` | Service decorator |
| `@adapter.for_()` | `dioxide` | Adapter registration decorator |
| `@lifecycle` | `dioxide` | Lifecycle management decorator |
| `Profile` | `dioxide` | Profile class and built-in constants |
| `Container` | `dioxide` | Dependency injection container |
| `Container.scan()` | `dioxide` | Module scanning for registration |
| `Container.resolve()` | `dioxide` | Dependency resolution |
| `Container[T]` | `dioxide` | Bracket syntax for resolution |
| `Container.create_scope()` | `dioxide` | Request-scoped container creation |
| `ScopedContainer` | `dioxide` | Scoped container for request isolation |
| `Scope` | `dioxide` | Scope enum (SINGLETON, FACTORY) |
| `container` | `dioxide` | Global container instance |
| `reset_global_container()` | `dioxide` | Reset global container state |
| `fresh_container()` | `dioxide.testing` | Test utility for isolated containers |
| `DioxideError` | `dioxide` | Base exception class |
| `AdapterNotFoundError` | `dioxide` | Raised when no adapter matches |
| `ServiceNotFoundError` | `dioxide` | Raised when service is not registered |
| `CircularDependencyError` | `dioxide` | Raised on circular dependencies |
| `ResolutionError` | `dioxide` | Base resolution error |
| `ScopeError` | `dioxide` | Raised on scope violations |
| `CaptiveDependencyError` | `dioxide` | Raised on captive dependency detection |

### What Is Internal

Anything prefixed with an underscore has **no stability guarantees**:

| Symbol | Reason |
|--------|--------|
| `_registry` | Internal registration implementation |
| `_clear_registry()` | Internal testing utility |
| `_get_registered_components()` | Internal introspection |
| `rust/src/*` | Rust implementation details |

Internal APIs may change or be removed in any release without notice. If you depend on
an internal API, [open an issue](https://github.com/mikelane/dioxide/issues) requesting
a public alternative.

## API Stability Classification

Each public API has a stability level:

| API | Stability | Guarantee |
|-----|-----------|-----------|
| `@service` | **Stable** | Signature will not break |
| `@adapter.for_()` | **Stable** | Signature will not break |
| `@lifecycle` | **Stable** | Signature will not break |
| `Profile` constants | **Stable** | Existing values will not change |
| `Profile()` constructor | **Stable** | Custom profiles always supported |
| `Container()` | **Stable** | Constructor signature may add optional kwargs |
| `Container.scan()` | **Stable** | Signature may add optional kwargs |
| `Container.resolve()` | **Stable** | Signature will not break |
| `Container[T]` | **Stable** | Bracket syntax will not break |
| `Container.create_scope()` | **Stable** | Signature will not break |
| `Scope` enum | **Stable** | Existing values will not change; new values may be added |
| `fresh_container()` | **Stable** | Testing utility will be maintained |
| Exception classes | **Stable** | Class hierarchy will not break |
| Framework integrations | **Stable** | `dioxide.fastapi`, `dioxide.flask`, etc. |

**Stable** means the signature and behavior will not change in a backwards-incompatible
way without following the deprecation process described below.

**"Signature may add optional kwargs"** means new optional keyword arguments may be
added in minor releases. Positional arguments and existing keyword arguments will not
change.

## What Constitutes a Breaking Change

The following changes are **breaking** and require a major version bump:

- Removing a public API symbol
- Changing the signature of a public function or method in an incompatible way
  (removing parameters, changing parameter types, changing return types)
- Changing the behavior of a public API in a way that breaks existing correct usage
- Renaming or moving a public symbol to a different module
- Removing a `Profile` constant or changing its string value
- Changing the exception hierarchy (removing exception classes, changing base classes)
- Dropping support for a Python version

## What Is NOT a Breaking Change

The following changes are **not breaking** and may happen in any minor or patch release:

- Adding new public API symbols (new decorators, classes, functions)
- Adding new optional keyword arguments to existing functions
- Adding new `Profile` constants or `Scope` values
- Adding new exception classes
- Bug fixes that change incorrect behavior to match documentation
- Performance improvements
- Changes to internal APIs (`_prefixed` symbols, Rust internals)
- Improving error messages
- Adding new framework integrations
- Documentation updates

## Deprecation Process

When a public API needs to change, dioxide follows a structured deprecation process:

### Step 1: Deprecation Warning (Minor Release)

The deprecated API continues to work but emits a `DeprecationWarning` with:
- The version in which the deprecation was introduced
- The replacement API or migration path
- The version in which the deprecated API will be removed

```python
# Example deprecation warning
import warnings
warnings.warn(
    "old_function() is deprecated since v2.1.0. "
    "Use new_function() instead. "
    "old_function() will be removed in v3.0.0.",
    DeprecationWarning,
    stacklevel=2,
)
```

### Step 2: Documentation and CHANGELOG

- The CHANGELOG entry marks the deprecation
- API reference documentation marks the API as deprecated
- Migration instructions are provided in the release notes

### Step 3: Migration Support

- Find-and-replace patterns are documented for simple renames
- Codemod scripts are provided when feasible for complex changes
- The migration guide includes before/after code examples

### Step 4: Removal (Next Major Release)

- The deprecated API is removed in the next major version
- The major version release notes include a complete migration guide
- All breaking changes are listed with migration instructions

### Deprecation Timeline

- **Minimum lifetime**: A deprecated API will continue to work for at least **2 minor
  versions** after the deprecation is introduced
- **Removal**: Deprecated APIs are removed only in major version releases
- **Example**: If an API is deprecated in v2.1.0, it will work through at least v2.3.0
  and be removed no earlier than v3.0.0

## Supported Versions

| Version | Support Level |
|---------|--------------|
| Latest stable | Full support: bug fixes, security patches, new features |
| Previous minor | Security fixes and critical bug fixes only |
| Older versions | No active support; documentation remains available |

## Notification Process

Users are informed about upcoming changes through:

1. **Deprecation warnings** in the Python runtime (visible during development and testing)
2. **CHANGELOG entries** for every deprecation and breaking change
3. **Release notes** on GitHub with migration instructions
4. **Documentation** updated to mark deprecated APIs

### CHANGELOG Format for Breaking Changes

Breaking changes in the CHANGELOG are marked with a **BREAKING** indicator:

```markdown
## v3.0.0

### BREAKING

- **`old_function()` removed** - Use `new_function()` instead.
  See [migration guide](migration-v2-to-v3.md) for details.
  Affected API: `dioxide.old_function`
```

## Commitment to Migration Support

dioxide learned from the v1.x to v2.0 transition. For any future major version:

1. A **migration guide** will be published before the major release
2. All breaking changes will have **before/after code examples**
3. **Find-and-replace patterns** will be documented at minimum
4. **Codemod tooling** (e.g., using `libcst` or `bowler`) will be considered for
   complex migrations
5. The previous major version will receive security fixes for at least **6 months**
   after the new major release

## Pinning Recommendations

For production applications:

```
# Pin to minor version for stability with patch updates
dioxide>=2.1,<2.2

# Or pin exactly for maximum reproducibility
dioxide==2.1.3
```

For libraries that depend on dioxide:

```
# Allow minor version updates for compatibility
dioxide>=2.0,<3.0
```
