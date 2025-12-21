"""Sphinx configuration file for the dioxide documentation."""

from __future__ import annotations

import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sphinx.application import Sphinx

# Add the project root directory to the path so Sphinx can find the modules
sys.path.insert(0, str(Path('..').resolve()))

# Import version from package
# Version is synchronized across:
# - python/dioxide/__init__.py (__version__ variable)
# - Cargo.toml (package.version field)
# - ReadTheDocs (builds for each git tag matching v*.*.*)
import dioxide

_version = dioxide.__version__

# -- Project information -----------------------------------------------------
project = 'dioxide'
copyright = f'{datetime.now(tz=UTC).year}, dioxide Contributors'
author = 'dioxide Contributors'

# Version displayed in documentation
# - version: short X.Y version (e.g., "0.1")
# - release: full X.Y.Z version (e.g., "0.1.0-beta.2")
version = '.'.join(_version.split('.')[:2])  # Extract X.Y
release = _version  # Full version including pre-release tags

# The document name of the "master" document
master_doc = 'index'

# -- General configuration ---------------------------------------------------
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.viewcode',
    'sphinx.ext.napoleon',
    'sphinx.ext.intersphinx',
    'sphinx_autodoc_typehints',
    'sphinx.ext.coverage',
    'sphinx.ext.todo',
    'sphinx_copybutton',
    'sphinx_design',
    'sphinx_tippy',
    'sphinx_togglebutton',
    'sphinxcontrib.mermaid',
    'autoapi.extension',
    'myst_parser',
]

# Configure autoapi extension for automatic API documentation
autoapi_type = 'python'
autoapi_dirs = ['../python/dioxide']
autoapi_root = 'api'  # Generate API docs under /api/ for cleaner URLs
autoapi_keep_files = True
autoapi_options = [
    'members',
    'undoc-members',
    'show-inheritance',
    'show-module-summary',
    'special-members',
    'imported-members',
]

# Configure autodoc
autodoc_default_options = {
    'members': True,
    'undoc-members': True,
    'show-inheritance': True,
    'special-members': '__init__',
}
autodoc_typehints = 'description'
autodoc_member_order = 'bysource'

# Configure napoleon for parsing Google-style and NumPy-style docstrings
napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = False
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = True
napoleon_use_admonition_for_notes = True
napoleon_use_admonition_for_references = True
napoleon_use_ivar = False
napoleon_use_param = True
napoleon_use_rtype = True
napoleon_preprocess_types = False
napoleon_type_aliases = None
napoleon_attr_annotations = True

# Configure intersphinx to link to external documentation
intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
}

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store', '**.ipynb_checkpoints']

# Set the default role for inline code (to help with code formatting)
default_role = 'code'

# Configure MyST parser for Markdown
myst_enable_extensions = [
    'amsmath',
    'colon_fence',
    'deflist',
    'dollarmath',
    'html_admonition',
    'html_image',
    'linkify',
    'replacements',
    'smartquotes',
    'substitution',
    'tasklist',
]
myst_heading_anchors = 3
myst_update_mathjax = False
myst_linkify_fuzzy_links = False  # Only match URLs with schema (http://, https://)

# -- Options for HTML output -------------------------------------------------
html_theme = 'furo'
html_static_path = ['_static']
html_css_files = ['css/custom.css']

# Furo theme options
# See: https://pradyunsg.me/furo/customisation/
#
# dioxide color scheme:
#   - black: #000000
#   - white: #ffffff
#   - light orange: #ff8445
#   - dark orange: #8d2f0d
html_theme_options = {
    # Logo configuration - use dark logo on light background, light logo on dark background
    'light_logo': 'images/dioxide-logo-dark.png',
    'dark_logo': 'images/dioxide-logo-light.png',
    # Light mode brand colors (dark orange for contrast on light background)
    'light_css_variables': {
        'color-brand-primary': '#8d2f0d',
        'color-brand-content': '#8d2f0d',
        'color-link': '#8d2f0d',
        'color-link--hover': '#ff8445',
    },
    # Dark mode brand colors (light orange for contrast on dark background)
    'dark_css_variables': {
        'color-brand-primary': '#ff8445',
        'color-brand-content': '#ff8445',
        'color-link': '#ff8445',
        'color-link--hover': '#ffffff',
    },
    # Hide project name since logo includes it
    'sidebar_hide_name': True,
    # Enable keyboard navigation
    'navigation_with_keys': True,
    # Add view/edit buttons at top of page
    'top_of_page_buttons': ['view', 'edit'],
    # GitHub repository for edit links
    'source_repository': 'https://github.com/mikelane/dioxide/',
    'source_branch': 'main',
    'source_directory': 'docs/',
}

# HTML context for version information
html_context = {
    # Version information for ReadTheDocs version switcher
    # ReadTheDocs injects these automatically, but we set defaults for local builds
    'current_version': _version,
    'version': version,
    'release': release,
}

# Favicon - use the hex logo (no text) for browser tabs
html_favicon = '_static/images/dioxide-logo-hex.png'

# -- Options for LaTeX output ------------------------------------------------
latex_elements = {
    'papersize': 'letterpaper',
    'pointsize': '10pt',
    'preamble': '',
    'figure_align': 'htbp',
}

latex_documents = [
    (master_doc, 'dioxide.tex', 'dioxide Documentation', 'dioxide Contributors', 'manual'),
]

# -- Options for manual page output ------------------------------------------
man_pages = [(master_doc, 'dioxide', 'dioxide Documentation', [author], 1)]

