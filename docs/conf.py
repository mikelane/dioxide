"""Sphinx configuration file for the dioxide documentation."""

from __future__ import annotations

import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sphinx.application import Sphinx

# Add the project root directory to the path so Sphinx can find the modules
sys.path.insert(0, str(Path("..").resolve()))

# Import version from package
import dioxide

_version = dioxide.__version__

# -- Project information -----------------------------------------------------
project = "dioxide"
copyright = f"{datetime.now(tz=UTC).year}, dioxide Contributors"  # noqa: A001
author = "dioxide Contributors"

version = _version
release = _version

# The document name of the "master" document
master_doc = "index"

# -- General configuration ---------------------------------------------------
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.viewcode",
    "sphinx.ext.napoleon",
    "sphinx.ext.intersphinx",
    "sphinx_autodoc_typehints",
    "sphinx.ext.coverage",
    "sphinx.ext.todo",
    "sphinx_copybutton",
    "autoapi.extension",
    "myst_parser",
]

# Configure autoapi extension for automatic API documentation
autoapi_type = "python"
autoapi_dirs = ["../python/dioxide"]
autoapi_keep_files = True
autoapi_options = [
    "members",
    "undoc-members",
    "show-inheritance",
    "show-module-summary",
    "special-members",
    "imported-members",
]

# Configure autodoc
autodoc_default_options = {
    "members": True,
    "undoc-members": True,
    "show-inheritance": True,
    "special-members": "__init__",
}
autodoc_typehints = "description"
autodoc_member_order = "bysource"

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
    "python": ("https://docs.python.org/3", None),
}

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store", "**.ipynb_checkpoints"]

# Set the default role for inline code (to help with code formatting)
default_role = "code"

# Configure MyST parser for Markdown
myst_enable_extensions = [
    "amsmath",
    "colon_fence",
    "deflist",
    "dollarmath",
    "html_admonition",
    "html_image",
    "linkify",
    "replacements",
    "smartquotes",
    "substitution",
    "tasklist",
]
myst_heading_anchors = 3
myst_update_mathjax = False

# -- Options for HTML output -------------------------------------------------
html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]
html_css_files = ["css/custom.css"]

# Custom sidebar templates
html_sidebars = {
    "**": [
        "relations.html",  # needs 'show_related': True theme option
        "searchbox.html",
    ]
}

# Theme options
html_theme_options = {
    "navigation_depth": 4,
    "collapse_navigation": False,
    "sticky_navigation": True,
    "titles_only": False,
    "display_version": True,
    "logo_only": False,
}

# HTML context
html_context = {
    "display_github": True,
    "github_user": "mikelane",
    "github_repo": "dioxide",
    "github_version": "main",
    "conf_py_path": "/docs/",
}

# Custom logo
# html_logo = '_static/logo.png'  # noqa: ERA001
html_favicon = None

# -- Options for LaTeX output ------------------------------------------------
latex_elements = {
    "papersize": "letterpaper",
    "pointsize": "10pt",
    "preamble": "",
    "figure_align": "htbp",
}

latex_documents = [
    (master_doc, "dioxide.tex", "dioxide Documentation", "dioxide Contributors", "manual"),
]

# -- Options for manual page output ------------------------------------------
man_pages = [(master_doc, "dioxide", "dioxide Documentation", [author], 1)]

# -- Options for Texinfo output ----------------------------------------------
texinfo_documents = [
    (
        master_doc,
        "dioxide",
        "dioxide Documentation",
        author,
        "dioxide",
        "Fast, Rust-backed declarative dependency injection framework for Python.",
        "Miscellaneous",
    ),
]

# -- Options for todo extension ----------------------------------------------
todo_include_todos = True

# Custom CSS file for minor styling adjustments
html_static_path = ["_static"]


def setup(app: Sphinx) -> None:
    """Add custom CSS file to Sphinx build."""
    app.add_css_file("css/custom.css")
