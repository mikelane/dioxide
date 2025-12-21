# Changelog

All notable changes to dioxide will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
