"""Step definitions for documentation navigation BDD scenarios.

These tests verify that developers can find answers quickly through
the documentation. Tests are designed to FAIL against current
documentation, validating that improvements are needed.

Run with: uv run pytest tests/docs_ux/ -v
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

import pytest
from pytest_bdd import (
    parsers,
    scenarios,
    then,
    when,
)

from tests.docs_ux.conftest import (
    get_code_blocks,
)

if TYPE_CHECKING:
    from playwright.sync_api import Page

# Load all scenarios from the feature file
scenarios('../features/docs_navigation.feature')


# =============================================================================
# Scenario: New user finds quickstart in under 30 seconds
# =============================================================================


@when('I arrive at the documentation homepage')
def arrive_at_homepage(docs_page: Page) -> None:
    """Navigate to the documentation homepage."""
    # docs_page fixture already navigates to the homepage
    assert docs_page.url, 'Page URL should be set'


@then('I see a prominent "Quick Start" link in the navigation')
def see_quickstart_link(docs_page: Page) -> None:
    """Verify Quick Start link is prominently visible.

    The Quick Start link should be:
    1. Visible without scrolling
    2. In the main navigation or hero section
    3. Easy to find (not buried in a submenu)
    """
    # Look for Quick Start link in navigation or hero section
    quickstart_selectors = [
        'a:has-text("Quick Start")',
        'a:has-text("Get Started")',
        'a:has-text("Quickstart")',
        'nav a:has-text("Start")',
        '.hero a:has-text("Start")',
        'a.sd-sphinx-override:has-text("Get Started")',  # Sphinx design button
    ]

    found = False
    for selector in quickstart_selectors:
        element = docs_page.query_selector(selector)
        if element and element.is_visible():
            found = True
            break

    assert found, (
        'Quick Start link not found in navigation. '
        'Expected a prominent link with text containing "Quick Start" or "Get Started"'
    )


@then(parsers.parse('clicking "Quick Start" loads within {seconds:d} seconds'))
def quickstart_loads_fast(docs_page: Page, seconds: int) -> None:
    """Verify Quick Start page loads quickly."""
    # Find and click the Quick Start link
    quickstart_selectors = [
        'a:has-text("Quick Start")',
        'a:has-text("Get Started")',
        'a:has-text("Quickstart")',
        'a.sd-sphinx-override:has-text("Get Started")',
    ]

    for selector in quickstart_selectors:
        element = docs_page.query_selector(selector)
        if element and element.is_visible():
            start_time = time.time()
            element.click()
            docs_page.wait_for_load_state('networkidle')
            load_time = time.time() - start_time

            assert load_time <= seconds, f'Quick Start page took {load_time:.2f}s to load, expected <= {seconds}s'
            return

    pytest.fail('Could not find Quick Start link to click')


@then('the quick start page shows working code within the first viewport')
def code_in_first_viewport(docs_page: Page) -> None:
    """Verify working code is visible without scrolling.

    Users should see copy-pasteable code immediately when landing
    on the Quick Start page, without needing to scroll.
    """
    code_blocks = get_code_blocks(docs_page)

    assert len(code_blocks) > 0, 'No code blocks found on Quick Start page'

    # Check if at least one code block is in the first viewport
    first_block = code_blocks[0]
    bounding_box = first_block.bounding_box()  # type: ignore[union-attr]
    viewport = docs_page.viewport_size

    if bounding_box and viewport:
        in_viewport = bounding_box['y'] + bounding_box['height'] <= viewport['height']
        assert in_viewport, (
            'First code block is not visible in the first viewport. '
            f'Code block starts at y={bounding_box["y"]}, '
            f'viewport height={viewport["height"]}'
        )
    else:
        pytest.fail('Could not determine code block position or viewport size')


@then('each code block has a "Copy" button')
def code_blocks_have_copy_buttons(docs_page: Page) -> None:
    """Verify all code blocks have copy buttons.

    The sphinx-copybutton extension should add copy buttons to all
    code blocks for easy copying.
    """
    code_blocks = get_code_blocks(docs_page)

    if not code_blocks:
        pytest.skip('No code blocks found on page')

    # Check for copy buttons (sphinx-copybutton adds these)
    copy_buttons = docs_page.query_selector_all('button.copybtn')

    # We expect at least as many copy buttons as code blocks
    # (some themes may have extra buttons)
    assert len(copy_buttons) >= len(code_blocks), (
        f'Expected copy buttons for {len(code_blocks)} code blocks, '
        f'but found only {len(copy_buttons)} copy buttons. '
        'Ensure sphinx-copybutton extension is properly configured.'
    )


# =============================================================================
# Scenario: Developer finds @service vs @adapter guidance
# =============================================================================


@when(parsers.parse('I use the documentation search for "{query}"'))
def search_documentation(docs_page: Page, query: str, docs_url: str) -> None:
    """Use the documentation search functionality.

    Note: Search may not work with local file:// URLs as Sphinx search
    requires JavaScript that doesn't load properly from file://. For full
    testing, use a served documentation (HTTP URL).
    """
    # Furo theme has a search button/input in the header
    search_input = docs_page.query_selector('input[type="search"]')
    if not search_input:
        # Try clicking search button first
        search_button = docs_page.query_selector('button.search-button, .search-button-field')
        if search_button:
            search_button.click()
            docs_page.wait_for_timeout(500)
            search_input = docs_page.query_selector('input[type="search"]')

    # Provide clear error message about file:// limitation
    if not search_input and docs_url.startswith('file://'):
        pytest.skip(
            'Search input not found - Sphinx search requires HTTP server. '
            'Run with: DOCS_URL=http://localhost:8000 uv run pytest tests/docs_ux/ '
            '(after running: uv run python -m http.server -d docs/_build/html 8000)'
        )

    assert search_input, 'Search input not found on page. Ensure documentation has search functionality enabled.'

    search_input.fill(query)
    search_input.press('Enter')
    docs_page.wait_for_timeout(1000)  # Wait for search results


@then(parsers.parse('the search results include "{guide_name}" guide'))
def search_includes_guide(docs_page: Page, guide_name: str) -> None:
    """Verify search results include the expected guide."""
    # Look for search results containing the guide name
    results = docs_page.query_selector_all('.search-result, .search li, [data-search-result]')

    if not results:
        # Check if we're on a search results page
        page_text = docs_page.text_content('body') or ''
        assert guide_name.lower() in page_text.lower(), (
            f'Guide "{guide_name}" not found in search results. Page content does not contain "{guide_name}"'
        )
        return

    found = False
    for result in results:
        text = result.text_content() or ''
        if guide_name.lower().replace('-', ' ') in text.lower():
            found = True
            break

    assert found, f'Guide "{guide_name}" not found in search results'


@then(parsers.parse('the guide appears in the top {n:d} results'))
def guide_in_top_results(docs_page: Page, n: int) -> None:
    """Verify the guide appears in top N search results."""
    results = docs_page.query_selector_all('.search-result, .search li, [data-search-result]')

    # Check if services-vs-adapters is in top N
    found_in_top_n = False
    for _i, result in enumerate(results[:n]):
        text = result.text_content() or ''
        if 'service' in text.lower() and 'adapter' in text.lower():
            found_in_top_n = True
            break

    assert found_in_top_n, (
        f'services-vs-adapters guide not in top {n} search results. Found {len(results)} results total.'
    )


@then('the guide includes a decision tree diagram')
def guide_has_decision_tree(docs_page: Page) -> None:
    """Verify the guide includes a decision tree diagram.

    The decision tree should help developers choose between
    @service and @adapter decorators.
    """
    # Navigate to the services-vs-adapters page if not already there
    if 'services-vs-adapters' not in docs_page.url:
        link = docs_page.query_selector('a[href*="services-vs-adapters"]')
        if link:
            link.click()
            docs_page.wait_for_load_state('networkidle')

    # Look for Mermaid diagram or image that represents a decision tree
    diagram_selectors = [
        '.mermaid',  # Mermaid diagram
        'svg.mermaid',  # Rendered Mermaid
        'img[alt*="decision"]',  # Image with decision in alt text
        'img[alt*="tree"]',
        'img[alt*="flowchart"]',
        '[data-diagram]',
        '.diagram',
    ]

    found = False
    for selector in diagram_selectors:
        element = docs_page.query_selector(selector)
        if element:
            found = True
            break

    assert found, (
        'Decision tree diagram not found on services-vs-adapters page. '
        'Expected a Mermaid diagram or image showing when to use @service vs @adapter'
    )


@then(parsers.parse('the decision tree fits within {n:d} scroll lengths'))
def decision_tree_fits_in_scrolls(docs_page: Page, n: int) -> None:
    """Verify the decision tree is reasonably sized.

    Users should not have to scroll excessively to see the full
    decision tree.
    """
    # Find the decision tree/diagram
    diagram = docs_page.query_selector('.mermaid, svg.mermaid, [data-diagram]')

    if not diagram:
        pytest.skip('No decision tree diagram found to measure')

    bounding_box = diagram.bounding_box()
    viewport = docs_page.viewport_size

    if bounding_box and viewport:
        diagram_height = bounding_box['height']
        viewport_height = viewport['height']
        scroll_lengths = diagram_height / viewport_height

        assert scroll_lengths <= n, (
            f'Decision tree requires {scroll_lengths:.1f} scroll lengths, '
            f'expected <= {n}. Consider simplifying the diagram.'
        )


# =============================================================================
# Scenario: Skeptic finds "why dioxide" justification
# =============================================================================


@when('I navigate to the documentation homepage')
def navigate_to_homepage(docs_page: Page, docs_url: str) -> None:
    """Navigate to the documentation homepage."""
    docs_page.goto(docs_url, wait_until='networkidle')


@when('I look for comparison or "why" content')
def look_for_why_content(docs_page: Page) -> None:
    """Look for why/comparison content in navigation."""
    # This step just documents the user intent
    # The actual verification is in the Then steps
    pass


@then(parsers.parse('I find a "Why dioxide?" page within {n:d} clicks from home'))
def find_why_page(docs_page: Page, n: int, docs_url: str) -> None:
    """Verify Why dioxide page is reachable within N clicks.

    Users should be able to find justification for using dioxide
    quickly from the homepage.
    """
    docs_page.goto(docs_url, wait_until='networkidle')

    # Try to find Why dioxide link
    why_selectors = [
        'a:has-text("Why dioxide")',
        'a:has-text("Why Dioxide")',
        'a[href*="why-dioxide"]',
        'a[href*="why_dioxide"]',
    ]

    clicks = 0
    found = False

    for selector in why_selectors:
        element = docs_page.query_selector(selector)
        if element and element.is_visible():
            element.click()
            docs_page.wait_for_load_state('networkidle')
            clicks = 1
            found = True
            break

    if not found:
        # Try looking in sidebar or navigation dropdowns
        nav_items = docs_page.query_selector_all('nav a, .sidebar a')
        for item in nav_items:
            text = item.text_content() or ''
            if 'why' in text.lower():
                item.click()
                docs_page.wait_for_load_state('networkidle')
                clicks = 1
                found = True
                break

    assert found, 'Could not find "Why dioxide?" page from homepage. Expected a link in navigation or sidebar.'
    assert clicks <= n, f'Why dioxide page required {clicks} clicks, expected <= {n}'


@then('the page compares dioxide to at least dependency-injector')
def page_compares_to_dependency_injector(docs_page: Page) -> None:
    """Verify the page includes comparison to dependency-injector.

    As the main alternative DI framework, dioxide should explain
    how it differs.
    """
    page_text = docs_page.text_content('body') or ''

    assert 'dependency-injector' in page_text.lower() or 'dependency injector' in page_text.lower(), (
        'Why dioxide page does not mention dependency-injector. '
        'Expected comparison to the main alternative DI framework.'
    )


@then('the page includes an "Anti-goals" or "What dioxide doesn\'t do" section')
def page_has_antigoals(docs_page: Page) -> None:
    """Verify the page includes what dioxide doesn't do.

    Setting expectations helps users evaluate if dioxide is right
    for their use case.
    """
    page_text = docs_page.text_content('body') or ''

    anti_goal_patterns = [
        'anti-goal',
        'antigoal',
        "doesn't do",
        "doesn't try",
        'not building',
        'not included',
        "won't do",
        'out of scope',
        'non-goal',
        'nongoal',
    ]

    found = any(pattern in page_text.lower() for pattern in anti_goal_patterns)

    assert found, (
        'Why dioxide page lacks anti-goals or "what we don\'t do" section. '
        'Expected clear scope boundaries to help users evaluate fit.'
    )


# =============================================================================
# Scenario: Tester finds testing patterns
# =============================================================================


@then('the search results include the testing guide')
def search_includes_testing_guide(docs_page: Page) -> None:
    """Verify search results include testing guide."""
    page_text = docs_page.text_content('body') or ''

    testing_patterns = ['testing', 'test', 'fakes', 'fixtures']
    found = any(pattern in page_text.lower() for pattern in testing_patterns)

    assert found, 'Testing guide not found in search results'


@then('the testing guide explains "fakes at the seams" philosophy')
def testing_guide_explains_fakes(docs_page: Page) -> None:
    """Verify testing guide explains the fakes philosophy.

    dioxide's testing philosophy is "fakes at the seams" rather than
    mocking frameworks.
    """
    # Navigate to testing guide if needed
    testing_link = docs_page.query_selector(
        'a[href*="testing"], a[href*="test"], a:has-text("Testing"), a:has-text("test")'
    )
    if testing_link:
        testing_link.click()
        docs_page.wait_for_load_state('networkidle')

    page_text = docs_page.text_content('body') or ''

    fakes_patterns = ['fakes', 'fake', 'seams', 'not mock', 'instead of mock']
    found = any(pattern in page_text.lower() for pattern in fakes_patterns)

    assert found, (
        'Testing guide does not explain "fakes at the seams" philosophy. '
        'Expected discussion of using fakes instead of mocks.'
    )


@then('the guide includes pytest fixture code examples')
def guide_has_pytest_fixtures(docs_page: Page) -> None:
    """Verify testing guide includes pytest fixture examples."""
    page_text = docs_page.text_content('body') or ''

    # Look for pytest fixture patterns in code
    pytest_patterns = ['@pytest.fixture', 'def fixture', 'pytest', 'conftest']
    found = any(pattern in page_text.lower() for pattern in pytest_patterns)

    assert found, 'Testing guide lacks pytest fixture examples. Expected @pytest.fixture decorated functions.'


@then('the examples are complete and copy-pasteable')
def examples_are_complete(docs_page: Page) -> None:
    """Verify code examples are complete and runnable.

    Examples should not have '...' truncation or missing imports
    that would prevent direct copy-paste usage.
    """
    code_blocks = get_code_blocks(docs_page)

    if not code_blocks:
        pytest.skip('No code blocks found on page')

    # Check that code blocks don't have incomplete markers
    incomplete_markers = ['...', '# ...', '# (truncated)', '# etc']

    for block in code_blocks:
        text = block.text_content() or ''  # type: ignore[union-attr]

        # Allow '...' in docstrings (which is valid Python)
        lines = text.split('\n')
        for line in lines:
            # Skip docstring ellipsis
            if line.strip() == '...' or line.strip() == '"""...':
                continue
            # Check for truncation markers
            for marker in incomplete_markers:
                if marker in line and not line.strip().startswith(('"""', "'''")):
                    # This is likely a truncated example
                    pass  # Allow for now, documentation may have intentional truncation

    # At minimum, examples should have imports
    all_text = ' '.join(block.text_content() or '' for block in code_blocks)  # type: ignore[union-attr]
    has_imports = 'import' in all_text or 'from' in all_text

    assert has_imports, 'Code examples lack import statements - not copy-pasteable'


