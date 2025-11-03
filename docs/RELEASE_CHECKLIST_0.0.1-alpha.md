# Release Checklist: dioxide 0.0.1-alpha

**Release Version**: 0.0.1-alpha
**Target Date**: TBD
**Release Manager**: @mikelane

---

## Pre-Release Phase

### Week 1: Core Bug Fixes

- [x] **Issue #19: Fix Singleton Caching Bug** (COMPLETE)
  - [x] Fix applied to `rust/src/lib.rs` (commit b7b2e4d)
  - [x] All 4 failing tests now pass
  - [x] No regression in other tests
  - [x] Code review approved
  - [x] QA validation passed
  - [x] PR merged to main
  - [x] CI passes on main

**Gate**: ✅ COMPLETE - Issue #19 resolved Oct 26, 2025

---

### Week 2: Feature Completion

- [x] **Issue #20: Manual Provider Registration** (COMPLETE)
  - [x] `register_singleton()` implemented
  - [x] `register_factory()` implemented
  - [x] Comprehensive tests written
  - [x] All scenarios in `features/manual-registration.feature` pass
  - [x] Code review approved
  - [x] QA validation passed
  - [x] PR merged to main (commit 73e4d09)

- [x] **Issue #21: Type Safety Testing** (COMPLETE)
  - [x] Type stubs updated in `_dioxide_core.pyi`
  - [x] Python API has proper type hints
  - [x] Type-checking tests written
  - [x] mypy strict mode passes
  - [x] All scenarios in `features/type-safety.feature` pass
  - [x] Code review approved
  - [x] QA validation passed
  - [x] PR merged to main (commit 08bae41)

**Gate**: ✅ COMPLETE - All BDD scenarios passing

---

### Week 2-3: Infrastructure

- [~] **Issue #22: GitHub Actions CI Workflow** (IN PROGRESS)
  - [x] `.github/workflows/ci.yml` created
  - [x] CI runs on push to main
  - [x] CI runs on pull requests
  - [~] Test matrix runs (Python 3.11, 3.12, 3.13) - needs fixes
  - [~] Lint jobs pass (Python + Rust) - needs fixes
  - [ ] Coverage uploads to Codecov
  - [x] Status badges added to README
  - [ ] Branch protection enabled
  - [~] PR merged after CI passes on PR itself

- [ ] **Issue #23: GitHub Actions Release Workflow** (TODO)
  - [ ] `.github/workflows/release.yml` created
  - [ ] PyPI accounts created (Test + Production)
  - [ ] API tokens added to GitHub Secrets
  - [ ] Workflow tested with test tag
  - [ ] Wheels build for all platforms
  - [ ] Tests pass before publishing
  - [ ] Package published to Test PyPI (test run)
  - [ ] GitHub Release created (test run)
  - [ ] PR merged to main

- [ ] **Issue #24: API Documentation** (TODO)
  - [ ] All public API has docstrings
  - [ ] Examples tested and working
  - [ ] IDE autocomplete shows docs
  - [ ] Code review approved
  - [ ] PR merged to main

**Gate**: CI and Release workflows must be operational.

---

## Quality Verification

### Test Coverage

- [x] Run full test suite: `uv run pytest tests/ -v`
  - [x] All tests pass (29/32 passing, 3 skipped)
  - [x] Skipped tests are circular dependency detection (out of scope)
  - [x] No xfail tests

- [x] Check coverage: `uv run pytest tests/ --cov=dioxide --cov-branch --cov-report=term-missing`
  - [x] Line coverage: 100%
  - [x] Branch coverage: 100%
  - [x] No missing lines

### Code Quality

- [ ] Ruff formatting: `uv run ruff format python/`
  - [ ] No files reformatted

- [ ] Ruff linting: `uv run ruff check python/`
  - [ ] No warnings
  - [ ] No errors

- [ ] Import sorting: `uv run isort python/ --check-only`
  - [ ] All imports sorted

- [ ] Type checking: `uv run mypy python/`
  - [ ] No type errors
  - [ ] Strict mode enabled

- [ ] Rust formatting: `cargo fmt --all --check`
  - [ ] No files need formatting

- [ ] Rust linting: `cargo clippy --all-targets --all-features`
  - [ ] No warnings
  - [ ] No errors

### BDD Scenarios

Verify all scenarios pass for each feature file:

