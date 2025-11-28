# Release Process

This document describes how to create releases for dioxide. The release process uses
commitizen for version management and GitHub Actions for automated building and publishing.

## Prerequisites

Before creating a release, ensure:

1. **Clean working directory**: All changes committed and pushed
   ```bash
   git status  # Should show "nothing to commit, working tree clean"
   ```

2. **On main branch**: Releases must be tagged from main
   ```bash
   git checkout main
   git pull origin main
   ```

3. **All CI checks passing**: Check the latest commit on main
   ```bash
   gh run list --branch main --limit 5
   ```

4. **CHANGELOG.md is current**: Review unreleased changes
   ```bash
   head -50 CHANGELOG.md
   ```

5. **Dependencies installed**: Ensure commitizen is available
   ```bash
   uv sync --group dev
   ```

## Creating a Release

### Using Commitizen (Recommended)

Commitizen automates version bumping, changelog updates, and git tagging based on
conventional commits.

#### Dry Run First

Always preview what will happen before actually bumping:

```bash
uv run cz bump --dry-run
```

This shows:
- Current version
- New version (based on commit types)
- Files that will be modified
- Changelog entries that will be added

#### Create the Release

If the dry run looks correct:

```bash
uv run cz bump
```

This will:
1. Analyze commits since the last tag
2. Determine the version bump type:
   - `feat:` commits trigger **minor** bump (0.3.0 -> 0.4.0)
   - `fix:`, `perf:` commits trigger **patch** bump (0.3.0 -> 0.3.1)
   - `BREAKING CHANGE:` in body triggers **major** bump (0.3.0 -> 1.0.0)
   - `docs:`, `chore:`, `ci:`, `test:` do NOT trigger a release
3. Update version in `Cargo.toml`
4. Update `CHANGELOG.md` with new entries
5. Create a commit: `bump: version X.Y.Z -> A.B.C`
6. Create a git tag: `vA.B.C`

#### Push the Release

```bash
git push origin main --tags
```

The tag push triggers the release workflow.

### Specifying a Version Manually

To force a specific version (useful for pre-releases or corrections):

```bash
# Bump to specific version
uv run cz bump --version 0.4.0

# Create a pre-release
uv run cz bump --prerelease beta  # Creates 0.4.0-beta.0

# Increment pre-release
uv run cz bump --prerelease beta  # Creates 0.4.0-beta.1
```

### Manual Release (Emergency Only)

If commitizen is unavailable or you need fine-grained control:

```bash
# 1. Update Cargo.toml version manually
vim Cargo.toml  # Change version = "X.Y.Z" to new version

# 2. Update Cargo.lock
cargo check

# 3. Update CHANGELOG.md manually

# 4. Commit and tag
git add Cargo.toml Cargo.lock CHANGELOG.md
git commit -m "bump: version X.Y.Z -> A.B.C"
git tag vA.B.C
git push origin main --tags
```

## What Happens During Release

When you push a tag matching `v*.*.*`, GitHub Actions runs the release workflow:

### 1. Version Validation (2 minutes)

- Extracts version from `Cargo.toml`
- Compares with git tag version
- **Fails immediately** if they don't match (prevents wasting build time)

### 2. Build Wheels (30-45 minutes)

Builds wheels for all supported platforms in parallel:

| Platform | Architecture | Python Versions |
|----------|-------------|-----------------|
| Linux | x86_64 | 3.11, 3.13, 3.14 |
| Linux | aarch64 (ARM64) | 3.11, 3.13, 3.14 |
| macOS | x86_64 (Intel) | 3.14 |
| macOS | aarch64 (Apple Silicon) | 3.14 |
| Windows | x86_64 | 3.11 (abi3 wheel) |

Note: Windows uses `abi3` wheels that work for all Python versions >= 3.11.

### 3. Build Source Distribution (5 minutes)

Creates `dioxide-X.Y.Z.tar.gz` for pip installation from source.

### 4. Validate Wheels (5 minutes)

- Validates ZIP structure of each wheel
- Checks for trailing data after EOCD (End of Central Directory)
- Validates wheel metadata with `check-wheel-contents`
- **Warnings** for trailing data (will be stripped before upload)
- **Errors** for corrupt ZIP structure (fails the release)

### 5. Test Wheels (10-15 minutes)

- Installs built wheels on each platform
- Runs smoke tests (`tests/smoke_test.py`)
- Runs full test suite (`pytest tests/`)

### 6. Create GitHub Release (2 minutes)

- Extracts release notes from `CHANGELOG.md`
- Creates GitHub Release with all artifacts attached

### 7. Publish to PyPI (5 minutes)

- Strips trailing data from wheels (PyPI validation fix)
- Publishes using PyPI Trusted Publishing (OIDC, no tokens)
- Creates deployment summary

### 8. Verify Publication (2 minutes)

- Waits 60 seconds for PyPI propagation
- Installs from PyPI: `pip install dioxide==X.Y.Z`
- Verifies import works

**Total time**: ~90-120 minutes

## Handling Failures

### Version Mismatch

**Symptom**: Workflow fails in "Validate Version" step

**Cause**: Tag version doesn't match `Cargo.toml` version

**Fix**:
```bash
# Delete the tag locally and remotely
git tag -d vX.Y.Z
git push origin :refs/tags/vX.Y.Z

# Fix Cargo.toml version, commit, and re-tag
vim Cargo.toml
cargo check
git add Cargo.toml Cargo.lock
git commit --amend --no-edit
git tag vX.Y.Z
git push origin main --tags --force
```