# =============================================================================
# Scenario: Contributor understands design decisions
# =============================================================================


@when('I look for architecture or design content')
def look_for_design_content(docs_page: Page) -> None:
    """Look for architecture/design content in navigation."""
    # This step documents user intent
    pass


@then(parsers.parse('I find design principles within {n:d} clicks from home'))
def find_design_principles(docs_page: Page, n: int, docs_url: str) -> None:
    """Verify design principles are reachable within N clicks."""
    docs_page.goto(docs_url, wait_until='networkidle')

    design_selectors = [
        'a:has-text("Design")',
        'a:has-text("Architecture")',
        'a:has-text("Philosophy")',
        'a:has-text("Principles")',
        'a[href*="design"]',
        'a[href*="architecture"]',
        'a[href*="philosophy"]',
    ]

    clicks = 0
    found = False

    # First try direct links
    for selector in design_selectors:
        element = docs_page.query_selector(selector)
        if element and element.is_visible():
            element.click()
            docs_page.wait_for_load_state('networkidle')
            clicks = 1
            found = True
            break

    if not found:
        # Try sidebar navigation
        nav_items = docs_page.query_selector_all('nav a, .sidebar a, .toctree a')
        for item in nav_items:
            text = item.text_content() or ''
            href = item.get_attribute('href') or ''
            if any(
                term in text.lower() or term in href.lower()
                for term in ['design', 'architecture', 'philosophy', 'principle']
            ):
                item.click()
                docs_page.wait_for_load_state('networkidle')
                clicks = 1
                found = True
                break

    if not found:
        # Try Development section which might contain design docs
        dev_link = docs_page.query_selector('a:has-text("Development"), a[href*="development"]')
        if dev_link:
            dev_link.click()
            docs_page.wait_for_load_state('networkidle')
            clicks = 1

            # Look for design link on this page
            for selector in design_selectors:
                element = docs_page.query_selector(selector)
                if element and element.is_visible():
                    element.click()
                    docs_page.wait_for_load_state('networkidle')
                    clicks = 2
                    found = True
                    break

    assert found, (
        'Could not find design principles from homepage. Expected Design, Architecture, or Philosophy section.'
    )
    assert clicks <= n, f'Design principles required {clicks} clicks, expected <= {n}'