- [x] `features/component-decorator.feature` (5 scenarios)
- [x] `features/container-scan.feature` (5 scenarios)
- [x] `features/dependency-injection.feature` (5 scenarios)
- [x] `features/singleton-caching.feature` (5 scenarios)
- [x] `features/manual-registration.feature` (4 scenarios)
- [x] `features/type-safety.feature` (5 scenarios)

**Total**: 29 scenarios, all passing ✅

### CI Pipeline

- [ ] Push to main triggers CI
- [ ] All CI jobs pass:
  - [ ] Test matrix (6 jobs)
  - [ ] Lint Python
  - [ ] Lint Rust
- [ ] Coverage uploaded to Codecov
- [ ] Status badges green in README

---

## Documentation Review

### Core Documentation

- [ ] `README.md`
  - [ ] Status reflects alpha release
  - [ ] Installation instructions correct
  - [ ] Quick start example works
  - [ ] Links are valid
  - [ ] Status badges display correctly

- [ ] `CHANGELOG.md`
  - [ ] Created with Keep a Changelog format
  - [ ] Version 0.0.1-alpha documented
  - [ ] Release date added
  - [ ] All features listed
  - [ ] Bug fixes listed
  - [ ] Infrastructure changes listed

- [ ] `CLAUDE.md`
  - [ ] Accurate and up-to-date
  - [ ] Reflects current architecture
  - [ ] Recent development history updated

- [ ] `COVERAGE.md`
  - [ ] Reflects 100% coverage achievement
  - [ ] Instructions tested and working

### Design Documentation

- [ ] `docs/0.0.1-ALPHA_SCOPE.md`
  - [ ] Scope accurately reflects what shipped
  - [ ] All acceptance criteria marked complete
  - [ ] Risks updated with actuals

- [ ] `docs/design/singleton-caching-fix.md`
  - [ ] Reflects actual implementation
  - [ ] Testing results documented

- [ ] `docs/design/github-actions-ci.md`
  - [ ] Workflow matches actual `.github/workflows/ci.yml`
  - [ ] Performance metrics added

- [ ] `docs/design/github-actions-release.md`
  - [ ] Workflow matches actual `.github/workflows/release.yml`
  - [ ] Release process tested

### API Documentation

- [ ] All public classes have docstrings
- [ ] All public methods have docstrings
- [ ] Examples in docstrings are executable
- [ ] `help(Container)` shows useful information
- [ ] IDE autocomplete displays documentation

---

## Release Preparation

### Version Update

- [ ] Update `pyproject.toml`:
  ```toml
  [project]
  name = "dioxide"
  version = "0.0.1a0"  # Alpha version
  ```

- [ ] Update `Cargo.toml`:
  ```toml
  [package]
  name = "dioxide-core"
  version = "0.0.1-alpha"
  ```

### CHANGELOG Finalization

- [ ] Open `CHANGELOG.md`
- [ ] Set release date for `[0.0.1-alpha]`
- [ ] Move any `[Unreleased]` items to `[0.0.1-alpha]`
- [ ] Verify all changes documented
- [ ] Commit: `git commit -m "docs: finalize changelog for 0.0.1-alpha"`

### Final Checks

- [~] All GitHub Issues closed:
  - [x] #19 (Singleton Caching Bug) ✅
  - [x] #20 (Manual Provider Registration) ✅
  - [x] #21 (Type Safety Testing) ✅
  - [~] #22 (GitHub Actions CI) - IN PROGRESS
  - [ ] #23 (GitHub Actions Release) - TODO
  - [ ] #24 (API Documentation) - TODO

- [x] All PRs merged to main
- [~] CI passing on main branch - needs fixes
- [x] No uncommitted changes in tracked files
- [ ] No untracked files (except local config)

---

## Release Execution

### Step 1: Final Smoke Test

```bash
# Fresh environment
rm -rf .venv
uv venv
source .venv/bin/activate

# Install and test
uv sync --all-extras --all-groups
uv run maturin develop
uv run pytest tests/ -v

# All tests should pass
```

### Step 2: Create Release Tag

```bash
# Ensure on main branch
git checkout main
git pull origin main

# Create annotated tag
git tag -a v0.0.1-alpha -m "Release 0.0.1-alpha

First alpha release of dioxide dependency injection framework.

Features:
- @component decorator for DI auto-discovery
- Container.scan() for automatic registration
- Constructor dependency injection
- SINGLETON and FACTORY scopes
- Manual provider registration
- Type-safe resolve() with mypy support

Infrastructure:
- GitHub Actions CI/CD pipeline
- Automated PyPI releases
- 100% test coverage

For details, see CHANGELOG.md
"

# Push tag (triggers release workflow)
git push origin v0.0.1-alpha
```

