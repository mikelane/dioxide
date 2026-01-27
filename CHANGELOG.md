# Changelog

All notable changes to dioxide will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [2.0.1] - 2026-01-27

### Added

- **Container introspection API** (#360)
  - `container.debug()` prints summary of all registered services and adapters
  - `container.explain(cls)` shows the resolution tree for a type
  - `container.graph(format)` generates Mermaid or DOT format dependency graphs

- **Config injection pattern** (#357, #359)
  - `container.register_instance(cls, instance)` registers pre-created instances
  - Works with `@service` decorated classes and Pydantic BaseSettings
  - Registration before `scan()` takes precedence over decorator registration
  - Type-safe: instance must be compatible with the registered type

- **Rich error messages** (#356, #358)
  - `DioxideError` base class with structured formatting (title, context, suggestions, example)
  - Builder methods: `with_context()`, `with_suggestion()`, `with_example()`
  - Exception constructors accept structured parameters for programmatic access
  - `AdapterNotFoundError`: accepts port, profile, available_adapters
  - `ServiceNotFoundError`: accepts service, profile, dependencies, failed_dependency
  - `ScopeError`: accepts component, required_scope
  - `CaptiveDependencyError`: accepts parent, parent_scope, child, child_scope

- **Async lifecycle verification** (#355)
  - Comprehensive test suite documenting async `initialize()` and `dispose()` behavior
  - Verified dependency ordering, rollback on failure, error handling patterns

### Fixed

- **pytest no longer required at runtime** (#363)
  - `import dioxide` now works without pytest installed
  - pytest fixtures only defined when pytest is available
  - `fresh_container` context manager works without pytest

### Documentation

- Fixed incorrect method name in CHANGELOG

## [2.0.0] - 2026-01-23

### ⚠️ BREAKING CHANGES

- **Profile is now an extensible `str` subclass instead of `StrEnum`** (#333)
  - `Profile.PRODUCTION`, `Profile.TEST`, etc. still work unchanged
  - **Broken:** `profile.value` → use `str(profile)` or just `profile`
  - **Broken:** `profile.name` → not available, use the constant directly
  - **Broken:** `for p in Profile:` → use explicit list `[Profile.PRODUCTION, Profile.TEST, ...]`
  - **Broken:** `Profile['PRODUCTION']` → use `Profile.PRODUCTION` directly
  - **New:** Custom profiles are now first-class: `MY_PROFILE = Profile('custom')`

### Added

- **Container introspection API** (#327)
  - `container.list_registered()` returns all registered types
  - Useful for debugging and verifying container state

- **Pytest fixtures** (#324)
  - `fresh_container` fixture for isolated test containers
  - `production_container` and `test_container` convenience fixtures
  - Available from `dioxide.testing` module

- **Terse error messages** (#323)
  - Runtime errors now 1-3 lines max with actionable guidance
  - No more stack trace noise for common configuration errors
  - Clear "what went wrong" + "how to fix it" format

- **Deprecation warnings for non-canonical profile patterns** (#333)
  - Using string profiles (`profile='production'`) now emits `DeprecationWarning`
  - Guides users to canonical `Profile.PRODUCTION` pattern
  - Strings still work but will be removed in v2.0

### Documentation

- **Developer Experience (DX) Overhaul** - Epic #309 complete (13/13 issues)
  - Package scanning guide: behavior, side effects, best practices (#335, #321)
  - Async/sync lifecycle patterns guide (#334, #320)
  - Decorator order clarification (order is irrelevant) (#331, #322)
  - Global vs instance container usage guide (#329, #313)
  - @service vs @adapter decision tree and mental model (#326, #314)
  - Real-world pattern examples and migration guides (#328, #319)
  - Auto-scan documentation (#310)
  - Profile system canonical pattern docs (#311)
  - Scope parameter for @service documented (#315)

### Tests

- Comprehensive BDD tests for auto-scan feature (#332)
- Scope parameter tests for @service decorator (#330)
- Rust backend benchmark suite with performance baselines (#325, #318)

## [1.1.2] - 2026-01-20

### Added

- **Multi-binding / Collection injection** (#255, #308)
  - `@adapter.for_(Port, multi=True)` registers multiple adapters for the same port
  - `@adapter.for_(Port, multi=True, priority=N)` controls injection order (lower first)
  - `list[Port]` type hints automatically collect all matching adapters
  - Profile filtering applies — only active profile adapters included
  - Enables plugin patterns, operator chains, and extensible architectures

### Documentation

- Comprehensive documentation overhaul for v1.0.0 stable release
  - New "Migration from Mocks" guide with side-by-side examples (#287)
  - Philosophy essay explaining why dioxide exists (#305)
  - FAQ entry: "Why not just use @patch?" (#289)
  - Service-locator tradeoff acknowledgment in function injection docs (#288)
  - Reader persona navigation page (#299)
  - Architecture golden path diagram (#298)
  - Cross-references between testing guides (#302, #303)
  - Updated README tagline and Anti-goals section (#286)

### Infrastructure

- GitHub Sponsors funding link added
- Bumped GitHub Actions dependencies (actions/cache, github/issue-metrics)

## v1.0.1 (2025-12-21)

### Fixed

- Resolved CI failures for Lint Python and Check Documentation Links (#277)
  - Added `djangorestframework-stubs` for proper DRF type checking
  - Set `myst_linkify_fuzzy_links=False` to prevent linkify from matching bare filenames as URLs

### Changed

- Slimmed down CLAUDE.md from ~7,500 to ~1,400 tokens (#275)
  - Removed content duplicated in `.claude/rules/` files
  - Added modular guidelines table pointing to rules files

### Infrastructure

- Bumped GitHub Actions dependencies (#274)
  - actions/checkout 5.0.0 → 6.0.1
  - codecov/codecov-action, actions/cache, actions/upload-artifact, and others

## v1.0.0 (2025-12-12)

### Highlights

- **MLP Complete**: All 6 phases of the Minimum Lovable Product are complete
- **Production Ready**: Stable API with no breaking changes until v2.0
- **Framework Integrations**: FastAPI, Flask, Celery, Click, Django, DRF, Django Ninja

### Added

- **Django Integration** (`dioxide.django`)
  - `configure_dioxide()` for app configuration
  - `DioxideMiddleware` for request-scoped containers
  - `inject()` helper for dependency resolution in views
  - Thread-local storage for WSGI request safety

- **Django REST Framework Support**
  - Works with `APIView`, `ViewSet`, and `@api_view` decorators
  - Full compatibility with DRF's request lifecycle

- **Django Ninja Integration** (`dioxide.ninja`)
  - `configure_dioxide(api, profile=...)` for NinjaAPI setup
  - Same middleware + inject() pattern as Django integration
  - Sync and async endpoint support

### Documentation

- Comprehensive Django integration guide at `docs/integrations/django.md`
- Updated README with Framework Integrations section
- MLP Vision document marked all phases COMPLETE

### Infrastructure

- 44 new tests for Django/DRF/Ninja integrations
- 93.94% overall test coverage


### Added
- Initial alpha release
- `@component` decorator for declarative dependency injection auto-discovery
- `Container.scan()` for automatic component registration and dependency resolution
- Constructor dependency injection via type hints
- SINGLETON and FACTORY scopes for lifecycle management
- Manual provider registration with `Container.register()`
- Type-safe `Container.resolve()` with full mypy support
- Python 3.11, 3.12, 3.13 support
- Cross-platform support (Linux, macOS, Windows)

### Fixed
- Singleton caching bug in Rust container - Factory providers now correctly cached
- Recursive import issues resolved with better module organization

### Infrastructure
- GitHub Actions CI pipeline with test matrix (3 Python versions × 3 platforms)
- Automated code quality checks (ruff, mypy, clippy)
- Coverage reporting with Codecov integration
- 100% branch coverage requirement enforced
- Pre-commit hooks for consistent code quality
- Automated release workflow with multi-platform wheel building
- PyPI publishing automation (Test PyPI for alpha releases)

### Documentation
- Comprehensive README with quick start guide
- Design documents for CI/CD workflows
- COVERAGE.md explaining testing strategy for Python/Rust hybrid projects
- CLAUDE.md with project guidelines and best practices

[2.0.1]: https://github.com/mikelane/dioxide/releases/tag/v2.0.1
[2.0.0]: https://github.com/mikelane/dioxide/releases/tag/v2.0.0
[1.1.2]: https://github.com/mikelane/dioxide/releases/tag/v1.1.2
[0.2.1]: https://github.com/mikelane/dioxide/releases/tag/v0.2.1
[0.1.1]: https://github.com/mikelane/dioxide/releases/tag/v0.1.1
[0.1.0-beta.2]: https://github.com/mikelane/dioxide/releases/tag/v0.1.0-beta.2
[0.1.0-beta]: https://github.com/mikelane/dioxide/releases/tag/v0.1.0-beta
[0.1.0]: https://github.com/mikelane/dioxide/releases/tag/v0.1.0
[0.0.4-alpha.1]: https://github.com/mikelane/dioxide/releases/tag/v0.0.4-alpha.1
[0.0.1-alpha]: https://github.com/mikelane/dioxide/releases/tag/v0.0.1-alpha

## v0.4.1 (2025-11-29)

### Feat

- add FastAPI integration module with DioxideMiddleware and Inject helper (#182)
- add optional profile parameter to Container constructor (#236)
- add hex logo for favicon and hide landing page title

### Docs

- add library author guide to cookbook (#237)
- add why dioxide comparison page (#234)
- add cookbook section with real-world recipes (#233)
- add architecture diagrams for hexagonal patterns (#232)
- add dioxide logo and establish brand color scheme (#231)
- create visual landing page with hero section (#229)
- add sphinx-autobuild for live reload development (#227)
- add sphinx-copybutton, sphinx-design, and mermaid extensions (#226)
- update README with honest performance positioning (#225)
- convert index.rst to MyST Markdown (#223)
- switch to Furo theme with autoapi_root (#224)
- modernize ReadTheDocs configuration (#221)
- add migration guide from dependency-injector (#186)
- add RELEASE.md documenting release process (#203)

### Fix

- remove redundant TOC from getting_started
- reduce hero font size from sd-fs-1 to sd-fs-2
- use padding-top to clear theme icons instead of width constraints
- prevent hero text from colliding with theme icons
- add pyo3.rs to linkcheck ignore list
- add GitHub blob URLs to linkcheck ignore list (#214)
- publish to PyPI before creating GitHub Release (#199)
- strip wheel trailing data at build time (#200)
- sync release test dependencies with CI (#198)

### CI

- update GitHub Actions to latest versions (#230)
- add linkcheck to CI workflow (#228)

### Perf

- add honest benchmark comparison vs dependency-injector (#188)

## v0.3.1 (2025-11-27)

### Fix

- minor documentation fixes

## v0.3.0 (2025-11-27)

### Feat

- add warning for empty profile matches in container.scan() (#191)
- add Scope.REQUEST enum value (#190)

### Fix

- use pypa/gh-action-pypi-publish instead of maturin upload
- remove Test PyPI step to prevent version burn (#178)

## v0.2.1 (2025-11-25)

### Feat

- add dioxide.testing module with fresh_container helper (#177)
- implement container.reset() method (#175)
- add scope parameter to @adapter.for_() (#173)

## v0.1.1 (2025-11-24)

## v0.1.0 (2025-11-24)

### Feat

- configure versioned documentation for ReadTheDocs (#152) (#164)
- configure ReadTheDocs for automated doc builds (#155)
- add documentation build to CI/CD pipeline (#162)
- Phase 1 CI/CD release process improvements (#137)

### Fix

- add Python 3.14 to tox test matrix
- make mypy type-checking tests hermetic and parallel-safe
- add missing test dependencies to tox environments

## v0.1.0-beta.2 (2025-11-23)

### Fix

- strip trailing data from wheels before PyPI upload

## v0.1.0-beta (2025-11-23)

### Feat

- add performance benchmarking infrastructure (#18) (#133)
- add comprehensive FastAPI integration example (#127) (#132)

### Fix

- use windows-2022 runner to avoid Windows Server 2025 wheel issues
- cache lifecycle instances to prevent disposal bugs (#135) (#136)

## v0.0.4-alpha.1 (2025-11-22)

## v0.0.4-alpha (2025-11-22)

### Feat

- implement package scanning for container.scan() (#86) (#126)
- implement container lifecycle runtime support (#95) (#125)
- add type stubs for @lifecycle decorator (#67) (#122)
- implement @lifecycle decorator for opt-in lifecycle management (#67) (#121)
- replace KeyError with descriptive error messages (#114) (#120)
- add deprecation warnings to @component API (#119)
- add port-based resolution to container (#104)
- add Profile enum support to container.scan() (#97) (#103)
- add @adapter.for_() decorator for hexagonal architecture (#96)
- add @service decorator for core domain logic (#96)
- add Profile enum for hexagonal architecture (#96)

### Fix

- correct version format to 0.0.4-alpha for Cargo semver compatibility
- restore @lifecycle runtime implementation and tests (#67) (#123)
- enable force_grid_wrap in isort config

## v0.0.2a1 (2025-11-09)

### Feat

- support both manual tags and semantic-release in workflow
- implement @component.implements(Protocol) (#66) (#79)
- implement container.scan() with package and profile parameters (#69) (#80)
- implement @component.factory syntax (#65) (#78)
- implement global singleton container (#70) (#77)
- upgrade PyO3 to 0.27 for Python 3.14 support (#35) (#36)
- **infrastructure**: implement world-class issue lifecycle management (#37)
- add Python 3.14 support with uv package manager
- add Python 3.14 support and modernize CI/CD pipeline
- add release automation and CHANGELOG for 0.0.1-alpha (#23)
- **api**: add register_singleton() and register_factory() convenience methods
- implement @component decorator with auto-discovery and dependency injection
- implement provider registration with three provider types
- implement basic Container with Rust core and Python wrapper
- add GitHub Actions CI/CD pipelines and behave BDD framework
- add Gherkin feature for basic Container structure

### Fix

- disable semantic-release entirely
- remove deprecated release.yml workflow (#52) (#53)
- prevent duplicate workflow runs from semantic-release commits (#50)
- upgrade download-artifact to v4.3.0 to fix checksum failures
- use correct TOML path for Cargo.toml version update
- configure semantic-release to update Cargo.toml version
- remove broken Cargo.toml update step from release workflow (#49)
- use SEMANTIC_RELEASE_TOKEN and official action (#47) (#48)
- add allow_zero_version=true to semantic-release config (#45) (#46)
- disable automated release workflow until v0.x config is fixed (#43) (#44)
- reset version to 0.x and configure semantic-release properly (#41) (#42)
- remove invalid YAML syntax from issue-triage workflow (#38)
- download artifacts with patterns to prevent corruption
- remove Unicode checkmark for Windows compatibility
- remove future annotations from smoke test for local class resolution
- wheel installation selects platform-compatible wheel
- **ci**: correct PyO3/maturin-action SHA to v1.49.4
- **container**: resolve forward references in type hints using class globals
- **ci**: update codecov action SHA to v5.5.1
- **ci**: correct Swatinem/rust-cache SHA to v2.8.1
- **ci**: temporarily disable automated release workflow
- **ci**: set major_on_zero to false for 0.x versioning
- **ci**: don't commit Cargo.lock in automated release
- **ci**: add missing toolchain parameter to Rust setup actions
- **release**: add mypy to test dependencies (#23)
- **ci**: consolidate and fix GitHub Actions workflows (#22)
- **ci**: explicitly install maturin before running maturin develop
- **ci**: use official astral-sh/setup-uv action for cross-platform support
- **ci**: use uv run for maturin commands
- **ci**: repair broken GitHub Actions pipeline
- distinguish singleton vs transient factories in Rust container
- resolve circular import and configure Python source directory
- correct step definition matching in behave tests
- add Rust library path and type stubs

### Refactor

- rename package from rivet-di to dioxide