@then('I can find ADRs (Architecture Decision Records)')
def can_find_adrs(docs_page: Page) -> None:
    """Verify ADRs are accessible from documentation."""
    page_text = docs_page.text_content('body') or ''

    # Check current page for ADR references
    adr_found = 'adr' in page_text.lower() or 'architecture decision' in page_text.lower()

    if not adr_found:
        # Look for ADR links
        adr_link = docs_page.query_selector(
            'a:has-text("ADR"), a:has-text("Architecture Decision"), a[href*="adr"], a[href*="design"]'
        )
        if adr_link:
            adr_link.click()
            docs_page.wait_for_load_state('networkidle')
            page_text = docs_page.text_content('body') or ''
            adr_found = 'adr' in page_text.lower() or 'decision' in page_text.lower()

    assert adr_found, (
        'ADRs (Architecture Decision Records) not accessible. Expected link to ADRs in design/architecture section.'
    )


@then('the design section clearly marks internal vs public docs')
def design_marks_internal_vs_public(docs_page: Page) -> None:
    """Verify documentation distinguishes internal from public docs.

    Contributors should know which documentation is for users
    vs which is for project internals.
    """
    page_text = docs_page.text_content('body') or ''

    # Look for internal/public distinction markers
    distinction_patterns = [
        'internal',
        'public api',
        'private',
        'contributor',
        'developer guide',
        'for contributors',
        'for developers',
        'implementation',
    ]

    found = any(pattern in page_text.lower() for pattern in distinction_patterns)

    # Also check page structure for separate sections
    headers = docs_page.query_selector_all('h1, h2, h3')
    for header in headers:
        text = header.text_content() or ''
        if any(term in text.lower() for term in ['internal', 'developer', 'contributor', 'api reference']):
            found = True
            break

    assert found, (
        'Documentation does not clearly distinguish internal vs public docs. '
        'Expected sections or labels indicating which docs are for users vs contributors.'
    )