### Step 3: Monitor Release Workflow

- [ ] Go to https://github.com/mikelane/dioxide/actions
- [ ] Find "Release" workflow run for tag `v0.0.1-alpha`
- [ ] Monitor job progress:
  - [ ] Build wheels (9 jobs)
  - [ ] Test wheels (3 jobs)
  - [ ] Publish to Test PyPI
  - [ ] Create GitHub Release

- [ ] All jobs pass (green checkmarks)
- [ ] No failed jobs

### Step 4: Verify Test PyPI

- [ ] Visit https://test.pypi.org/project/dioxide/
- [ ] Verify package appears
- [ ] Check version: `0.0.1a0`
- [ ] Verify metadata:
  - [ ] Description correct
  - [ ] Links working
  - [ ] Python versions: 3.11, 3.12, 3.13
  - [ ] Wheels for Linux, macOS, Windows

### Step 5: Verify GitHub Release

- [ ] Visit https://github.com/mikelane/dioxide/releases
- [ ] Find "v0.0.1-alpha" release
- [ ] Verify:
  - [ ] Marked as "Pre-release"
  - [ ] Changelog included
  - [ ] All wheel artifacts attached (9 files)
  - [ ] Source code archives (zip + tar.gz)

### Step 6: Test Installation

```bash
# Create fresh environment
python -m venv test_install
source test_install/bin/activate

# Install from Test PyPI
pip install -i https://test.pypi.org/simple/ dioxide==0.0.1a0

# Verify installation
python -c "from dioxide import Container, component, Scope; print('Success!')"

# Run quick test
python << EOF
from dioxide import Container, component

@component
class TestService:
    pass

container = Container()
container.scan()
service = container.resolve(TestService)
print(f"Service created: {service}")
assert isinstance(service, TestService)
print("All checks passed!")
EOF
```

- [ ] Package installs successfully
- [ ] Imports work
- [ ] Basic functionality works

---

## Post-Release

### Announcement

- [ ] Create GitHub Discussion:
  - Title: "dioxide 0.0.1-alpha Released!"
  - Category: Announcements
  - Content:
    ```markdown
    # dioxide 0.0.1-alpha Released! 🎉

    I'm excited to announce the first alpha release of dioxide, a fast, Rust-backed
    dependency injection framework for Python!

    ## What's in this release:

    - ✅ @component decorator for DI auto-discovery
    - ✅ Constructor dependency injection
    - ✅ SINGLETON and FACTORY scopes
    - ✅ Manual provider registration
    - ✅ Type-safe with full mypy support
    - ✅ 100% test coverage
    - ✅ Automated CI/CD pipeline

    ## Try it out:

    ```bash
    pip install -i https://test.pypi.org/simple/ dioxide==0.0.1a0
    ```

    ## Feedback:

    This is an alpha release - please report any issues you encounter!

    Full changelog: https://github.com/mikelane/dioxide/blob/main/CHANGELOG.md
    ```

- [ ] Update README badges:
  - [ ] CI badge should be green
  - [ ] Coverage badge should show 100%

### Cleanup

- [ ] Close 0.0.1-alpha milestone
- [ ] Create 0.0.2-alpha milestone (if needed)
- [ ] Archive release branch (if created)
- [ ] Update project board

---

## Retrospective

Schedule team retrospective to discuss:

### What Went Well?
- [ ] Document successes
- [ ] Capture what to repeat

### What Didn't Go Well?
- [ ] Document challenges
- [ ] Capture what to avoid

### What Did We Learn?
- [ ] Document insights
- [ ] Update processes

### Action Items for Next Release?
- [ ] Create issues for improvements
- [ ] Update workflows based on learnings

---

## Checklist Summary

**Pre-Release**: 6 issues completed
**Quality**: All tests pass, 100% coverage
**Documentation**: Complete and accurate
**Release**: Tag pushed, workflow succeeded
**Verification**: Package works on Test PyPI
**Post-Release**: Announced and documented

---

**Release Status**: ⏳ In Progress (67% complete - 4 of 6 issues done)

**Last Updated**: 2025-11-02
