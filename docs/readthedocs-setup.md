# ReadTheDocs.io Setup Guide

This guide provides step-by-step instructions for setting up automatic documentation deployment for the dioxide project using ReadTheDocs.io.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Initial ReadTheDocs Setup](#initial-readthedocs-setup)
3. [Repository Configuration](#repository-configuration)
4. [Project Settings](#project-settings)
5. [Webhook Configuration](#webhook-configuration)
6. [Versioning Strategy](#versioning-strategy)
7. [Custom Domain Setup](#custom-domain-setup-optional)
8. [Verification Steps](#verification-steps)
9. [Maintenance](#maintenance)
10. [Troubleshooting](#troubleshooting)

---

## Prerequisites

Before starting, ensure you have:

- GitHub account with admin access to the dioxide repository
- Access to ReadTheDocs.io (account can be created during setup)
- Sphinx documentation already configured in the repository (PR #141, merged)
- `.readthedocs.yaml` configuration file in the repository (PR #155)

> **Note**: The `.readthedocs.yaml` file is added by [PR #155](https://github.com/mikelane/dioxide/pull/155).
> If that PR has not yet been merged, you can either:
> 1. Wait for PR #155 to merge first, or
> 2. Merge PR #155 before following this guide

**Verify prerequisites:**

```bash
# Check that Sphinx is set up
ls docs/conf.py docs/index.rst

# Check that ReadTheDocs config exists (requires PR #155)
ls .readthedocs.yaml

# Verify documentation builds locally
uv sync --group docs
uv run sphinx-build -b html docs docs/_build/html
```

All commands should succeed before proceeding.

---

## Initial ReadTheDocs Setup

### Step 1: Create ReadTheDocs Account

1. Navigate to https://readthedocs.io/
2. Click "Sign Up" in the top right corner
3. Choose "Sign Up with GitHub" (recommended for automatic repository access)
4. Authorize ReadTheDocs to access your GitHub account
   - **Required permissions:**
     - Read access to code
     - Read access to metadata
     - Read and write access to webhooks
5. Complete your profile information if prompted

**Expected result:** You are logged into ReadTheDocs with GitHub authentication.

### Step 2: Import the dioxide Repository

1. From the ReadTheDocs dashboard, click "Import a Project"
2. You should see a list of your GitHub repositories
3. Find `dioxide` in the list
4. Click the "+" button next to `dioxide` to import it

**If you don't see the repository:**

1. Click "Import Manually" at the top of the page
2. Fill in the details:
   - **Name:** `dioxide`
   - **Repository URL:** `https://github.com/mikelane/dioxide`
   - **Repository type:** Git
   - **Default branch:** `main`
   - **Default version:** `latest`
3. Click "Next"

**Expected result:** The dioxide project appears in your ReadTheDocs dashboard.

---

## Repository Configuration

The repository should already have the necessary configuration files:

- **Sphinx documentation structure**: Added by PR #141 (merged)
- **ReadTheDocs configuration**: Added by PR #155

Verify the following files exist and are properly configured:

### Verify `.readthedocs.yaml`

Location: `.readthedocs.yaml` (repository root)

```yaml
# .readthedocs.yaml
# ReadTheDocs configuration file
# See https://docs.readthedocs.io/en/stable/config-file/v2.html

version: 2

build:
  os: ubuntu-22.04
  tools:
    python: "3.11"
  jobs:
    post_install:
      # Install Rust toolchain for building the Rust extension
      - curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
      - source $HOME/.cargo/env
      # Install maturin to build the Rust extension
      - pip install maturin

sphinx:
  configuration: docs/conf.py
  builder: html
  fail_on_warning: true

formats:
  - pdf
  - epub

python:
  install:
    # Install dioxide with dev dependencies
    - method: pip
      path: .
      extra_requirements:
        - dev
```

**Key configuration points:**

- `build.os: ubuntu-22.04` - Uses Ubuntu 22.04 for build environment
- `build.tools.python: "3.11"` - Uses Python 3.11 for building docs
- `build.jobs.post_install` - Installs Rust toolchain and maturin for building the Rust extension
- `sphinx.configuration: docs/conf.py` - Points to Sphinx config
- `sphinx.fail_on_warning: true` - Build fails if Sphinx warnings occur (ensures quality)
- `formats` - Generates HTML, PDF, and EPUB versions
- `python.install` - Installs dioxide with dev dependencies (includes Sphinx and extensions)

### Verify `docs/conf.py`

Location: `docs/conf.py` (repository root)

Ensure the Sphinx configuration includes:

```python
# Sphinx extensions for Python documentation
extensions = [
    "sphinx.ext.autodoc",      # Auto-generate docs from docstrings
    "sphinx.ext.napoleon",     # Support Google/NumPy docstring styles
    "sphinx.ext.viewcode",     # Add links to source code
    "sphinx.ext.intersphinx",  # Link to other projects' docs
    "sphinx.ext.autosummary",  # Generate summary tables
]

# Theme configuration
html_theme = "furo"  # Modern, clean theme
```

**Why these extensions matter for ReadTheDocs:**

- `autodoc` - Generates API documentation from Python docstrings
- `napoleon` - Supports readable docstring formats (Google/NumPy style)
- `viewcode` - Links documentation to source code on GitHub
- `intersphinx` - Links to external Python documentation (e.g., Python standard library)
- `autosummary` - Creates summary tables for modules/classes

---

## Project Settings

Configure the ReadTheDocs project settings for optimal documentation deployment.

### Step 1: Access Project Settings

1. Go to https://readthedocs.io/dashboard/
2. Click on the `dioxide` project
3. Click "Admin" in the left sidebar
4. Navigate to "Settings"

### Step 2: Configure General Settings

**Admin → Settings → General**

- **Name:** `dioxide`
- **Repository URL:** `https://github.com/mikelane/dioxide`
- **Repository type:** Git
- **Default branch:** `main`
- **Default version:** `latest`
- **Privacy level:** Public (unless you want private docs)
- **Programming language:** Python

**Save changes.**

### Step 3: Configure Advanced Settings

**Admin → Advanced Settings**

Key settings to configure:

- **Build privacy level:** Public
- **Default version:** `latest`
- **Show version warning:** ✓ (checked) - Shows banner when viewing old versions
- **Enable PDF build:** ✓ (checked) - Generates PDF version
- **Enable EPUB build:** ✓ (checked) - Generates EPUB version
- **Single version:** ✗ (unchecked) - Allows multiple versions (latest, stable, tags)

**Build settings:**

- **Build timeout:** 900 seconds (15 minutes) - Rust builds can take time
- **Install Project:** ✓ (checked) - Installs your project before building docs
- **Requirements file:** Leave empty (handled by `.readthedocs.yaml`)
- **Python interpreter:** CPython 3.x (from `.readthedocs.yaml`)

**Privacy settings:**

- **Make documentation private:** ✗ (unchecked) - Public documentation

**Save changes.**

### Step 4: Configure Automation Rules

**Admin → Automation Rules**

ReadTheDocs can automatically activate versions based on branch/tag patterns. Configure rules:

**Rule 1: Activate all branches**

- **Description:** Activate documentation for all branches
- **Match:** Custom Match
- **Pattern:** `.*` (regex matching all branches)
- **Version type:** Branch
- **Action:** Activate version
- **Priority:** 0

**Rule 2: Set stable version from tags**

- **Description:** Set stable version from latest release tag
- **Match:** Custom Match
- **Pattern:** `^v[0-9]+\.[0-9]+\.[0-9]+$` (matches v0.1.0, v1.0.0, etc.)
- **Version type:** Tag
- **Action:** Set as stable version
- **Priority:** 0

**Rule 3: Set default version to latest**

- **Description:** Set default version to latest (main branch)
- **Match:** Custom Match
- **Pattern:** `^main$`
- **Version type:** Branch
- **Action:** Set as default version
- **Priority:** 10 (higher priority)

**Save changes.**

---

## Webhook Configuration

ReadTheDocs needs a webhook to receive notifications when you push to GitHub, so it can automatically rebuild documentation.

### Step 1: Verify Webhook Integration

ReadTheDocs should automatically create a webhook when you import via GitHub. Verify it exists:

**On ReadTheDocs:**

1. Go to https://readthedocs.io/dashboard/
2. Click on the `dioxide` project
3. Click "Admin" in the left sidebar
4. Navigate to "Integrations"
5. You should see a "GitHub incoming webhook" integration
6. Note the webhook URL (e.g., `https://readthedocs.io/api/v2/webhook/dioxide/123456/`)

**On GitHub:**

1. Go to https://github.com/mikelane/dioxide
2. Click "Settings" (repository settings, not account settings)
3. Click "Webhooks" in the left sidebar
4. You should see a webhook with:
   - **Payload URL:** `https://readthedocs.io/api/v2/webhook/dioxide/123456/`
   - **Content type:** `application/json`
   - **Events:** "Just the push event" (or "Let me select individual events" with "Pushes" checked)
   - **Active:** ✓ (checked with green checkmark)

### Step 2: Create Webhook Manually (if needed)

If the webhook doesn't exist, create it manually:

**On GitHub:**

1. Go to https://github.com/mikelane/dioxide/settings/hooks
2. Click "Add webhook"
3. Fill in the details:
   - **Payload URL:** Copy from ReadTheDocs Admin → Integrations
   - **Content type:** `application/json`
   - **Secret:** Leave empty (ReadTheDocs handles authentication via payload)
   - **SSL verification:** Enable SSL verification (recommended)
   - **Which events:** Select "Just the push event"
   - **Active:** ✓ (checked)
4. Click "Add webhook"

**Verify webhook:**

1. Click on the webhook you just created
2. Scroll to "Recent Deliveries"
3. GitHub will automatically send a ping event
4. The delivery should show a green checkmark (200 OK response)

**Expected result:** GitHub sends webhook notifications to ReadTheDocs on every push to `main`.

---

## Versioning Strategy

Configure how ReadTheDocs handles different versions of your documentation.

### Version Types

ReadTheDocs supports three version types:

1. **latest** - Always points to the `main` branch (bleeding edge)
2. **stable** - Points to the latest release tag (e.g., `v0.1.0`)
3. **Tags** - Specific version tags (e.g., `v0.1.0`, `v0.2.0`)

### Configure Versions

**Admin → Versions**

You should see a list of versions detected from your repository:

**Branches:**

- `main` → Map to `latest`
  - **Active:** ✓ (checked)
  - **Hidden:** ✗ (unchecked)
  - **Privacy Level:** Public

**Tags (once you create release tags):**

- `v0.1.0` → First release
  - **Active:** ✓ (checked)
  - **Hidden:** ✗ (unchecked)
  - **Privacy Level:** Public
- `v0.2.0` → Second release
  - **Active:** ✓ (checked)
  - **Hidden:** ✗ (unchecked)
  - **Privacy Level:** Public

**Designate stable version:**

- Select the latest release tag (e.g., `v0.1.0`)
- Click "Set as default version" or mark it as `stable`

### Automated Versioning with Git Tags

When you create a new release:

```bash
# Tag a new release
git tag -a v0.1.0 -m "Release v0.1.0-beta: MLP Complete"
git push origin v0.1.0

# ReadTheDocs automatically:
# 1. Detects the new tag
# 2. Activates the version
# 3. Builds documentation for that version
# 4. Updates 'stable' to point to v0.1.0
```

**Version URLs:**

- Latest (main branch): https://dioxide.readthedocs.io/en/latest/
- Stable (latest release): https://dioxide.readthedocs.io/en/stable/
- Specific version: https://dioxide.readthedocs.io/en/v0.1.0/

---

## Custom Domain Setup (Optional)

ReadTheDocs provides a default subdomain (`dioxide.readthedocs.io`), but you can configure a custom domain.

### Step 1: Configure Custom Domain on ReadTheDocs

**Admin → Domains**

1. Click "Add Domain"
2. Enter your custom domain:
   - **Domain:** `docs.dioxide.dev` (example)
   - **Canonical:** ✓ (checked) - Makes this the primary domain
   - **HTTPS:** ✓ (checked) - Forces HTTPS
3. Click "Add"

**ReadTheDocs will provide DNS instructions:**

- **CNAME record:** Point `docs.dioxide.dev` to `dioxide.readthedocs.io`

### Step 2: Configure DNS

Go to your DNS provider (e.g., Cloudflare, Namecheap, Route 53) and add:

**DNS Record:**

- **Type:** CNAME
- **Name:** `docs` (or whatever subdomain you want)
- **Value:** `dioxide.readthedocs.io`
- **TTL:** 3600 (1 hour) or Auto

**Wait for DNS propagation** (usually 5-30 minutes, up to 48 hours).

### Step 3: Verify Custom Domain

Once DNS propagates:

1. Visit `https://docs.dioxide.dev`
2. You should see your documentation
3. ReadTheDocs automatically provisions an SSL certificate via Let's Encrypt

**Note:** If you don't have a custom domain, the default `dioxide.readthedocs.io` works perfectly fine.

---

## Verification Steps

After completing the setup, verify that everything works correctly.

### 1. Trigger a Build Manually

**Test that builds work:**

1. Go to https://readthedocs.io/projects/dioxide/
2. Click "Versions" in the left sidebar
3. Find the `latest` version
4. Click "Build Version"
5. Monitor the build log

**Expected result:** Build succeeds with no errors. Documentation is accessible at `https://dioxide.readthedocs.io/en/latest/`.

### 2. Trigger a Build via Push

**Test automatic webhook:**

```bash
# Make a small change to documentation (from repository root)
echo "# Test update" >> docs/index.rst

# Commit and push
git add docs/index.rst
git commit -m "docs: test ReadTheDocs webhook"
git push origin main
```

**Verify:**

1. Go to https://readthedocs.io/projects/dioxide/builds/
2. A new build should appear within seconds
3. Monitor the build log
4. Once complete, visit `https://dioxide.readthedocs.io/en/latest/`
5. Your change should be visible

**Expected result:** Build triggers automatically on push, completes successfully, and documentation updates.

### 3. Verify Documentation Quality

**Check all pages render correctly:**

1. Visit https://dioxide.readthedocs.io/en/latest/
2. Navigate through all sections:
   - **Home/Index** - Main landing page
   - **Getting Started** - Installation and quick start
   - **User Guide** - Tutorials and how-tos
   - **API Reference** - Auto-generated API docs
   - **Developer Guide** - Contributing and development
3. Verify all pages load without errors
4. Check that code examples have syntax highlighting
5. Verify that internal links work (no 404s)

**Check search functionality:**

1. Use the search box in the top right
2. Search for "adapter" or "service"
3. Verify search results are relevant

**Check version selector:**

1. Look for the version selector in the bottom left (usually a dropdown)
2. Verify it shows:
   - `latest` (main branch)
   - `stable` (latest release, if tagged)
   - Version tags (e.g., `v0.1.0`)
3. Switch between versions to verify they load

**Check downloadable formats:**

1. Look for "Download" link in the left sidebar or footer
2. Verify PDF and EPUB versions are available
3. Download and open the PDF to verify formatting

### 4. Verify Badge in README

After setup is complete, add the ReadTheDocs badge to `README.md`:

```markdown
[![Documentation Status](https://readthedocs.org/projects/dioxide/badge/?version=latest)](https://dioxide.readthedocs.io/en/latest/?badge=latest)
```

**Verify:**

1. Push the README update to GitHub
2. Visit https://github.com/mikelane/dioxide
3. The badge should appear and show "passing" (green) or "failing" (red)
4. Click the badge to verify it links to the documentation

---

## Maintenance

Regular maintenance tasks to keep documentation healthy.

### Monitor Builds

**Check build status regularly:**

1. Visit https://readthedocs.io/projects/dioxide/builds/
2. Review recent builds for failures
3. Fix any broken builds immediately (documentation is part of the product)

**Enable email notifications:**

1. Go to Admin → Notifications
2. Add your email address
3. Enable notifications for:
   - Failed builds
   - Build status changes

### Update Configuration

**When to update `.readthedocs.yaml`:**

- Upgrading Python version (e.g., 3.11 → 3.13)
- Adding new Sphinx extensions
- Changing build requirements
- Adjusting build timeout (for slow builds)

**After updating `.readthedocs.yaml`:**

1. Commit and push changes
2. Monitor the next build to ensure it uses the new configuration
3. Check build logs for any configuration warnings

### Manage Versions

**When you release a new version:**

```bash
# Tag the release
git tag -a v0.2.0 -m "Release v0.2.0: Post-MLP Features"
git push origin v0.2.0
```

**On ReadTheDocs:**

1. Go to Admin → Versions
2. The new tag (`v0.2.0`) should appear automatically
3. Activate the version (if not automatically activated)
4. Mark it as `stable` if it's the latest stable release
5. Optionally hide old versions to reduce clutter

### Deprecate Old Versions

**For very old versions:**

1. Go to Admin → Versions
2. Find the old version (e.g., `v0.1.0` after `v0.5.0` is released)
3. **Don't delete** - Keep for historical reference
4. Mark as **Hidden** to remove from version selector
5. Builds remain accessible via direct URL: `https://dioxide.readthedocs.io/en/v0.1.0/`

---

## Troubleshooting

Common issues and solutions when working with ReadTheDocs.

### Build Fails with "Command not found: cargo" or "rustc not found"

**Problem:** Rust toolchain not installed in the ReadTheDocs build environment.

**Solution:** Verify `.readthedocs.yaml` includes Rust installation in `build.jobs.post_install`:

```yaml
build:
  jobs:
    post_install:
      - curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
      - source $HOME/.cargo/env
      - pip install maturin
```

### Build Fails with "ModuleNotFoundError: No module named 'dioxide'"

**Problem:** The dioxide package isn't installed before Sphinx tries to import it.

**Solution:** Ensure `.readthedocs.yaml` installs the package:

```yaml
python:
  install:
    - method: pip
      path: .
      extra_requirements:
        - dev
```

**Why this works:** Sphinx's `autodoc` extension needs to import your Python modules to extract docstrings. Installing the package makes it importable.

### Build Fails with "sphinx.errors.ExtensionError: Could not import extension"

**Problem:** A Sphinx extension listed in `docs/conf.py` isn't installed.

**Solution:**

1. Check which extension is missing (look at the error message)
2. Add it to `pyproject.toml` under `[project.optional-dependencies]` → `dev`
3. Common missing extensions:
   - `sphinx-autodoc-typehints`
   - `sphinx-rtd-theme` or `furo`
   - `myst-parser` (for Markdown support)

Example fix in `pyproject.toml`:

```toml
[project.optional-dependencies]
dev = [
    "sphinx>=7.0.0",
    "sphinx-autodoc-typehints>=1.24.0",
    "furo>=2023.9.10",
    # ... other deps
]
```

### Build Timeout (Exceeds 15 minutes)

**Problem:** Build takes too long, especially when building the Rust extension.

**Solution:**

1. Increase timeout in Admin → Advanced Settings → Build timeout (max 60 minutes)
2. Or, optimize the build:
   - Use Rust release mode for faster builds (already in `.readthedocs.yaml`)
   - Cache Cargo dependencies (ReadTheDocs caches automatically)
   - Consider pre-building wheels and installing from PyPI (for stable releases)

### Webhook Not Triggering Builds

**Problem:** Pushing to GitHub doesn't trigger ReadTheDocs builds.

**Diagnosis:**

1. Go to GitHub → Settings → Webhooks
2. Click on the ReadTheDocs webhook
3. Check "Recent Deliveries"
4. If deliveries are failing (red X), click on one to see the error

**Solutions:**

- **404 Not Found:** Webhook URL is incorrect. Copy the correct URL from ReadTheDocs Admin → Integrations.
- **403 Forbidden:** Authentication issue. Regenerate the webhook on ReadTheDocs and update on GitHub.
- **Timeout:** ReadTheDocs might be down. Check https://status.readthedocs.com/
- **No deliveries at all:** Webhook isn't configured. Add it manually (see [Webhook Configuration](#webhook-configuration)).

### Documentation Not Updating After Push

**Problem:** You pushed changes but they don't appear on the live site.

**Diagnosis:**

1. Go to https://readthedocs.io/projects/dioxide/builds/
2. Check the latest build status:
   - **Passed:** Build succeeded, but you might be viewing a cached page
   - **Failed:** Build failed, fix the error and rebuild
   - **No build triggered:** Webhook issue (see above)

**Solutions:**

- **Cache issue:** Clear browser cache or open in incognito mode
- **Build failed:** Check build logs for errors, fix, and push again
- **Webhook not triggering:** See "Webhook Not Triggering Builds" above
- **Wrong branch:** Verify you pushed to `main`, not a feature branch

### "stable" Version Shows Outdated Docs

**Problem:** The `stable` version doesn't point to the latest release.

**Solution:**

1. Go to Admin → Versions
2. Find the latest release tag (e.g., `v0.2.0`)
3. Click "Edit"
4. Check "Set as stable version"
5. Save changes
6. Rebuild the `stable` version

### Search Results Are Empty or Outdated

**Problem:** Search doesn't find recently added documentation.

**Solution:** Search indexes rebuild during the next successful build. If search is still broken:

1. Go to Admin → Advanced Settings
2. Find "Search" section
3. Click "Reindex"
4. Wait for reindexing to complete (usually a few minutes)

### PDF/EPUB Downloads Are Missing

**Problem:** Can't find download links for PDF/EPUB versions.

**Solution:**

1. Verify formats are enabled in `.readthedocs.yaml`:
   ```yaml
   formats:
     - pdf
     - epub
   ```
2. Go to Admin → Advanced Settings
3. Ensure "Enable PDF build" and "Enable EPUB build" are checked
4. Rebuild the version
5. Look for download links in the left sidebar or footer

### Build Warnings Cause Build to Fail

**Problem:** Sphinx warnings (e.g., "reference not found") fail the build.

**Context:** We set `sphinx.fail_on_warning: true` in `.readthedocs.yaml` to maintain high documentation quality.

**Solution:**

1. Review the build log to see the specific warning
2. Fix the warning in the source (e.g., fix broken references, add missing docstrings)
3. If the warning is a false positive, you can disable `fail_on_warning` temporarily:
   ```yaml
   sphinx:
     fail_on_warning: false  # NOT RECOMMENDED for production
   ```
4. Push the fix and rebuild

**Common warnings:**

- **"reference target not found":** Broken link or invalid reference
- **"undefined label":** Missing or misspelled label in cross-reference
- **"document isn't included in any toctree":** Orphaned RST file not linked from any table of contents

### Can't Access Private Documentation

**Problem:** Documentation is set to private but you can't access it.

**Solution:**

1. Verify you're logged into ReadTheDocs with the correct account
2. Go to Admin → Settings
3. Check "Privacy level" is set to "Private"
4. Add users who need access:
   - Go to Admin → Maintainers
   - Add GitHub usernames or email addresses
   - They'll receive an invitation email

**Note:** Private documentation requires a ReadTheDocs subscription.

### Builds Succeed Locally But Fail on ReadTheDocs

**Problem:** `make html` works locally but fails on ReadTheDocs.

**Common causes:**

1. **Different Python version:** ReadTheDocs uses Python 3.11 (from `.readthedocs.yaml`), you might use 3.13 locally.
2. **Missing dependencies:** ReadTheDocs doesn't have access to your local environment.
3. **Path differences:** Absolute paths in `conf.py` might not work on ReadTheDocs.
4. **Rust toolchain:** ReadTheDocs needs Rust installed via `post_install` hook.

**Solution:**

1. Test builds in a clean virtual environment:
   ```bash
   python3.11 -m venv test-env
   source test-env/bin/activate
   pip install -e ".[dev]"
   cd docs && make html
   ```
2. Review build logs carefully on ReadTheDocs
3. Ensure all dependencies are in `pyproject.toml` under `dev` extras

---

## Best Practices

### Documentation Quality

1. **Always test locally first:**
   ```bash
   cd docs && make html
   open build/html/index.html  # macOS
   ```

2. **Write clear docstrings:**
   - Use Google or NumPy docstring format (napoleon extension parses both)
   - Document all public classes, functions, and methods
   - Include examples in docstrings

3. **Keep documentation DRY (Don't Repeat Yourself):**
   - Use `.. include::` to reuse content
   - Use `.. literalinclude::` to include code from source files
   - Auto-generate API docs with `autodoc`

4. **Maintain a changelog:**
   - Update `CHANGELOG.md` for each release
   - Include the changelog in Sphinx docs: `docs/changelog.rst`

### Version Control

1. **Use semantic versioning for tags:**
   - `v0.1.0` - Initial beta release
   - `v0.2.0` - Minor version bump
   - `v1.0.0` - Stable release

2. **Keep `main` branch stable:**
   - Only merge to `main` when ready to deploy docs
   - Use feature branches for WIP documentation

3. **Tag releases immediately:**
   ```bash
   git tag -a v0.1.0 -m "Release v0.1.0-beta"
   git push origin v0.1.0
   ```

### Monitoring

1. **Enable build notifications:**
   - Admin → Notifications
   - Add your email
   - Get notified immediately when builds fail

2. **Check build status regularly:**
   - Visit https://readthedocs.io/projects/dioxide/builds/ weekly
   - Fix broken builds within 24 hours

3. **Monitor documentation quality:**
   - Review user feedback (GitHub issues)
   - Check search analytics (if available)
   - Update outdated documentation proactively

### Performance

1. **Optimize build time:**
   - ReadTheDocs caches dependencies automatically
   - Keep Sphinx extensions minimal (only what you need)
   - Consider pre-building wheels for stable releases

2. **Keep docs size manageable:**
   - Large images slow down builds and page loads
   - Optimize images before committing (use tools like `optipng`, `jpegoptim`)
   - Consider hosting videos externally (YouTube, Vimeo)

### Security

1. **Never commit secrets:**
   - No API keys in documentation
   - No credentials in code examples
   - Use placeholders: `YOUR_API_KEY_HERE`

2. **Keep dependencies updated:**
   - Dependabot alerts (enable on GitHub)
   - Regularly update Sphinx and extensions
   - Review security advisories

---

## Additional Resources

### ReadTheDocs Documentation

- [Official ReadTheDocs Documentation](https://docs.readthedocs.io/)
- [Configuration File Reference](https://docs.readthedocs.io/en/stable/config-file/v2.html)
- [Build Process Overview](https://docs.readthedocs.io/en/stable/builds.html)
- [Versioning Documentation](https://docs.readthedocs.io/en/stable/versions.html)
- [Webhooks & Automation](https://docs.readthedocs.io/en/stable/webhooks.html)

### Sphinx Documentation

- [Sphinx Official Documentation](https://www.sphinx-doc.org/)
- [Sphinx Extensions](https://www.sphinx-doc.org/en/master/usage/extensions/index.html)
- [reStructuredText Primer](https://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html)

### GitHub Integration

- [GitHub Webhooks Documentation](https://docs.github.com/en/developers/webhooks-and-events/webhooks)
- [GitHub OAuth Apps](https://docs.github.com/en/developers/apps/building-oauth-apps)

### dioxide Documentation

- [Issue #139: Documentation Epic](https://github.com/mikelane/dioxide/issues/139)
- [Issue #141: Sphinx Structure](https://github.com/mikelane/dioxide/issues/141)
- [Issue #142: ReadTheDocs Config](https://github.com/mikelane/dioxide/issues/142)

---

## Conclusion

This guide provides comprehensive instructions for setting up ReadTheDocs.io for the dioxide project. By following these steps, documentation will automatically deploy on every commit to `main`, ensuring users always have access to up-to-date, high-quality documentation.

**Key takeaways:**

- ReadTheDocs integrates seamlessly with GitHub via webhooks
- Builds are triggered automatically on push
- Multiple versions (latest, stable, tags) are supported
- Configuration is managed via `.readthedocs.yaml` (version-controlled)
- Troubleshooting is straightforward with detailed build logs

**Next steps after setup:**

1. Verify all documentation builds successfully
2. Add ReadTheDocs badge to README.md
3. Monitor builds regularly
4. Update documentation as the codebase evolves
5. Maintain versioning discipline (tag releases)

For questions or issues, refer to the [Troubleshooting](#troubleshooting) section or consult the [ReadTheDocs Community](https://readthedocs.org/support/).
