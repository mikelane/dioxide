# Design Doc: GitHub Actions CI Workflow

**Status**: Draft
**Author**: Product & Technical Lead
**Date**: 2025-01-26
**Related Issue**: #4
**Assignee**: @sre-platform

---

## Problem Statement

dioxide currently has **no automated CI pipeline**. This creates several problems:

1. **No automated testing** - Tests only run locally before commits
2. **No cross-platform verification** - macOS, Linux, Windows builds not tested
3. **No Python version matrix** - Only tested on developer's Python version
4. **No pre-merge quality gates** - PRs can break main branch
5. **Manual quality checks** - Linting, type checking, coverage are manual

**Goal**: Implement a robust CI pipeline that runs on every push and PR, ensuring code quality before merge.

---

## Requirements

### Functional Requirements

**FR1**: Run full test suite on every push to main and every PR
**FR2**: Test on Python 3.11, 3.12, 3.13
**FR3**: Test on macOS, Linux, and Windows (if feasible)
**FR4**: Run all quality checks (ruff, mypy, clippy)
**FR5**: Measure and report code coverage
**FR6**: Fail the build if tests fail or coverage drops below threshold
**FR7**: Run pre-commit hooks in CI
**FR8**: Cache dependencies for faster builds

### Non-Functional Requirements

**NFR1**: CI run should complete in under 10 minutes
**NFR2**: Clear, actionable error messages on failure
**NFR3**: Coverage reports uploaded to Codecov (or similar)
**NFR4**: Status badges in README
**NFR5**: Cost-effective (use GitHub Actions free tier)

---

## Proposed Solution

### GitHub Actions Workflow

**File**: `.github/workflows/ci.yml`

**Triggers**:
- Push to `main` branch
- Pull request opened/updated/reopened
- Manual workflow dispatch (for debugging)

**Strategy**: Matrix build across Python versions

```yaml
strategy:
  matrix:
    python-version: ['3.11', '3.12', '3.13']
    os: [ubuntu-latest, macos-latest]  # Windows optional for v2
```

---

## Workflow Design

### Job 1: Test Matrix

**Purpose**: Run tests across Python versions and OS

**Steps**:

1. **Checkout code**
   ```yaml
   - uses: actions/checkout@v4
   ```

2. **Setup Rust toolchain**
   ```yaml
   - uses: dtolnay/rust-toolchain@stable
   ```

3. **Cache Rust dependencies**
   ```yaml
   - uses: Swatinem/rust-cache@v2
     with:
       workspaces: rust
   ```

4. **Setup Python with uv**
   ```yaml
   - uses: actions/setup-python@v5
     with:
       python-version: ${{ matrix.python-version }}

   - name: Install uv
     run: curl -LsSf https://astral.sh/uv/install.sh | sh

   - name: Add uv to PATH
     run: echo "$HOME/.cargo/bin" >> $GITHUB_PATH
   ```

5. **Install Python dependencies**
   ```yaml
   - name: Install dependencies
     run: |
       uv venv
       source .venv/bin/activate
       uv sync --all-extras --all-groups
   ```

6. **Build Rust extension**
   ```yaml
   - name: Build Rust extension
     run: |
       source .venv/bin/activate
       uv run maturin develop
   ```

7. **Run tests with coverage**
   ```yaml
   - name: Run tests
     run: |
       source .venv/bin/activate
       uv run pytest tests/ \
         --cov=dioxide \
         --cov-report=xml \
         --cov-report=term-missing \
         --cov-branch \
         --cov-fail-under=95
   ```

8. **Upload coverage to Codecov**
   ```yaml
   - name: Upload coverage
     uses: codecov/codecov-action@v4
     with:
       file: ./coverage.xml
       flags: python-${{ matrix.python-version }}
       name: dioxide-${{ matrix.python-version }}
   ```

---

### Job 2: Lint and Type Check

**Purpose**: Ensure code quality and type safety

**Steps**:

1. **Checkout code**

2. **Setup Python (latest)**
   ```yaml
   - uses: actions/setup-python@v5
     with:
       python-version: '3.13'  # Use latest for linting
   ```

3. **Install uv and dependencies**

4. **Run Ruff format check**
   ```yaml
   - name: Check formatting
     run: uv run ruff format --check python/
   ```

5. **Run Ruff lint**
   ```yaml
   - name: Lint Python
     run: uv run ruff check python/
   ```

6. **Run isort check**
   ```yaml
   - name: Check imports
     run: uv run isort python/ --check-only
   ```

