# Design Doc: GitHub Actions Release Workflow

**Status**: Draft
**Author**: Product & Technical Lead
**Date**: 2025-01-26
**Related Issue**: #5
**Assignee**: @sre-platform

---

## Problem Statement

dioxide currently has **no automated release process**. To publish a new version, a developer must:

1. Manually build wheels for multiple platforms
2. Manually run tests
3. Manually tag the release
4. Manually publish to PyPI
5. Manually create GitHub Release
6. Manually write release notes

**Problems**:
- Error-prone and time-consuming
- No guarantee of reproducible builds
- Easy to forget steps (like testing before publishing)
- Cross-platform builds require multiple machines
- Release notes often incomplete or missing

**Goal**: Automate the entire release process from git tag to PyPI publish and GitHub Release.

---

## Requirements

### Functional Requirements

**FR1**: Trigger on git tag push matching pattern `v*.*.*`
**FR2**: Build wheels for multiple Python versions (3.11, 3.12, 3.13)
**FR3**: Build wheels for multiple platforms (Linux, macOS, Windows)
**FR4**: Run full test suite before publishing
**FR5**: Publish to PyPI automatically (Test PyPI for alpha)
**FR6**: Create GitHub Release with changelog
**FR7**: Upload build artifacts to GitHub Release
**FR8**: Fail if any tests fail

### Non-Functional Requirements

**NFR1**: Release process completes in under 30 minutes
**NFR2**: Clear error messages if release fails
**NFR3**: Idempotent (can re-run without side effects)
**NFR4**: Secure (PyPI token in GitHub Secrets)
**NFR5**: Audit trail (all steps logged)

---

## Proposed Solution

### GitHub Actions Workflow

**File**: `.github/workflows/release.yml`

**Triggers**:
- Git tag push matching `v*.*.*` (e.g., `v0.0.1-alpha`, `v0.1.0`, `v1.0.0`)

**Strategy**: Multi-platform matrix build using maturin

---

## Workflow Design

### Job 1: Build Wheels

**Purpose**: Build platform-specific wheels using maturin

**Matrix**:
```yaml
strategy:
  matrix:
    os: [ubuntu-latest, macos-latest, windows-latest]
    python-version: ['3.11', '3.12', '3.13']
```

**Steps**:

1. **Checkout code**
   ```yaml
   - uses: actions/checkout@v4
   ```

2. **Setup Python**
   ```yaml
   - uses: actions/setup-python@v5
     with:
       python-version: ${{ matrix.python-version }}
   ```

3. **Setup Rust**
   ```yaml
   - uses: dtolnay/rust-toolchain@stable
   ```

4. **Build wheels with maturin**
   ```yaml
   - uses: PyO3/maturin-action@v1
     with:
       command: build
       args: --release --out dist --interpreter python${{ matrix.python-version }}
   ```

5. **Upload wheel artifacts**
   ```yaml
   - uses: actions/upload-artifact@v4
     with:
       name: wheels-${{ matrix.os }}-${{ matrix.python-version }}
       path: dist/*.whl
   ```

---

### Job 2: Test Wheels

**Purpose**: Verify wheels can be installed and tests pass

**Depends-On**: build

**Steps**:

1. **Download wheel artifacts**
   ```yaml
   - uses: actions/download-artifact@v4
     with:
       pattern: wheels-*
       path: dist
       merge-multiple: true
   ```

2. **Setup Python**

3. **Install wheel**
   ```yaml
   - name: Install wheel
     run: pip install dist/dioxide-*.whl
   ```

4. **Install test dependencies**
   ```yaml
   - name: Install test dependencies
     run: pip install pytest pytest-cov
   ```

5. **Run tests**
   ```yaml
   - name: Run tests
     run: pytest tests/ -v
   ```

---

### Job 3: Publish to PyPI

**Purpose**: Publish wheels to PyPI (or Test PyPI for alpha)

**Depends-On**: test-wheels

**Steps**:

1. **Download all wheel artifacts**

2. **Setup Python**

3. **Install twine**
   ```yaml
   - name: Install twine
     run: pip install twine
   ```

4. **Publish to Test PyPI (for alpha)**
   ```yaml
   - name: Publish to Test PyPI
     if: contains(github.ref, 'alpha') || contains(github.ref, 'beta')
     env:
       TWINE_USERNAME: __token__
       TWINE_PASSWORD: ${{ secrets.TEST_PYPI_TOKEN }}
     run: |
       twine upload --repository testpypi dist/*.whl
   ```

5. **Publish to PyPI (for stable)**
   ```yaml
   - name: Publish to PyPI
     if: "!contains(github.ref, 'alpha') && !contains(github.ref, 'beta')"
     env:
       TWINE_USERNAME: __token__
       TWINE_PASSWORD: ${{ secrets.PYPI_TOKEN }}
     run: |
       twine upload dist/*.whl
   ```

---

### Job 4: Create GitHub Release

**Purpose**: Create GitHub Release with changelog and artifacts

