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

🚧 **Work in Progress** - Currently implementing the v0.1 Walking Skeleton.

See [Issues](https://github.com/mikelane/dioxide/issues) and [Milestones](https://github.com/mikelane/dioxide/milestones) for current progress.

## Vision

Traditional Python DI frameworks like `dependency-injector` are feature-rich but can be slow with large dependency graphs. `dioxide` aims to provide:

1. **Fast graph construction** using Rust's `petgraph`
2. **Type-based resolution** via Python's `__annotations__`
3. **Lifecycle management** with proper shutdown ordering
4. **Clear error messages** for missing dependencies and cycles

## Quick Start (Planned API)

```python
from dioxide import Container, Scope, component

@component(scope=Scope.SINGLETON)
class DatabaseConnection:
    def __init__(self, connection_string: str):
        self.connection_string = connection_string

@component(scope=Scope.SINGLETON)
class UserRepository:
    def __init__(self, db: DatabaseConnection):
        self.db = db

# Create container and register components
container = Container()
container.register_value('connection_string', 'postgresql://localhost/mydb')
container.register(DatabaseConnection)
container.register(UserRepository)

# Resolve dependencies
repo = container.resolve(UserRepository)
# repo.db is automatically injected

# Clean shutdown
container.shutdown()
```

## Features

### v0.1 Walking Skeleton (In Progress)
- [x] Basic project structure
- [ ] Type-based dependency resolution
- [ ] Singleton and factory scopes
- [ ] Value injection by parameter name
- [ ] Duplicate registration prevention
- [ ] Clear error messages

### v0.2 Core Features (Planned)
- [ ] Named tokens for disambiguation
- [ ] Circular dependency detection
- [ ] Graceful shutdown with reverse ordering
- [ ] Comprehensive test coverage (>95%)
- [ ] Mutation testing with `mutmut`

### Future Enhancements (Backlog)
- [ ] Conditional registration
- [ ] Provider functions
- [ ] Property injection
- [ ] Performance benchmarks vs. `dependency-injector`
- [ ] Documentation site

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

### Roadmap

- v0.1: Walking skeleton with basic DI
- v0.2: Production-ready core features
- v0.3: Performance optimization and benchmarks
- v1.0: Stable API

## License

MIT License - see [LICENSE](LICENSE) for details.

## Acknowledgments

- Inspired by [dependency-injector](https://github.com/ets-labs/python-dependency-injector) and Spring Framework
- Built with [PyO3](https://github.com/PyO3/pyo3) and [maturin](https://github.com/PyO3/maturin)
- Graph algorithms powered by [petgraph](https://github.com/petgraph/petgraph)

---

**Note**: This project is under active development. APIs may change before v1.0.
