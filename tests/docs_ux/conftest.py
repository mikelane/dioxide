"""Pytest configuration and shared fixtures for documentation UX BDD tests.

These tests verify documentation UX acceptance criteria using Playwright
for browser automation. Tests are designed to FAIL against current
documentation, validating that improvements are needed.

Usage:
    # Build docs first (required for local testing)
    uv run sphinx-build -b html docs docs/_build/html

    # Run all docs-ux tests
    uv run pytest tests/docs_ux/ -v

    # Run specific scenario
    uv run pytest tests/docs_ux/ -v -k "quickstart"

    # Run against live ReadTheDocs (slower, but tests production)
    DOCS_URL=https://dioxide.readthedocs.io/en/latest uv run pytest tests/docs_ux/ -v
"""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from pytest_bdd import given

if TYPE_CHECKING:
    from playwright.sync_api import (
        ElementHandle,
        Page,
    )


# Configuration
DOCS_BUILD_DIR = Path(__file__).parent.parent.parent / 'docs' / '_build' / 'html'
DEFAULT_DOCS_URL = os.environ.get('DOCS_URL', f'file://{DOCS_BUILD_DIR.absolute()}')
DOCS_SERVER_PORT = 8765


@pytest.fixture(scope='session')
def docs_url() -> str:
    """Return the URL for the documentation site.

    Uses DOCS_URL environment variable if set, otherwise serves local build.
    """
    return DEFAULT_DOCS_URL


@pytest.fixture(scope='session')
def docs_available(docs_url: str) -> bool:
    """Check if documentation is available (built or served).

    Returns True if docs are accessible, False otherwise.
    For local file:// URLs, checks if the directory exists.
    For http:// URLs, would need to check connectivity.
    """
    if docs_url.startswith('file://'):
        path = docs_url.replace('file://', '')
        index_path = Path(path) / 'index.html'
        return index_path.exists()
    # For remote URLs, assume available (Playwright will fail if not)
    return True


@pytest.fixture(scope='session')
def browser_context_args(browser_context_args: dict[str, object]) -> dict[str, object]:
    """Configure browser context with viewport and other settings."""
    return {
        **browser_context_args,
        'viewport': {'width': 1280, 'height': 720},
        'ignore_https_errors': True,
    }


@pytest.fixture
def docs_page(page: Page, docs_url: str) -> Page:
    """Provide a page loaded at the documentation root."""
    page.goto(docs_url, wait_until='networkidle')
    return page


# Shared Given step for all scenarios
@given('the dioxide documentation site is available')
def docs_site_available(docs_available: bool, docs_url: str) -> None:
    """Verify the documentation site is accessible.

    This step will fail if the docs haven't been built:
        uv run sphinx-build -b html docs docs/_build/html
    """
    if not docs_available:
        pytest.skip(
            f'Documentation not available at {docs_url}. '
            'Build docs first: uv run sphinx-build -b html docs docs/_build/html'
        )


# Helper functions for step definitions
def measure_load_time(page: Page, url: str, timeout: float = 30000) -> float:
    """Measure page load time in seconds."""
    start = time.time()
    page.goto(url, wait_until='networkidle', timeout=timeout)
    return time.time() - start


def is_in_viewport(page: Page, selector: str) -> bool:
    """Check if an element is visible in the current viewport without scrolling."""
    element = page.query_selector(selector)
    if not element:
        return False

    viewport_size = page.viewport_size
    if not viewport_size:
        return False

    bounding_box = element.bounding_box()
    if not bounding_box:
        return False

    return bool(
        bounding_box['y'] >= 0
        and bounding_box['y'] + bounding_box['height'] <= viewport_size['height']
        and bounding_box['x'] >= 0
        and bounding_box['x'] + bounding_box['width'] <= viewport_size['width']
    )


def count_scroll_lengths_to_element(page: Page, selector: str) -> int:
    """Count how many viewport heights need to be scrolled to see an element.

    Returns 0 if element is in first viewport, 1 if in second, etc.
    """
    element = page.query_selector(selector)
    if not element:
        return -1

    viewport_size = page.viewport_size
    if not viewport_size:
        return -1

    bounding_box = element.bounding_box()
    if not bounding_box:
        return -1

    # Calculate how many viewport heights down the element is
    viewport_height = viewport_size['height']
    element_bottom = bounding_box['y'] + bounding_box['height']

    return int(element_bottom // viewport_height)


def get_code_blocks(page: Page) -> list[ElementHandle]:
    """Find all code blocks on the page."""
    # Sphinx uses different selectors depending on theme and highlighting
    selectors = [
        'pre.highlight',  # Furo theme
        'div.highlight pre',  # Alternative
        'pre code',  # Generic
        '.highlight-python pre',  # Python-specific
        '.highlight pre',  # Generic highlight
    ]

    for selector in selectors:
        elements: list[ElementHandle] = page.query_selector_all(selector)
        if elements:
            return elements

    return []


def has_copy_button(page: Page, code_block: ElementHandle) -> bool:
    """Check if a code block has an associated copy button.

    The sphinx-copybutton extension adds copy buttons to code blocks.
    """
    # sphinx-copybutton adds a button inside the highlight div
    parent = code_block.evaluate('el => el.closest(".highlight")')
    if parent:
        # Check for copy button within the same container
        button = page.query_selector('.highlight button.copybtn')
        return button is not None

    return False