# -- Options for Texinfo output ----------------------------------------------
texinfo_documents = [
    (
        master_doc,
        'dioxide',
        'dioxide Documentation',
        author,
        'dioxide',
        'Declarative dependency injection framework for Python that makes clean architecture simple.',
        'Miscellaneous',
    ),
]

# -- Options for todo extension ----------------------------------------------
todo_include_todos = True

# -- Options for sphinx-copybutton extension ---------------------------------
# Remove common prompts from copied code blocks
copybutton_prompt_text = r'>>> |\.\.\. |\$ |In \[\d*\]: | {2,5}\.\.\.: | {5,8}: '
copybutton_prompt_is_regexp = True
# Skip output-only blocks (lines starting with output prefixes)
copybutton_only_copy_prompt_lines = True
copybutton_remove_prompts = True

# -- Options for sphinx-tippy extension --------------------------------------
# Enable rich hover previews for cross-references
# Documentation: https://sphinx-tippy.readthedocs.io/
tippy_rtd_urls = [
    'https://dioxide.readthedocs.io/en/latest/',
]
tippy_enable_mathjax = False
tippy_props = {
    'placement': 'auto',
    'maxWidth': 500,
    'interactive': True,
    'delay': [100, 0],
}

# -- Options for sphinx-design extension -------------------------------------
# sphinx-design provides cards, grids, tabs, dropdowns, and badges
# No additional configuration needed - enabled via the extension

# -- Options for sphinx-togglebutton extension --------------------------------
# sphinx-togglebutton provides collapsible content sections
# Reduces cognitive load by hiding advanced content until needed
togglebutton_hint = 'Click to show'
togglebutton_hint_hide = 'Click to hide'

# -- Options for sphinxcontrib-mermaid extension -----------------------------
# Use a specific mermaid.js version from CDN for consistent rendering
mermaid_version = '11.4.1'
# Configure mermaid to work with Furo dark theme (dioxide color scheme)
# dioxide brand colors: orange #e67e22, dark background #1a1a1a
mermaid_init_js = '''
mermaid.initialize({
    startOnLoad: true,
    theme: 'dark',
    themeVariables: {
        primaryColor: '#d35400',
        primaryTextColor: '#ffffff',
        primaryBorderColor: '#e67e22',
        lineColor: '#e67e22',
        secondaryColor: '#2c3e50',
        tertiaryColor: '#1a252f',
        background: '#1a1a1a',
        mainBkg: '#2c3e50',
        nodeBorder: '#e67e22',
        clusterBkg: '#2c3e50',
        clusterBorder: '#e67e22',
        titleColor: '#ffffff',
        edgeLabelBackground: '#2c3e50',
        actorBkg: '#d35400',
        actorBorder: '#e67e22',
        actorTextColor: '#ffffff',
        signalColor: '#e67e22',
        signalTextColor: '#ffffff',
        noteBkgColor: '#2c3e50',
        noteTextColor: '#ffffff',
        noteBorderColor: '#e67e22'
    }
});
'''

# -- Options for linkcheck builder --------------------------------------------
# Patterns to ignore when checking links
linkcheck_ignore = [
    # Local development servers
    r'http://localhost:\d+',
    r'http://127\.0\.0\.1:\d+',
    # GitHub blob URLs (can be rate-limited during linkcheck)
    r'https://github\.com/mikelane/dioxide/blob/.*',
    # GitHub line anchors (often cause false positives due to dynamic content)
    r'https://github\.com/.*/blob/.*#L\d+',
    # GitHub settings pages (require authentication)
    r'https://github\.com/.*/settings/.*',
    # GitHub security advisories (require authentication)
    r'https://github\.com/.*/security/advisories/.*',
    # GitHub discussions (may not be enabled on all repos)
    r'https://github\.com/.*/discussions',
    # ReadTheDocs dashboard URLs (require authentication or redirect)
    r'https://readthedocs\.io/.*',
    r'https://readthedocs\.org/support/.*',
    # ReadTheDocs versioned URLs (version may not exist yet)
    r'https://dioxide\.readthedocs\.io/en/v[\d\.]+/',
    # External sites that can be slow or unreliable
    r'https://pyo3\.rs.*',
    r'https://www\.maturin\.rs.*',
]

# Anchors to ignore (fragment identifiers that may not exist)
linkcheck_anchors_ignore = [
    # GitHub dynamically generates anchors
    r'^L\d+',
]

# Timeout for each link check request (seconds)
linkcheck_timeout = 30

# Number of retries for failed links
linkcheck_retries = 3

# Number of parallel workers for link checking
linkcheck_workers = 5

# Allow common redirects (e.g., PyPI package pages often redirect)
linkcheck_allowed_redirects = {
    r'https://pypi\.org/.*': r'https://pypi\.org/.*',
    r'https://packaging\.python\.org/.*': r'https://packaging\.python\.org/.*',
    r'https://pyo3\.rs/.*': r'https://pyo3\.rs/.*',
    r'https://python-semantic-release\.readthedocs\.io/.*': r'https://python-semantic-release\.readthedocs\.io/.*',
    r'https://semantic-release\.gitbook\.io/.*': r'https://semantic-release\.gitbook\.io/.*',
    r'https://www\.sphinx-doc\.org/.*': r'https://www\.sphinx-doc\.org/.*',
    r'https://docs\.rs/.*': r'https://docs\.rs/.*',
    r'https://docs\.readthedocs\.io/.*': r'https://docs\.readthedocs\.io/.*',
}

# Rate limit requests to avoid being blocked (seconds between requests per host)
linkcheck_rate_limit_timeout = 5.0