### Wheel Build Failures

**Symptom**: One or more wheel builds fail

**Common causes**:
- Rust compilation errors on specific platforms
- Missing platform-specific dependencies
- GitHub runner issues (rare)

**Fix**:
1. Check the failing job logs
2. If it's a code issue, fix and create a new patch release
3. If it's a runner issue, re-run the failed job

### Test Failures

**Symptom**: Tests pass locally but fail in CI

**Common causes**:
- Platform-specific behavior differences
- Missing test dependencies
- Timing issues (flaky tests)

**Fix**:
1. Reproduce locally if possible:
   ```bash
   # Create fresh environment
   uv venv --python 3.13
   source .venv/bin/activate
   uv sync --all-extras
   maturin develop
   pytest tests/ -v
   ```
2. Fix the issue and create a new patch release

### Wheel Validation Failures

**Symptom**: Wheels fail ZIP structure validation

**Cause**: Maturin sometimes adds trailing NULL bytes after ZIP EOCD

**Note**: This is automatically handled - the workflow strips trailing data before
PyPI upload. If you see warnings about trailing data, these are informational only.

**If you see errors** (not warnings):
- The wheel has genuine ZIP corruption
- Check Rust build logs for errors
- May need to clean build and retry

### PyPI Upload Failures

**Symptom**: Upload to PyPI fails

**Common causes**:
- Network issues (retry usually works)
- Version already exists on PyPI (version burn)
- Invalid wheel structure (should be caught by validation)

**If version already exists** (version burn):

PyPI has a strict policy: once a version is uploaded, that version number can
NEVER be reused, even if the release is deleted. This is called "version burn."

**Fix for version burn**:
```bash
# Create a patch release with the next version
uv run cz bump --increment PATCH

# Or manually
# Edit Cargo.toml to next patch version
# Update CHANGELOG
git add Cargo.toml Cargo.lock CHANGELOG.md
git commit -m "bump: version X.Y.Z -> X.Y.Z+1"
git tag vX.Y.(Z+1)
git push origin main --tags
```

### Failed Release Cleanup

If a release partially succeeded (e.g., GitHub Release created but PyPI failed):

```bash
# Delete the GitHub release through the UI or:
gh release delete vX.Y.Z --yes

# Delete the git tag
git tag -d vX.Y.Z
git push origin :refs/tags/vX.Y.Z

# Fix the issue
# Create new release with incremented version
```

## Lessons Learned

### v0.3.0 / v0.3.1 Release Issues

The v0.3.0 release experienced several issues that led to improvements:

1. **Test PyPI caused version burn, not prevented it**

   We initially used Test PyPI as a staging step before Production PyPI. However,
   Test PyPI and Production PyPI are separate registries with the SAME version-burn
   policy. When Test PyPI succeeded but Production PyPI failed (due to trailing data),
   we couldn't retry - we had to bump to v0.3.1.

   **Solution**: Removed Test PyPI step. Test PyPI is useful for testing the upload
   PROCESS, not the code. If CI passes (tests, wheel validation), go directly to
   Production PyPI.

2. **Wheel trailing data caused PyPI rejection**

   Maturin sometimes adds trailing NULL bytes after the ZIP End of Central Directory.
   PyPI's strict validation rejects these wheels.

   **Solution**: Added wheel validation step that warns about trailing data, and
   stripping step that removes trailing data before upload.

3. **Windows Server 2025 compatibility issues**

   The `windows-latest` runner upgraded to Windows Server 2025, which caused wheel
   compatibility issues.

   **Solution**: Pin to `windows-2022` runner explicitly.

4. **Multiple Windows wheel builds were redundant**

   We were building separate wheels for each Python version on Windows, but abi3
   wheels work for all Python versions.

   **Solution**: Build Windows wheel only once (with Python 3.11 abi3).

## Configuration

### Commitizen Configuration

Located in `pyproject.toml`:

```toml
[tool.commitizen]
name = "cz_conventional_commits"
version_provider = "cargo"           # Read/write version from Cargo.toml
tag_format = "v$version"             # Tags like v0.3.0
update_changelog_on_bump = true      # Auto-update CHANGELOG.md
changelog_file = "CHANGELOG.md"
major_version_zero = true            # Allow breaking changes in 0.x
```

### Release Workflow

Located in `.github/workflows/release-automated.yml`

Triggers on:
- Tag push matching `v*.*.*`
- Manual workflow dispatch (for testing)

### PyPI Trusted Publishing

dioxide uses OIDC-based Trusted Publishing:
- No API tokens stored in secrets
- GitHub verifies the workflow identity
- PyPI trusts the verified identity

Configuration is done in PyPI project settings, not in the repository.

## Monitoring Releases

### During Release

Watch the workflow progress:
```bash
gh run watch
```

Or view in browser:
```bash
gh run view --web
```

### After Release

Verify the release:

```bash
# Check PyPI
pip index versions dioxide

# Check GitHub release
gh release view vX.Y.Z

# Install and test
pip install dioxide==X.Y.Z
python -c "import dioxide; print(dioxide.__version__)"
```

## Quick Reference

```bash
# Preview release
uv run cz bump --dry-run

# Create release
uv run cz bump
git push origin main --tags

# Force patch release
uv run cz bump --increment PATCH

# Force minor release
uv run cz bump --increment MINOR

# Create pre-release
uv run cz bump --prerelease beta

# Watch workflow
gh run watch

# Check PyPI
pip index versions dioxide
```