**Depends-On**: publish

**Steps**:

1. **Download all wheel artifacts**

2. **Extract version from tag**
   ```yaml
   - name: Get version
     id: get_version
     run: echo "VERSION=${GITHUB_REF#refs/tags/v}" >> $GITHUB_OUTPUT
   ```

3. **Generate changelog**
   ```yaml
   - name: Generate changelog
     id: changelog
     run: |
       # Extract changelog for this version from CHANGELOG.md
       VERSION=${{ steps.get_version.outputs.VERSION }}
       sed -n "/## \[$VERSION\]/,/## \[/p" CHANGELOG.md | head -n -1 > release_notes.md
   ```

4. **Create GitHub Release**
   ```yaml
   - name: Create Release
     uses: softprops/action-gh-release@v1
     with:
       body_path: release_notes.md
       files: dist/*.whl
       draft: false
       prerelease: ${{ contains(github.ref, 'alpha') || contains(github.ref, 'beta') }}
     env:
       GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
   ```

---

## Complete Workflow File

```yaml
name: Release

on:
  push:
    tags:
      - 'v*.*.*'

jobs:
  build:
    name: Build wheels on ${{ matrix.os }}
    runs-on: ${{ matrix.os }}
    strategy:
      fail-fast: false
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]
        python-version: ['3.11', '3.12', '3.13']

    steps:
      - uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}

      - name: Setup Rust
        uses: dtolnay/rust-toolchain@stable

      - name: Build wheels
        uses: PyO3/maturin-action@v1
        with:
          command: build
          args: --release --out dist --interpreter python${{ matrix.python-version }}

      - name: Upload wheels
        uses: actions/upload-artifact@v4
        with:
          name: wheels-${{ matrix.os }}-py${{ matrix.python-version }}
          path: dist/*.whl

  test-wheels:
    name: Test wheels on ${{ matrix.os }}
    needs: build
    runs-on: ${{ matrix.os }}
    strategy:
      fail-fast: true
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]
        python-version: ['3.13']  # Test on latest Python only

    steps:
      - uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}

      - name: Download wheels
        uses: actions/download-artifact@v4
        with:
          pattern: wheels-${{ matrix.os }}-*
          path: dist
          merge-multiple: true

      - name: Install wheel
        shell: bash
        run: |
          pip install dist/dioxide-*.whl

      - name: Install test dependencies
        run: pip install pytest pytest-cov

      - name: Run tests
        run: pytest tests/ -v

  publish:
    name: Publish to PyPI
    needs: test-wheels
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Download all wheels
        uses: actions/download-artifact@v4
        with:
          pattern: wheels-*
          path: dist
          merge-multiple: true

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.13'

      - name: Install twine
        run: pip install twine

      - name: Publish to Test PyPI (alpha/beta)
        if: contains(github.ref, 'alpha') || contains(github.ref, 'beta')
        env:
          TWINE_USERNAME: __token__
          TWINE_PASSWORD: ${{ secrets.TEST_PYPI_TOKEN }}
        run: |
          twine upload --repository testpypi dist/*.whl

      - name: Publish to PyPI (stable)
        if: "!contains(github.ref, 'alpha') && !contains(github.ref, 'beta')"
        env:
          TWINE_USERNAME: __token__
          TWINE_PASSWORD: ${{ secrets.PYPI_TOKEN }}
        run: |
          twine upload dist/*.whl

  release:
    name: Create GitHub Release
    needs: publish
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Download all wheels
        uses: actions/download-artifact@v4
        with:
          pattern: wheels-*
          path: dist
          merge-multiple: true

      - name: Get version
        id: get_version
        run: echo "VERSION=${GITHUB_REF#refs/tags/v}" >> $GITHUB_OUTPUT

      - name: Extract changelog
        run: |
          VERSION=${{ steps.get_version.outputs.VERSION }}
          # Extract section for this version from CHANGELOG.md
          if [ -f CHANGELOG.md ]; then
            sed -n "/## \[$VERSION\]/,/## \[/p" CHANGELOG.md | head -n -1 > release_notes.md
          else
            echo "Release $VERSION" > release_notes.md
          fi

      - name: Create GitHub Release
        uses: softprops/action-gh-release@v1
        with:
          body_path: release_notes.md
          files: dist/*.whl
          draft: false
          prerelease: ${{ contains(github.ref, 'alpha') || contains(github.ref, 'beta') }}
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

---

## Implementation Plan

### Phase 1: Setup PyPI Accounts

1. **Create Test PyPI account**
   - Sign up at https://test.pypi.org
   - Generate API token
   - Add to GitHub Secrets as `TEST_PYPI_TOKEN`

2. **Create PyPI account** (for stable releases)
   - Sign up at https://pypi.org
   - Generate API token
   - Add to GitHub Secrets as `PYPI_TOKEN`

### Phase 2: Create Workflow File

1. Create `.github/workflows/release.yml`
2. Start with build job only
3. Test with a test tag: `v0.0.1-alpha-test`
4. Verify wheels build successfully

### Phase 3: Add Testing and Publishing

1. Add test-wheels job
2. Add publish job (Test PyPI only)
3. Test with `v0.0.1-alpha`
4. Verify package appears on Test PyPI

### Phase 4: Add GitHub Release

1. Add release job
2. Create CHANGELOG.md
3. Test full workflow
4. Verify GitHub Release created

### Phase 5: Test Installation

1. Create fresh virtual environment
2. Install from Test PyPI:
   ```bash
   pip install -i https://test.pypi.org/simple/ dioxide
   ```
3. Verify package works

---

## CHANGELOG.md Format

Create `CHANGELOG.md` in project root:

```markdown
# Changelog