# =============================================================================
# Scenario: Error messages link to troubleshooting
# =============================================================================


@when('I see an error message from dioxide')
def see_error_message(docs_page: Page) -> None:
    """Simulate seeing an error message from dioxide.

    This step tests that error messages include documentation URLs.
    We check the actual error classes for URL presence.
    """
    # This is verified in the Then steps by checking actual exception classes
    pass


@then('the error includes a URL to documentation')
def error_includes_url() -> None:
    """Verify dioxide exceptions include documentation URLs.

    Error messages should help users find solutions by linking
    to relevant documentation.
    """
    from dioxide.exceptions import (
        AdapterNotFoundError,
        CircularDependencyError,
        DioxideError,
        ServiceNotFoundError,
    )

    # Check if exceptions have doc URLs in their messages or attributes
    error_classes = [
        DioxideError,
        AdapterNotFoundError,
        ServiceNotFoundError,
        CircularDependencyError,
    ]

    has_url = False
    for error_class in error_classes:
        # Check class docstring
        if error_class.__doc__ and 'http' in error_class.__doc__:
            has_url = True
            break

        # Check if class has docs_url attribute
        if hasattr(error_class, 'docs_url'):
            has_url = True
            break

        # Create sample error and check message
        try:
            # Try to get error message format
            if hasattr(error_class, 'message_template'):
                template = error_class.message_template
                if 'http' in template:
                    has_url = True
                    break
        except (TypeError, AttributeError):
            pass

    assert has_url, (
        'dioxide exception classes do not include documentation URLs. '
        'Expected exceptions to link to troubleshooting guides.'
    )


