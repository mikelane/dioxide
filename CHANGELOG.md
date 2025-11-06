# Changelog

All notable changes to dioxide will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2025-02-05

### Added
- Python 3.14 support across all platforms
- ARM64/aarch64 builds for Apple Silicon and AWS Graviton
- Comprehensive smoke tests for wheel validation

### Changed
- Modernized CI/CD pipeline with 100/100 state-of-the-art score
- Switched to PyPI Trusted Publishing (OIDC) for secure releases
- SHA-pinned all GitHub Actions for supply chain security
- Optimized Rust release builds (LTO, single codegen unit)
- Reduced test matrix to Python 3.11, 3.13, 3.14 for cost efficiency

### Fixed
- Automated semantic versioning configuration for 0.x releases
- CI/CD workflow with proper version synchronization

## [0.0.1-alpha] - 2025-01-27

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

[0.1.0]: https://github.com/mikelane/dioxide/releases/tag/v0.1.0
[0.0.1-alpha]: https://github.com/mikelane/dioxide/releases/tag/v0.0.1-alpha
