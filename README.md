# dioxide

**Fast, Rust-backed declarative dependency injection for Python**

[![CI](https://github.com/mikelane/dioxide/workflows/CI/badge.svg)](https://github.com/mikelane/dioxide/actions)
[![Release](https://github.com/mikelane/dioxide/actions/workflows/release-automated.yml/badge.svg)](https://github.com/mikelane/dioxide/actions/workflows/release-automated.yml)
[![PyPI version](https://badge.fury.io/py/dioxide.svg)](https://pypi.org/project/dioxide/)
[![Python Versions](https://img.shields.io/pypi/pyversions/dioxide.svg)](https://pypi.org/project/dioxide/)
[![Platform Support](https://img.shields.io/badge/platform-Linux%20%7C%20macOS%20%7C%20Windows-blue)](https://github.com/mikelane/dioxide)
[![Architecture](https://img.shields.io/badge/arch-x86__64%20%7C%20aarch64-green)](https://github.com/mikelane/dioxide)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## Overview

`dioxide` is a dependency injection framework for Python that combines:

- **Declarative Python API** - Simple decorators and type hints
- **Rust-backed performance** - Fast graph construction and resolution via PyO3
- **Type safety** - Full support for mypy and type checkers
- **Clean architecture** - Encourages loose coupling and testability

## Installation

```bash
pip install dioxide
```

### Platform Support

| Platform | x86_64 | ARM64/aarch64 |
|----------|--------|---------------|
| Linux    | ✅     | ✅            |
| macOS    | ✅     | ✅ (M1/M2/M3) |
| Windows  | ✅     | ❌            |

**Python Versions**: 3.11, 3.12, 3.13, 3.14

## Status

**⚠️ ALPHA**: dioxide is in active alpha development. API changes expected between releases.

- **Latest Release**: [v0.0.1-alpha](https://github.com/mikelane/dioxide/releases/tag/v0.0.1-alpha) (Nov 6, 2025) - Published to Test PyPI
- **Current Work**: v0.0.2-alpha - MLP API Realignment (breaking changes)
- **Next Milestone**: v0.1.0-beta - MLP Complete (API freeze) - Mid-December 2025

See [ROADMAP.md](ROADMAP.md) for detailed timeline and [Issues](https://github.com/mikelane/dioxide/issues) for current work.

## Vision

**Make the Dependency Inversion Principle feel inevitable.**

dioxide exists to make clean architecture (ports-and-adapters) the path of least resistance. We combine:

1. **Type-safe DI** - If mypy passes, the wiring is correct
2. **Profile-based implementations** - Swap PostgreSQL ↔ in-memory with one line
3. **Testing without mocks** - Fast fakes at the seams, not mock behavior
4. **Rust-backed performance** - Fast graph operations and resolution

See [MLP_VISION.md](docs/MLP_VISION.md) for the complete design philosophy.

## Quick Start

**⚠️ Note**: API examples show **target MLP syntax** (v0.1.0-beta). Current v0.0.1-alpha uses different syntax. See [CHANGELOG.md](CHANGELOG.md) for migration guide.

```python
from dioxide import container, component, profile
from typing import Protocol

# Define a protocol (the seam)
class EmailProvider(Protocol):
    async def send(self, to: str, subject: str, body: str) -> None: ...

# Production implementation
@component.implements(EmailProvider)
@profile.production
class SendGridEmail:
    async def send(self, to: str, subject: str, body: str) -> None:
        # Real SendGrid API call
        pass

# Test/dev implementation
@component.implements(EmailProvider)
@profile("test", "development")
class FakeEmail:
    def __init__(self):
        self.outbox = []

    async def send(self, to: str, subject: str, body: str) -> None:
        self.outbox.append({"to": to, "subject": subject})

# Business logic depends on protocol, not implementation
@component
class NotificationService:
    def __init__(self, email: EmailProvider):
        self.email = email

    async def send_welcome(self, user_email: str) -> None:
        await self.email.send(user_email, "Welcome!", "Thanks for signing up!")

# Scan and activate profile
container.scan("app", profile="production")  # or "test" for testing

# Use services directly (dependencies auto-injected)
service = NotificationService()
await service.send_welcome("user@example.com")
```

**Key features**:
- `@component` for singleton components (shared across app)
- `@component.factory` for per-request components (new instance each time)
- `@profile` to swap implementations by environment
- Global singleton container (no manual instantiation)
- Constructor injection via type hints

## Features

### v0.0.1-alpha ✅ RELEASED (Nov 6, 2025)
- [x] `@component` decorator for auto-discovery
- [x] Container.scan() for automatic registration
- [x] Constructor dependency injection
- [x] SINGLETON and FACTORY scopes
- [x] Manual provider registration
- [x] Type-safe Container.resolve() with mypy support
- [x] 100% test coverage
- [x] Full CI/CD automation

### v0.0.2-alpha 🔄 IN PROGRESS (MLP API Realignment)
- [ ] `@component.factory` and `@component.implements()` syntax
- [ ] `@profile` decorator system (hybrid approach)
- [ ] `container.scan()` with package and profile parameters
- [ ] Global singleton container pattern
- [ ] Documentation realignment
- [ ] Optional: `container[Type]` syntax

### v0.1.0-beta 🎯 TARGET: Mid-December 2025 (MLP Complete)
- [ ] Lifecycle protocols (`Initializable`, `Disposable`)
- [ ] Circular dependency detection at startup
- [ ] Excellent error messages with suggestions
- [ ] Complete example application
- [ ] FastAPI integration example
- [ ] Testing guide (fakes > mocks philosophy)
- [ ] API frozen (no breaking changes until 2.0)

### Post-MLP Features (v0.2.0+)
See [ROADMAP.md](ROADMAP.md) for post-MLP features:
- Request scoping
- Property injection
- Framework integrations (FastAPI, Flask, Django)
- Developer tooling (CLI, IDE plugins)

## Development

### Prerequisites

- Python 3.11+
- Rust 1.70+
- [uv](https://github.com/astral-sh/uv) for Python package management
- [maturin](https://github.com/PyO3/maturin) for building Rust extensions

### Setup

```bash
# Clone the repository
git clone https://github.com/mikelane/dioxide.git
cd dioxide

# Install dependencies with uv
uv venv
source .venv/bin/activate  # or `.venv\Scripts\activate` on Windows
uv pip install -e ".[dev]"

# Build the Rust extension
maturin develop

# Run tests
pytest

# Run all quality checks
tox
```

### Development Workflow

```bash
# Format code
tox -e format

# Lint
tox -e lint

# Type check
tox -e type

# Run tests for all Python versions
tox

# Run tests with coverage
tox -e cov

# Mutation testing
tox -e mutate
```

### Pre-commit Hooks

Install pre-commit hooks to ensure code quality:

```bash
pre-commit install
```

## Architecture

```
dioxide/
├── python/dioxide/       # Python API
│   ├── __init__.py
│   ├── container.py       # Main Container class
│   ├── decorators.py      # @component decorator
│   └── scope.py           # Scope enum
├── rust/src/              # Rust core
│   └── lib.rs             # PyO3 bindings and graph logic
├── tests/                 # Python tests
└── pyproject.toml         # Project configuration
```

### Key Design Decisions

1. **Rust for graph operations** - Dependency graphs can get complex; Rust's performance and safety help scale
2. **Python-first API** - Developers work in pure Python; Rust is an implementation detail
3. **Type hints as the contract** - Leverage Python's type system for DI metadata
4. **Explicit over implicit** - Registration is manual to avoid surprises
5. **Test-driven development** - Every feature starts with failing tests

## Comparison to Other Frameworks

| Feature | dioxide | dependency-injector | injector |
|---------|----------|---------------------|----------|
| Type-based DI | ✅ | ✅ | ✅ |
| Rust-backed | ✅ | ❌ | ❌ |
| Scopes | ✅ | ✅ | ✅ |
| Lifecycle | ✅ | ✅ | ❌ |
| Cycle detection | ✅ (planned) | ❌ | ❌ |
| Performance* | 🚀 (goal) | ⚡ | ⚡ |

*Benchmarks coming in v0.2

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

See [ROADMAP.md](ROADMAP.md) for the complete product roadmap and [MLP_VISION.md](docs/MLP_VISION.md) for the design philosophy.

## License

MIT License - see [LICENSE](LICENSE) for details.

## Acknowledgments

- Inspired by [dependency-injector](https://github.com/ets-labs/python-dependency-injector) and Spring Framework
- Built with [PyO3](https://github.com/PyO3/pyo3) and [maturin](https://github.com/PyO3/maturin)
- Graph algorithms powered by [petgraph](https://github.com/petgraph/petgraph)

---

**⚠️ Alpha Status**: dioxide is in active alpha development. Breaking API changes expected until v0.1.0-beta (mid-December 2025), when the API will freeze. Not recommended for production use yet.

**MLP Timeline**:
- **Now**: v0.0.2-alpha - API realignment with MLP Vision
- **Dec 2025**: v0.1.0-beta - MLP Complete, API frozen ✨
- **2026+**: Post-MLP features, ecosystem growth, 1.0 stable