7. **Run mypy**
   ```yaml
   - name: Type check
     run: uv run mypy python/
   ```

---

### Job 3: Rust Lint

**Purpose**: Ensure Rust code quality

**Steps**:

1. **Checkout code**

2. **Setup Rust toolchain**
   ```yaml
   - uses: dtolnay/rust-toolchain@stable
     with:
       components: rustfmt, clippy
   ```

3. **Cache Rust dependencies**

4. **Run cargo fmt check**
   ```yaml
   - name: Check Rust formatting
     run: cargo fmt --all --check
     working-directory: rust
   ```

5. **Run cargo clippy**
   ```yaml
   - name: Lint Rust
     run: |
       cargo clippy --all-targets --all-features \
         -- -D warnings -A non-local-definitions
     working-directory: rust
   ```

---

### Job 4: Pre-commit Hooks

**Purpose**: Run all pre-commit hooks in CI

**Steps**:

1. **Checkout code**

2. **Setup Python**

3. **Setup Rust**

4. **Install pre-commit**
   ```yaml
   - name: Install pre-commit
     run: pip install pre-commit
   ```

5. **Run pre-commit**
   ```yaml
   - name: Run pre-commit hooks
     run: pre-commit run --all-files
   ```

---

## Complete Workflow File

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
  workflow_dispatch:

jobs:
  test:
    name: Test Python ${{ matrix.python-version }} on ${{ matrix.os }}
    runs-on: ${{ matrix.os }}
    strategy:
      fail-fast: false
      matrix:
        python-version: ['3.11', '3.12', '3.13']
        os: [ubuntu-latest, macos-latest]

    steps:
      - uses: actions/checkout@v4

      - name: Setup Rust
        uses: dtolnay/rust-toolchain@stable

      - name: Cache Rust dependencies
        uses: Swatinem/rust-cache@v2
        with:
          workspaces: rust

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install uv
        run: curl -LsSf https://astral.sh/uv/install.sh | sh

      - name: Add uv to PATH
        run: echo "$HOME/.cargo/bin" >> $GITHUB_PATH

      - name: Install dependencies
        run: |
          uv venv
          source .venv/bin/activate
          uv sync --all-extras --all-groups

      - name: Build Rust extension
        run: |
          source .venv/bin/activate
          uv run maturin develop

      - name: Run tests with coverage
        run: |
          source .venv/bin/activate
          uv run pytest tests/ \
            --cov=dioxide \
            --cov-report=xml \
            --cov-report=term-missing \
            --cov-branch \
            --cov-fail-under=95 \
            -v

      - name: Upload coverage
        uses: codecov/codecov-action@v4
        if: matrix.os == 'ubuntu-latest' && matrix.python-version == '3.13'
        with:
          file: ./coverage.xml
          flags: python-${{ matrix.python-version }}
          name: dioxide
        env:
          CODECOV_TOKEN: ${{ secrets.CODECOV_TOKEN }}

  lint-python:
    name: Lint Python
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.13'

      - name: Install uv
        run: curl -LsSf https://astral.sh/uv/install.sh | sh

      - name: Add uv to PATH
        run: echo "$HOME/.cargo/bin" >> $GITHUB_PATH

      - name: Install dependencies
        run: |
          uv venv
          source .venv/bin/activate
          uv sync --all-extras --all-groups

      - name: Check formatting
        run: |
          source .venv/bin/activate
          uv run ruff format --check python/

      - name: Lint
        run: |
          source .venv/bin/activate
          uv run ruff check python/

      - name: Check imports
        run: |
          source .venv/bin/activate
          uv run isort python/ --check-only

      - name: Type check
        run: |
          source .venv/bin/activate
          uv run mypy python/

  lint-rust:
    name: Lint Rust
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Setup Rust
        uses: dtolnay/rust-toolchain@stable
        with:
          components: rustfmt, clippy

      - name: Cache Rust dependencies
        uses: Swatinem/rust-cache@v2
        with:
          workspaces: rust

      - name: Check formatting
        run: cargo fmt --all --check
        working-directory: rust

      - name: Lint
        run: cargo clippy --all-targets --all-features -- -D warnings -A non-local-definitions
        working-directory: rust
