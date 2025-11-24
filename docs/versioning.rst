Documentation Versioning Strategy
===================================

dioxide provides versioned documentation to ensure you can access documentation for the specific version of the library you're using.

Version Types
-------------

The documentation is available in three main forms:

- **latest**: Always tracks the ``main`` branch (bleeding edge, unreleased features)
- **stable**: Points to the most recent stable release (recommended for production)
- **Specific versions**: Documentation for each tagged release (e.g., v0.1.0, v0.2.0)

Accessing Different Versions
-----------------------------

When viewing the documentation on ReadTheDocs, you can switch between versions using the version selector dropdown in the bottom-left corner of the page.

Version Naming Convention
--------------------------

dioxide follows `Semantic Versioning <https://semver.org/>`_ (SemVer):

- **Major version** (X.0.0): Breaking changes to the public API
- **Minor version** (0.X.0): New features, backward compatible
- **Patch version** (0.0.X): Bug fixes, backward compatible

Pre-release versions include additional labels:

- **alpha** (0.1.0-alpha): Early development, API may change
- **beta** (0.1.0-beta): Feature complete, API stable, testing phase
- **rc** (0.1.0-rc.1): Release candidate, final testing before stable

Recommended Versions
--------------------

- **Production use**: Always use **stable** or a specific **stable release** (no pre-release label)
- **Testing new features**: Use **latest** to see upcoming features
- **Troubleshooting**: Use the **specific version** matching your installed package

Checking Your Installed Version
--------------------------------

To find which version of dioxide you have installed:

.. code-block:: python

   import dioxide
   print(dioxide.__version__)

Or from the command line:

.. code-block:: bash

   python -c "import dioxide; print(dioxide.__version__)"

Version Synchronization
-----------------------

dioxide maintains version synchronization across:

- Python package (``dioxide.__version__``)
- Rust crate (``Cargo.toml``)
- Documentation (built for each git tag)
- PyPI releases

This ensures consistency between the code, documentation, and published packages.

Documentation Build Process
----------------------------

Documentation is automatically built and published for:

1. Every commit to ``main`` → **latest** version
2. Every git tag matching ``v*.*.*`` → **specific version**
3. Latest stable tag → **stable** version

The build process:

1. ReadTheDocs detects new commits/tags via GitHub webhook
2. Rust extension is compiled during the build
3. Sphinx extracts version from ``dioxide.__version__``
4. Documentation is generated with the correct version number
5. Version switcher dropdown is updated

Local Documentation Builds
---------------------------

To build documentation locally:

.. code-block:: bash

   # Install documentation dependencies
   uv sync --group docs

   # Build HTML documentation
   uv run sphinx-build -b html docs docs/_build/html

   # View in browser
   open docs/_build/html/index.html  # macOS
   xdg-open docs/_build/html/index.html  # Linux
   start docs/_build/html/index.html  # Windows

The locally-built documentation will show your current development version.

Release Process
---------------

When a new version is released:

1. Version is updated in ``Cargo.toml``
2. Commit is tagged with ``v{VERSION}`` (e.g., ``v0.2.0``)
3. Tag is pushed to GitHub
4. CI/CD builds and publishes wheels to PyPI
5. ReadTheDocs automatically builds documentation for the new tag
6. Version appears in the version switcher dropdown

Deprecated Versions
-------------------

Documentation for older versions remains available indefinitely. However:

- Only the latest stable version receives bug fixes
- Security updates are backported to the last two minor versions
- Documentation is not updated for versions older than the current stable

Troubleshooting
---------------

**Version switcher not appearing**
   This is normal for local builds. The version switcher only appears on ReadTheDocs-hosted documentation.

**Wrong version displayed**
   The version comes from ``dioxide.__version__``. If you've made local changes, rebuild the package:

   .. code-block:: bash

      maturin develop

**Documentation out of sync with code**
   Ensure you're viewing documentation for your installed version using the version switcher.

See Also
--------

- `Contributing Guide <https://github.com/mikelane/dioxide/blob/main/CONTRIBUTING.md>`_ - Contributing guide with release process details
- `ReadTheDocs Versioning <https://docs.readthedocs.io/en/stable/versions.html>`_ - ReadTheDocs versioning documentation
- `Semantic Versioning <https://semver.org/>`_ - SemVer specification