All notable changes to dioxide will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.0.1-alpha] - 2025-01-26

### Added
- Initial alpha release
- @component decorator for DI auto-discovery
- Container.scan() for automatic registration
- Constructor dependency injection
- SINGLETON and FACTORY scopes
- Manual provider registration
- Type-safe resolve() with mypy support

### Fixed
- Singleton caching bug in Rust container

### Infrastructure
- GitHub Actions CI/CD pipeline
- Automated PyPI releases
- 100% test coverage
```

---

## Release Process

### For 0.0.1-alpha

```bash
# 1. Ensure all tests pass
uv run pytest tests/ -v

# 2. Update CHANGELOG.md with release date
# 3. Commit changelog
git add CHANGELOG.md
git commit -m "docs: update changelog for 0.0.1-alpha"

# 4. Create and push tag
git tag -a v0.0.1-alpha -m "Release 0.0.1-alpha"
git push origin v0.0.1-alpha

# 5. Monitor GitHub Actions
# - Check https://github.com/mikelane/dioxide/actions
# - Verify all jobs pass
# - Verify package on Test PyPI
# - Verify GitHub Release created

# 6. Test installation
pip install -i https://test.pypi.org/simple/ dioxide

# 7. Announce
# - Post in GitHub Discussions
# - Update README if needed
```

---

## Success Criteria

✅ Workflow triggers on tag push
✅ Wheels build for all platforms and Python versions
✅ Tests pass before publishing
✅ Package published to Test PyPI (for alpha)
✅ GitHub Release created with changelog
✅ Wheels attached to GitHub Release
✅ Package installs successfully from PyPI
✅ Full process completes in under 30 minutes

---

## Risks and Mitigation

### Risk 1: Cross-Platform Build Failures

**Mitigation**:
- Test builds locally on each platform first
- Use maturin-action (battle-tested)
- Start with Linux + macOS, add Windows later

**Contingency**: Mark Windows builds as experimental, allow failures

### Risk 2: PyPI Token Exposure

**Mitigation**:
- Use GitHub Secrets (encrypted at rest)
- Use API tokens (scoped permissions)
- Token only valid for dioxide package

**Contingency**: Revoke and regenerate token if exposed

### Risk 3: Failed Release Mid-Process

**Mitigation**:
- Jobs depend on previous success
- Use Test PyPI for alpha testing
- Can delete and re-tag if needed

**Contingency**: Manual cleanup of failed release, retag with -rc2 suffix

---

## Future Enhancements

### Post 0.0.1-alpha

1. **Source Distribution (sdist)**
   - Build sdist in addition to wheels
   - Useful for platforms without pre-built wheels

2. **Digital Signatures**
   - Sign wheels with GPG
   - Verify signatures in CI

3. **Release Drafter**
   - Auto-generate release notes from PR titles
   - Categorize changes (features, fixes, etc.)

4. **Version Bumping**
   - Auto-increment version in pyproject.toml
   - Create PR with version bump

5. **Rollback Mechanism**
   - Ability to yank release from PyPI
   - Automated rollback procedure

---

## Cost Analysis

**GitHub Actions Usage**:
- Build: 9 jobs (3 OS × 3 Python) × 10 minutes = 90 minutes
- Test: 3 jobs × 3 minutes = 9 minutes
- Publish: 1 job × 2 minutes = 2 minutes
- Release: 1 job × 1 minute = 1 minute
- **Total**: ~102 minutes per release

**Breakdown**:
- Linux: 30 minutes
- macOS: 30 minutes × 10 = 300 effective minutes
- Windows: 30 minutes × 2 = 60 effective minutes
- **Total**: ~360 effective minutes per release

**With 1 release/month**: Well within free tier.

---

## References

- **Issue**: #5 (GitHub Actions Release Workflow)
- **maturin-action**: https://github.com/PyO3/maturin-action
- **PyPI Publishing**: https://packaging.python.org/guides/publishing-package-distribution-releases-using-github-actions-ci-cd-workflows/
- **Keep a Changelog**: https://keepachangelog.com/
- **Semantic Versioning**: https://semver.org/

---

## Approval

**Product Lead**: Approved
**SRE/Platform**: Assigned
**Target Completion**: Week 2 of 0.0.1-alpha

---

*This design doc will be updated as implementation progresses.*
