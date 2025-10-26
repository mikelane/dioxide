# Contributing to dioxide

Thank you for your interest in contributing to dioxide! This document provides guidelines and instructions for contributing.

## Code of Conduct

Be respectful, inclusive, and professional. We're all here to build something useful together.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork**:
   ```bash
   git clone https://github.com/YOUR_USERNAME/dioxide.git
   cd dioxide
   ```
3. **Set up development environment**:
   ```bash
   uv venv
   source .venv/bin/activate
   uv pip install -e ".[dev]"
   maturin develop
   pre-commit install
   ```

## Development Workflow

### Before Making Changes

1. Check existing [issues](https://github.com/mikelane/dioxide/issues) and [pull requests](https://github.com/mikelane/dioxide/pulls)
2. Create an issue if one doesn't exist (use the appropriate template)
3. Discuss your approach in the issue before starting work on large changes

### Making Changes

1. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Write tests first** (TDD approach):
   - Add failing tests in `tests/`
   - Run `pytest` to confirm they fail
   - Implement the feature
   - Run `pytest` to confirm they pass

3. **Follow code style**:
   - Python: Single quotes, vertical hanging indent for imports
   - Rust: Standard `rustfmt` style
   - Run `tox -e format` to auto-format
   - Run `tox -e lint` to check

4. **Type check**:
   ```bash
   tox -e type
   ```

5. **Run full test suite**:
   ```bash
   tox
   ```

### Commit Guidelines

- Use clear, descriptive commit messages
- Follow conventional commits format (optional but appreciated):
  - `feat: Add named token support`
  - `fix: Resolve circular dependency detection bug`
  - `docs: Update README with examples`
  - `test: Add tests for shutdown lifecycle`
  - `refactor: Simplify graph construction logic`

### Pull Request Process

1. **Update documentation** if needed (README, docstrings, etc.)
2. **Ensure all tests pass**:
   ```bash
   tox
   ```
3. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```
4. **Create a Pull Request** on GitHub
5. **Fill out the PR template** with:
   - Description of changes
   - Related issue(s)
   - Testing performed
   - Checklist completion

### PR Checklist

- [ ] Tests pass locally (`tox`)
- [ ] Code is formatted (`tox -e format`)
- [ ] Linting passes (`tox -e lint`)
- [ ] Type checking passes (`tox -e type`)
- [ ] Documentation updated (if applicable)
- [ ] CHANGELOG.md updated (if applicable)
- [ ] Commit messages are clear

## Testing Guidelines

### Python Tests

- Use `pytest` for all Python tests
- Place tests in `tests/` directory
- Test file naming: `test_*.py`
- Use descriptive test names: `test_container_resolves_singleton_correctly`
- Avoid "should" in test names (use "returns" or "raises" instead)
- Keep tests simple - no branching or loops
- Use parametrize for multiple similar test cases

### Mutation Testing

- Run `tox -e mutate` to check test quality
- Aim for high mutation coverage (killed mutants)
- Add tests if mutants survive

### Rust Tests

- Add unit tests in Rust where appropriate
- Run `cargo test` in the `rust/` directory

## Code Style

### Python

- Python 3.11+ syntax
- Type hints for all functions
- Single quotes for strings (except docstrings)
- Docstrings for all public APIs
- Line length: 100 characters
- Use `isort` for imports (vertical hanging indent)

### Rust

- Follow standard Rust conventions
- Run `cargo fmt` and `cargo clippy`
- Document public APIs

## Documentation

- Update docstrings for new/changed APIs
- Add examples to README if introducing new features
- Update CHANGELOG.md for user-facing changes

## Release Process (Maintainers Only)

1. Update version in `pyproject.toml` and `Cargo.toml`
2. Update `CHANGELOG.md`
3. Create a git tag: `git tag -a v0.X.0 -m "Release v0.X.0"`
4. Push tag: `git push origin v0.X.0`
5. Build and publish:
   ```bash
   maturin build --release
   maturin publish
   ```

## Questions?

- Open an issue with the `question` label
- Check existing issues and discussions

## Thank You!

Your contributions make dioxide better for everyone. We appreciate your time and effort! 🎉
