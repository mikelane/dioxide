# Contributing to dioxide

Thank you for your interest in contributing to dioxide! This document provides guidelines and instructions for contributing.

## Code of Conduct

Be respectful, inclusive, and professional. We're all here to build something useful together.

## Getting Started

**IMPORTANT**: All contributions MUST go through the Pull Request process. External contributions MUST be made through forks. Maintainers work directly in the main repository but MUST still create PRs for all changes.

### For External Contributors (Fork-Based Workflow)

1. **Search First**: Before creating a new issue or PR, search [existing issues](https://github.com/mikelane/dioxide/issues) to avoid duplicates
2. **Read the Docs**: Familiarize yourself with the project documentation
3. **Understand the Issue Lifecycle**: Review our [Issue Lifecycle Documentation](docs/issue-lifecycle.md) and [Label Guide](docs/label-guide.md)
4. **Fork the repository** on GitHub (click the "Fork" button in the top right)
5. **Clone your fork**:
   ```bash
   git clone https://github.com/YOUR_USERNAME/dioxide.git
   cd dioxide
   ```
6. **Add upstream remote** to keep your fork in sync:
   ```bash
   git remote add upstream https://github.com/mikelane/dioxide.git
   git fetch upstream
   ```
7. **Set up development environment**:
   ```bash
   uv venv
   source .venv/bin/activate
   uv sync --all-extras
   uv run maturin develop
   pre-commit install
   ```

### For Maintainers (Direct Repository Access)

1. **Clone the repository** directly:
   ```bash
   git clone https://github.com/mikelane/dioxide.git
   cd dioxide
   ```
2. **Set up development environment**:
   ```bash
   uv venv
   source .venv/bin/activate
   uv sync --all-extras
   uv run maturin develop
   pre-commit install
   ```
3. **Create feature branches** directly in the main repository
4. **IMPORTANT**: ALL changes MUST go through the PR process - no direct pushes to main
5. **All work MUST have an associated GitHub issue** - create one before starting work

## How to Contribute

There are many ways to contribute to dioxide:

- 🐛 **Report bugs** using the [Bug Report template](.github/ISSUE_TEMPLATE/bug_report.yml)
- ✨ **Suggest features** using the [Feature Request template](.github/ISSUE_TEMPLATE/feature_request.yml)
- 📈 **Propose enhancements** using the [Enhancement template](.github/ISSUE_TEMPLATE/enhancement.yml)
- 📚 **Improve documentation** using the [Documentation template](.github/ISSUE_TEMPLATE/documentation.yml)
- ❓ **Ask questions** using the [Question template](.github/ISSUE_TEMPLATE/question.yml) or [Discussions](https://github.com/mikelane/dioxide/discussions)
- 💻 **Write code** by picking up issues labeled `good-first-issue` or `help-wanted`

### Reporting Bugs

Found a bug? Help us improve by reporting it!

**What makes a good bug report:**
- Clear, descriptive title: `[BUG] Container crashes when adding circular references`
- Minimal reproducible example that demonstrates the issue
- Expected vs actual behavior clearly stated
- Environment information (dioxide version, Python version, OS)
- Stack traces or error messages included
- Severity label (Critical/High/Medium/Low)

**Template:** Use the [Bug Report template](.github/ISSUE_TEMPLATE/bug_report.yml)

### Suggesting Features

Have an idea for a new feature?

**What makes a good feature request:**
- User story format: "As a [user], I want [goal], so that [benefit]"
- Clear problem statement explaining the pain point
- Concrete example showing how the feature would be used
- Acceptance criteria defining when the feature is "done"
- Priority level (Critical/High/Medium/Low)

**For improvements to existing features**, use the [Enhancement template](.github/ISSUE_TEMPLATE/enhancement.yml) instead.

**Template:** Use the [Feature Request template](.github/ISSUE_TEMPLATE/feature_request.yml)

### Issue Lifecycle

Issues go through several stages in our workflow:

1. **Triage** (`status: triage`) - New issue, needs review by maintainers
2. **Backlog** - Triaged and validated, not yet scheduled
3. **Planned** - Scheduled for development in upcoming sprint
4. **In Progress** (`status: in-progress`) - Actively being worked on
5. **Needs Review** (`status: needs-review`) - PR open, awaiting code review
6. **Done** - Issue closed, changes merged or issue resolved

See our [Issue Lifecycle Documentation](docs/issue-lifecycle.md) for detailed information.

### Service Level Agreements (SLAs)

We aim to meet these response times:

| Priority | Acknowledgement | Resolution Target |
|----------|----------------|-------------------|
| Critical | 4 hours | 24 hours |
| High | 1 day | 1 week |
| Medium | 3 days | 2 weeks |
| Low | Best effort | Best effort |

**Note:** These are targets, not guarantees. This is an open source project maintained by volunteers.

## Development Workflow

### Before Making Changes

1. Check existing [issues](https://github.com/mikelane/dioxide/issues) and [pull requests](https://github.com/mikelane/dioxide/pulls)
2. Create an issue if one doesn't exist (use the appropriate template)
3. Discuss your approach in the issue before starting work on large changes

### Making Changes

1. **Sync your fork with upstream** (if not already up to date):
   ```bash
   git checkout main
   git fetch upstream
   git merge upstream/main
   git push origin main
   ```

2. **Create a feature branch** in your fork:
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Write tests first** (TDD approach):
   - Add failing tests in `tests/`
   - Run `uv run pytest tests/` to confirm they fail
   - Implement the feature
   - Run `uv run pytest tests/` to confirm they pass

4. **Pre-commit hooks will automatically**:
   - Format Python code (ruff format)
   - Fix linting issues (ruff check --fix)
   - Sort imports (isort)
   - Check types (mypy --strict)
   - Format Rust code (cargo fmt)
   - Lint Rust code (cargo clippy)

5. **Run tests before pushing**:
   ```bash
   uv run pytest tests/ --cov=dioxide --cov-branch
   ```

6. **Run full quality checks** (optional, CI will run these):
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

### Pre-commit Hooks

Pre-commit hooks run automatically when you commit, catching issues before they reach CI.

**What hooks do**:
- ✅ Format Python code (ruff format)
- ✅ Auto-fix linting issues (ruff check --fix --unsafe-fixes)
- ✅ Sort imports (isort)
- ✅ Type check (mypy --strict)
- ✅ Format Rust code (cargo fmt)
- ✅ Lint Rust code (cargo clippy)
- ✅ Check YAML/TOML syntax
- ✅ Remove trailing whitespace

**Installation**:
```bash
pre-commit install
```

**Running manually**:
```bash
# Run all hooks on all files
pre-commit run --all-files

# Run specific hook
pre-commit run ruff --all-files

# Update hook versions
pre-commit autoupdate
```

**Bypassing hooks** (use sparingly):
```bash
# Skip hooks for WIP commits
git commit --no-verify -m "WIP: work in progress"
```

**Performance**:
- Hooks run in < 5 seconds for incremental commits
- First run may take longer (installing hook environments)

**Note on tests**:
Tests are NOT run in pre-commit hooks due to technical limitations with the Rust extension build.
Always run tests manually before pushing:
```bash
uv run pytest tests/ --cov=dioxide --cov-branch
```

### Pull Request Process

**ALL changes must go through PRs - no exceptions.**

#### For External Contributors (From Forks)

1. **Ensure issue exists** for the work (create one if needed)
2. **Update documentation** if needed (README, docstrings, etc.)
3. **Ensure all tests pass**:
   ```bash
   tox
   ```
4. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```
5. **Create a Pull Request** on GitHub from your fork to the main repository
6. **Fill out the PR template** with:
   - Description of changes
   - Related issue(s) - use "Fixes #N" or "Closes #N"
   - Testing performed
   - Checklist completion

#### For Maintainers (Direct Repository Access)

1. **Ensure issue exists** for the work (create one if needed - MANDATORY)
2. **Update documentation** if needed (README, docstrings, etc.)
3. **Ensure all tests pass**:
   ```bash
   tox
   ```
4. **Push to the main repository**:
   ```bash
   git push origin feature/your-feature-name
   ```
5. **Create a Pull Request** on GitHub - ALL changes require PR (for archaeology/documentation)
6. **Fill out the PR template** with:
   - Description of changes
   - Related issue(s) - use "Fixes #N" or "Closes #N"
   - Testing performed
   - Checklist completion
7. **Wait for CI checks** to pass before merging
8. **Merge directly** - No approval required for maintainer PRs (CODEOWNERS requirement doesn't apply to code owners)

### Review Requirements

**How code review works in dioxide:**

- **External contributor PRs**: Require approval from @mikelane (via CODEOWNERS)
- **Maintainer PRs**: No approval required (CODEOWNERS doesn't apply to code owners)
- **All PRs**: Must pass CI checks and conversation resolution

The repository uses `.github/CODEOWNERS` to automatically assign @mikelane as reviewer for all external contributions. This ensures code quality while allowing maintainers to merge their own PRs for efficient workflow.

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