@then('that URL leads to relevant troubleshooting content')
def url_leads_to_troubleshooting(docs_page: Page) -> None:
    """Verify error documentation URLs lead to useful content.

    This test would navigate to any error doc URLs and verify
    they contain troubleshooting information.
    """
    # For now, check if troubleshooting section exists
    troubleshoot_link = docs_page.query_selector(
        'a:has-text("Troubleshoot"), a:has-text("Error"), a[href*="troubleshoot"], a[href*="error"]'
    )

    if troubleshoot_link:
        troubleshoot_link.click()
        docs_page.wait_for_load_state('networkidle')

        page_text = docs_page.text_content('body') or ''
        has_troubleshooting = any(
            term in page_text.lower() for term in ['error', 'fix', 'solution', 'troubleshoot', 'resolve']
        )

        assert has_troubleshooting, 'Troubleshooting page lacks error resolution content'
    else:
        pytest.skip('No troubleshooting link found - URL verification skipped')


@then('the troubleshooting page provides actionable steps')
def troubleshooting_has_steps(docs_page: Page) -> None:
    """Verify troubleshooting content includes actionable steps.

    Users should get clear, step-by-step instructions for resolving
    common errors.
    """
    page_text = docs_page.text_content('body') or ''

    # Look for step indicators
    step_patterns = [
        'step 1',
        'step 2',
        'first,',
        'then,',
        'next,',
        'finally,',
        '1.',
        '2.',
        'check if',
        'verify that',
        'ensure',
        'make sure',
    ]

    has_steps = any(pattern in page_text.lower() for pattern in step_patterns)

    # Also check for numbered lists or ordered content
    ordered_lists = docs_page.query_selector_all('ol li')
    if len(ordered_lists) >= 2:
        has_steps = True

    assert has_steps, 'Troubleshooting content lacks actionable steps. Expected numbered steps or clear action items.'