```

---

## Implementation Plan

### Phase 1: Create Workflow File
1. Create `.github/workflows/` directory
2. Create `ci.yml` with test job only
3. Test on a feature branch
4. Verify tests run successfully

### Phase 2: Add Linting Jobs
1. Add `lint-python` job
2. Add `lint-rust` job
3. Test on feature branch
4. Verify linters run

### Phase 3: Add Coverage
1. Sign up for Codecov account
2. Add `CODECOV_TOKEN` to GitHub Secrets
3. Add coverage upload step
4. Verify coverage reports

### Phase 4: Add Status Badges
1. Add badges to README.md:
   ```markdown
   [![CI](https://github.com/mikelane/dioxide/workflows/CI/badge.svg)](https://github.com/mikelane/dioxide/actions)
   [![codecov](https://codecov.io/gh/mikelane/dioxide/branch/main/graph/badge.svg)](https://codecov.io/gh/mikelane/dioxide)
   ```

### Phase 5: Test and Refine
1. Run workflow on multiple PRs
2. Measure build times
3. Optimize caching if needed
4. Document any common issues

---

## Testing Strategy

### Pre-Deployment Testing
1. Create feature branch: `ci/github-actions-workflow`
2. Commit workflow file
3. Push and verify CI runs
4. Intentionally break a test to verify failure detection
5. Fix and verify success

### Post-Deployment Verification
1. Merge to main
2. Verify CI runs on main branch
3. Create test PR to verify PR checks
4. Verify status checks appear in PR
5. Verify coverage reports upload

---

## Success Criteria

✅ CI runs on every push to main
✅ CI runs on every PR
✅ Tests execute on Python 3.11, 3.12, 3.13
✅ Tests execute on Ubuntu and macOS
✅ All linting and type checking jobs pass
✅ Coverage reports upload to Codecov
✅ Build completes in under 10 minutes
✅ Status badges display in README
✅ Failed tests block PR merge (via branch protection)

---

## Risks and Mitigation

### Risk 1: Build Time Exceeds 10 Minutes

**Mitigation**:
- Use aggressive caching (Rust dependencies, Python packages)
- Use maturin's release mode selectively (dev mode faster)
- Consider reducing OS matrix (macOS only if needed)

**Contingency**: Reduce matrix to Ubuntu + Python 3.13 only for draft PRs

### Risk 2: Windows Build Failures

**Mitigation**:
- Start with Ubuntu + macOS only
- Add Windows in v2 after core CI is stable
- Use `setup-python` action's Windows support

**Contingency**: Mark Windows as experimental, allow failures

### Risk 3: uv Installation Issues

**Mitigation**:
- Pin uv version if needed
- Test on clean GitHub Actions environment
- Have fallback to pip if uv fails

**Contingency**: Use traditional pip/venv if uv proves unreliable in CI

---

## Future Enhancements

### Post 0.0.1-alpha

1. **Windows Support**
   - Add `windows-latest` to matrix
   - Test Windows-specific issues

2. **Coverage Trends**
   - Track coverage over time
   - Alert on coverage drops

3. **Performance Benchmarks**
   - Add benchmark job
   - Track performance regressions

4. **Mutation Testing**
   - Run mutmut in CI (expensive, optional)
   - Only on main branch, not PRs

5. **Dependency Scanning**
   - Use Dependabot for automatic updates
   - Snyk or similar for vulnerability scanning

---

## Cost Analysis

**GitHub Actions Free Tier**:
- 2,000 minutes/month for public repos
- macOS minutes count as 10x (200 effective minutes)
- Ubuntu minutes count as 1x

**Estimated Usage**:
- Test job: 6 runs (3 Python × 2 OS) × 5 minutes = 30 minutes per workflow
- Lint jobs: 2 runs × 2 minutes = 4 minutes per workflow
- **Total**: ~34 minutes per workflow run

**With**:
- 10 PRs/week = 10 runs
- 20 commits to main/week = 20 runs
- **Monthly**: 30 runs × 34 minutes = 1,020 minutes

**Breakdown**:
- Ubuntu: 24 minutes × 30 runs = 720 minutes
- macOS: 10 minutes × 30 runs × 10 = 3,000 effective minutes

**Conclusion**: Exceeds free tier if all jobs run on macOS. **Solution**: Run only Ubuntu in PR checks, add macOS for main branch only.

---

## References

- **Issue**: #4 (GitHub Actions CI Workflow)
- **GitHub Actions Docs**: https://docs.github.com/en/actions
- **uv Docs**: https://github.com/astral-sh/uv
- **maturin Action**: https://github.com/PyO3/maturin-action
- **Codecov Action**: https://github.com/codecov/codecov-action

---

## Approval

**Product Lead**: Approved
**SRE/Platform**: Assigned
**Target Completion**: Week 2 of 0.0.1-alpha

---

*This design doc will be updated as implementation progresses.*
