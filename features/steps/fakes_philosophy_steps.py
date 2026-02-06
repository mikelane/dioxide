"""Step definitions for fakes philosophy documentation verification.

These steps parse the actual documentation files and verify that the fakes
philosophy is convincingly explained with concrete examples, fair comparisons,
and actionable guidance.
"""

from __future__ import annotations

import re
from pathlib import Path

from behave import given, then, when
from behave.runner import Context

DOCS_ROOT = Path(__file__).resolve().parent.parent.parent / 'docs'
TESTING_GUIDE = DOCS_ROOT / 'TESTING_GUIDE.md'
MIGRATION_GUIDE = DOCS_ROOT / 'migration-from-mocks.md'
TESTING_WITH_FAKES_RST = DOCS_ROOT / 'user_guide' / 'testing_with_fakes.rst'


def _read_doc(path: Path) -> str:
    """Read a documentation file and return its contents."""
    if not path.exists():
        return ''
    return path.read_text(encoding='utf-8')


def _count_code_blocks(text: str) -> int:
    """Count fenced code blocks (``` delimited) in markdown text."""
    return len(re.findall(r'```\w*\n', text))


def _extract_sections(text: str, level: int = 2) -> dict[str, str]:
    """Extract sections from markdown by heading level.

    Returns a dict mapping heading text (lowercase) to section content.
    """
    pattern = rf'^{"#" * level}\s+(.+)$'
    sections: dict[str, str] = {}
    current_heading = None
    current_lines: list[str] = []

    for line in text.splitlines():
        match = re.match(pattern, line)
        if match:
            if current_heading is not None:
                sections[current_heading] = '\n'.join(current_lines)
            current_heading = match.group(1).strip().lower()
            current_lines = []
        elif current_heading is not None:
            current_lines.append(line)

    if current_heading is not None:
        sections[current_heading] = '\n'.join(current_lines)

    return sections


def _section_contains_pattern(section_text: str, pattern: str) -> bool:
    """Check if a section contains text matching a case-insensitive pattern."""
    return bool(re.search(pattern, section_text, re.IGNORECASE))


def _count_before_after_pairs(text: str) -> int:
    """Count before/after or mock/fake code example pairs in a section.

    Looks for patterns like:
    - "Before" ... code block ... "After" ... code block
    - "BAD" ... code block ... "GOOD" ... code block
    - "Mock" ... code block ... "Fake" ... code block
    """
    before_patterns = [
        r'(?:before|bad|mock[- ]based|mock approach|with mocks)',
        r'#\s*(?:❌|BAD)',
    ]
    after_patterns = [
        r'(?:after|good|fake[- ]based|fake approach|with fakes|dioxide)',
        r'#\s*(?:✅|GOOD)',
    ]

    before_count = 0
    after_count = 0
    for pat in before_patterns:
        before_count += len(re.findall(pat, text, re.IGNORECASE))
    for pat in after_patterns:
        after_count += len(re.findall(pat, text, re.IGNORECASE))

    return min(before_count, after_count)


# ---------------------------------------------------------------------------
# Scenario: Mock vs Fake comparison exists and is fair
# ---------------------------------------------------------------------------


@given('I navigate to the testing documentation')
def step_navigate_to_testing_docs(context: Context) -> None:
    context.testing_guide = _read_doc(TESTING_GUIDE)
    context.migration_guide = _read_doc(MIGRATION_GUIDE)
    context.all_testing_docs = context.testing_guide + '\n' + context.migration_guide
    assert context.testing_guide or context.migration_guide, (
        f'No testing documentation found at {TESTING_GUIDE} or {MIGRATION_GUIDE}'
    )


@when('I look for mock vs fake comparison')
def step_look_for_comparison(context: Context) -> None:
    docs = context.all_testing_docs
    context.has_comparison = _section_contains_pattern(
        docs, r'(?:mock\s+vs\.?\s+fake|comparison|key\s+differences|problem\s+with\s+mocks)'
    )
    context.comparison_sections = _extract_sections(context.all_testing_docs)


@then('I find a dedicated comparison section')
def step_find_comparison_section(context: Context) -> None:
    comparison_headings = [
        heading
        for heading in context.comparison_sections
        if re.search(
            r'(?:comparison|difference|problem.*mock|mock.*problem|key differences)',
            heading,
            re.IGNORECASE,
        )
    ]
    assert comparison_headings, (
        'No dedicated mock vs fake comparison section found in testing docs. '
        f'Found sections: {list(context.comparison_sections.keys())}'
    )
    context.comparison_section_content = '\n'.join(context.comparison_sections[h] for h in comparison_headings)


@then('the section shows at least 3 concrete problems with mocks')
def step_at_least_3_problems(context: Context) -> None:
    docs = context.all_testing_docs
    problem_indicators = [
        r'tight\s+coupling',
        r'(?:brittle|fragile|break)',
        r'mock[s]?\s+can\s+lie',
        r'false\s+confidence',
        r'unclear.*intent|obscured.*intent',
        r'complex(?:ity)?.*setup|setup.*complex',
        r'patch\s+path\s+fragil',
        r'implementation.*not\s+behavior',
    ]
    found_problems = [pat for pat in problem_indicators if re.search(pat, docs, re.IGNORECASE)]
    assert len(found_problems) >= 3, (
        f'Expected at least 3 concrete problems with mocks documented, '
        f'found {len(found_problems)}. '
        f'Matched: {found_problems}'
    )


@then('each problem has a before mock and after fake code example')
def step_before_after_examples(context: Context) -> None:
    docs = context.all_testing_docs
    pair_count = _count_before_after_pairs(docs)
    assert pair_count >= 3, (
        f'Expected at least 3 before/after (mock vs fake) code example pairs, '
        f'found {pair_count}. '
        'Each documented problem should show a mock example and a fake alternative.'
    )


@then('the comparison acknowledges when mocks are still appropriate')
def step_acknowledges_mocks_appropriate(context: Context) -> None:
    docs = context.all_testing_docs
    acknowledgement_patterns = [
        r'when\s+(?:to\s+)?(?:still\s+)?use\s+mocks',
        r'mocks?\s+(?:still\s+)?have\s+their\s+place',
        r'when\s+mocks?\s+(?:are|is)\s+(?:still\s+)?appropriate',
        r'acceptable.*mock',
        r'rare.*case.*mock',
    ]
    found = any(re.search(pat, docs, re.IGNORECASE) for pat in acknowledgement_patterns)
    assert found, (
        'Documentation does not acknowledge when mocks are still appropriate. '
        'A fair comparison should discuss legitimate mock use cases.'
    )


# ---------------------------------------------------------------------------
# Scenario: Problems with mocks are demonstrated not asserted
# ---------------------------------------------------------------------------


@given('I read the mock problems section')
def step_read_mock_problems(context: Context) -> None:
    context.testing_guide = _read_doc(TESTING_GUIDE)
    context.migration_guide = _read_doc(MIGRATION_GUIDE)
    context.all_testing_docs = context.testing_guide + '\n' + context.migration_guide
    sections = _extract_sections(context.all_testing_docs)
    problem_sections = {
        k: v for k, v in sections.items() if re.search(r'problem.*mock|mock.*problem', k, re.IGNORECASE)
    }
    context.mock_problem_sections = problem_sections
    assert problem_sections, (
        f'No "problems with mocks" section found in testing documentation. Found sections: {list(sections.keys())}'
    )


@when('I examine each problem description')
def step_examine_problems(context: Context) -> None:
    context.problem_content = '\n'.join(context.mock_problem_sections.values())


@then('each includes runnable code showing the problem')
def step_runnable_code(context: Context) -> None:
    content = context.problem_content
    code_block_count = _count_code_blocks(content)
    assert code_block_count >= 3, (
        f'Expected at least 3 code blocks in mock problems section, found {code_block_count}. '
        'Each problem should include runnable code demonstrating the issue.'
    )


@then('the mock examples demonstrate real failure modes')
def step_real_failure_modes(context: Context) -> None:
    content = context.problem_content
    failure_indicators = [
        r'assert_called',
        r'return_value',
        r'side_effect',
        r'@patch',
        r'Mock\(\)',
        r'MagicMock',
    ]
    found = [pat for pat in failure_indicators if re.search(pat, content, re.IGNORECASE)]
    assert len(found) >= 2, (
        f'Mock problem examples should use real mock patterns (assert_called, return_value, etc). Found only: {found}'
    )


@then('the examples are not strawman intentionally bad mock usage')
def step_not_strawman(context: Context) -> None:
    content = context.problem_content
    realistic_indicators = [
        r'(?:service|repository|adapter|controller)',
        r'(?:database|email|payment|api)',
        r'(?:user|order|notification)',
    ]
    found = [pat for pat in realistic_indicators if re.search(pat, content, re.IGNORECASE)]
    assert len(found) >= 2, (
        'Mock problem examples should use realistic domain concepts '
        '(services, repositories, real operations), not trivial strawman examples. '
        f'Found domain concepts: {found}'
    )


# ---------------------------------------------------------------------------
# Scenario: Fakes in production code deployment concern is explained
# ---------------------------------------------------------------------------


@given('I read about fakes in production code')
def step_read_fakes_in_prod(context: Context) -> None:
    context.testing_guide = _read_doc(TESTING_GUIDE)
    context.migration_guide = _read_doc(MIGRATION_GUIDE)
    context.all_testing_docs = context.testing_guide + '\n' + context.migration_guide


@when('I look for deployment concerns')
def step_look_for_deployment(context: Context) -> None:
    docs = context.all_testing_docs
    context.has_deployment_section = _section_contains_pattern(
        docs,
        r'(?:production|deploy|where\s+fakes?\s+live|fakes?\s+in\s+production)',
    )


@then('I find an explanation of how Profile.PRODUCTION excludes fakes')
def step_profile_production_excludes(context: Context) -> None:
    docs = context.all_testing_docs
    found = _section_contains_pattern(docs, r'Profile\.(?:PRODUCTION|TEST)')
    assert found, (
        'Documentation does not explain how Profile.PRODUCTION excludes fakes. '
        'Skeptical developers need to understand that fakes are never activated in production.'
    )


@then('I see that fake code exists but is never instantiated in production')
def step_code_present_not_instantiated(context: Context) -> None:
    docs = context.all_testing_docs
    existence_patterns = [
        r'(?:exist|present|live).*(?:never|not).*(?:instantiat|activat|execut|run)',
        r'(?:never|not).*(?:instantiat|activat|execut|run).*(?:production)',
        r'code\s+present\s+vs\s+code\s+executed',
        r'profile.*(?:exclud|filter|select)',
    ]
    found = any(re.search(pat, docs, re.IGNORECASE) for pat in existence_patterns)
    assert found, (
        'Documentation does not clearly explain that fake code exists in the codebase '
        'but is never instantiated in production. This is the key deployment concern '
        'skeptical developers have.'
    )


@then('I understand the trade-off of code present vs code executed')
def step_tradeoff_explained(context: Context) -> None:
    docs = context.all_testing_docs
    tradeoff_patterns = [
        r'trade[\s-]?off',
        r'(?:why|reason|benefit).*(?:production\s+code|live\s+in)',
        r'(?:reusab|maintain|document)',
    ]
    found = [pat for pat in tradeoff_patterns if re.search(pat, docs, re.IGNORECASE)]
    assert len(found) >= 1, (
        'Documentation does not explain the trade-off of having fake code present '
        'in the codebase. Should address why this is acceptable and what the benefits are.'
    )


# ---------------------------------------------------------------------------
# Scenario: Writing good fakes guide exists
# ---------------------------------------------------------------------------


@given('I want to write my first fake adapter')
def step_want_to_write_fake(context: Context) -> None:
    context.testing_guide = _read_doc(TESTING_GUIDE)
    context.migration_guide = _read_doc(MIGRATION_GUIDE)
    context.fakes_guide = _read_doc(TESTING_WITH_FAKES_RST)
    context.all_guides = context.testing_guide + '\n' + context.migration_guide + '\n' + context.fakes_guide


@when('I search for writing fakes guidance')
def step_search_writing_fakes(context: Context) -> None:
    docs = context.all_guides
    context.has_fakes_guide = _section_contains_pattern(
        docs,
        r'(?:writing|creating|implement).*fake|fake.*(?:pattern|guide|how)',
    )


@then('I find a guide with common patterns')
def step_find_guide_with_patterns(context: Context) -> None:
    docs = context.all_guides
    pattern_indicators = [
        r'(?:pattern|example|recipe|cookbook)',
        r'(?:in[\s-]?memory|simple\s+fake)',
    ]
    found = [pat for pat in pattern_indicators if re.search(pat, docs, re.IGNORECASE)]
    assert found, (
        'No guide with common fake patterns found. Developers need concrete patterns to write their first fakes.'
    )


@then('the guide covers the InMemoryRepository pattern')
def step_covers_in_memory_repo(context: Context) -> None:
    docs = context.all_guides
    found = _section_contains_pattern(
        docs,
        r'(?:in[\s-]?memory|fake.*(?:repository|repo|storage|user))',
    )
    assert found, (
        'Guide does not cover the InMemoryRepository pattern. '
        'This is the most common fake pattern and must be documented.'
    )


@then('the guide covers the FakeClock pattern')
def step_covers_fake_clock(context: Context) -> None:
    docs = context.all_guides
    found = _section_contains_pattern(
        docs,
        r'(?:fake[\s_]?clock|controllable.*(?:time|clock)|clock.*(?:fake|test))',
    )
    assert found, (
        'Guide does not cover the FakeClock pattern. '
        'Time-dependent logic is common and needs a documented testing approach.'
    )


@then('the guide covers the FakeHttpClient pattern')
def step_covers_fake_http(context: Context) -> None:
    docs = context.all_guides
    found = _section_contains_pattern(
        docs,
        r'(?:fake.*(?:http|api|client|weather|external|push|notification|email|payment)|'
        r'(?:http|api|client|external).*fake|'
        r'third[\s-]?party.*(?:api|port|fake)|'
        r'(?:stubbing|faking).*(?:third[\s-]?party|external))',
    )
    assert found, (
        'Guide does not cover the FakeHttpClient pattern (or equivalent external API fake). '
        'Testing against external APIs is a key concern and must be addressed.'
    )


# ---------------------------------------------------------------------------
# Scenario: Migration from mocks to fakes is documented
# ---------------------------------------------------------------------------


@given('I have an existing codebase using mocks')
def step_have_codebase_with_mocks(context: Context) -> None:
    context.migration_guide = _read_doc(MIGRATION_GUIDE)
    context.testing_guide = _read_doc(TESTING_GUIDE)
    context.all_migration_docs = context.migration_guide + '\n' + context.testing_guide


@when('I search for migration guidance')
def step_search_migration(context: Context) -> None:
    context.has_migration_guide = bool(context.migration_guide)


@then('I find a step-by-step migration guide')
def step_find_step_by_step(context: Context) -> None:
    docs = context.all_migration_docs
    step_patterns = [
        r'step\s+\d',
        r'(?:first|second|third|next).*(?:step|phase)',
        r'(?:identify|create|update|replace|convert)',
    ]
    found = [pat for pat in step_patterns if re.search(pat, docs, re.IGNORECASE)]
    assert len(found) >= 2, (
        f'Migration guide does not provide clear step-by-step instructions. Found step indicators: {found}'
    )


@then('the guide shows before mock and after fake test code')
def step_before_after_migration(context: Context) -> None:
    docs = context.all_migration_docs
    pair_count = _count_before_after_pairs(docs)
    assert pair_count >= 2, (
        f'Migration guide should show at least 2 before/after code pairs, found {pair_count}. '
        'Developers need to see concrete transformations from mocks to fakes.'
    )


@then('the migration is incremental not all-or-nothing')
def step_incremental_migration(context: Context) -> None:
    docs = context.all_migration_docs
    incremental_patterns = [
        r'incremental',
        r'one\s+(?:at\s+a\s+time|file|test|module)',
        r'gradual',
        r'start\s+(?:small|with)',
        r'priorit',
        r'don\'?t\s+have\s+to.*all\s+at\s+once',
    ]
    found = [pat for pat in incremental_patterns if re.search(pat, docs, re.IGNORECASE)]
    assert found, (
        'Migration guide does not mention incremental migration. '
        'Expecting developers to rewrite all tests at once is unrealistic. '
        'The guide should emphasize gradual adoption.'
    )


# ---------------------------------------------------------------------------
# Scenario: FAQ addresses common skepticism
# ---------------------------------------------------------------------------


@given('I have doubts about the fakes approach')
def step_have_doubts(context: Context) -> None:
    context.testing_guide = _read_doc(TESTING_GUIDE)
    context.migration_guide = _read_doc(MIGRATION_GUIDE)
    context.all_faq_docs = context.testing_guide + '\n' + context.migration_guide


@when('I look at the FAQ section')
def step_look_at_faq(context: Context) -> None:
    sections = _extract_sections(context.all_faq_docs)
    faq_sections = {k: v for k, v in sections.items() if 'faq' in k.lower()}
    context.faq_content = '\n'.join(faq_sections.values()) if faq_sections else ''
    context.all_faq_docs_text = context.all_faq_docs


@then('I find an answer for "Why not just use @patch?"')
def step_why_not_patch(context: Context) -> None:
    docs = context.all_faq_docs_text
    found = _section_contains_pattern(
        docs,
        r'why\s+not\s+(?:just\s+)?use\s+[`"\']*@?patch',
    )
    assert found, (
        'FAQ does not address "Why not just use @patch?" '
        'This is the most common question from experienced Python developers.'
    )


@then('I find an answer for "Don\'t fakes require more work?"')
def step_fakes_more_work(context: Context) -> None:
    docs = context.all_faq_docs_text
    work_patterns = [
        r'(?:fakes?|creating).*(?:more\s+work|seem.*more|require.*more)',
        r'more\s+(?:work|effort)',
        r'(?:initially|upfront).*yes',
        r'reusab',
    ]
    found = [pat for pat in work_patterns if re.search(pat, docs, re.IGNORECASE)]
    assert found, (
        'FAQ does not address the concern that fakes require more work than mocks. '
        'This is a primary objection from developers evaluating the approach.'
    )


@then('I find an answer for "What about external APIs I can\'t fake?"')
def step_external_apis(context: Context) -> None:
    docs = context.all_faq_docs_text
    external_patterns = [
        r'(?:external|third[\s-]?party).*(?:api|service|library)',
        r'(?:api|service|library).*(?:don\'?t|can\'?t|cannot)\s+control',
        r'stubbing\s+third[\s-]?party',
        r'what\s+about.*(?:external|third)',
    ]
    found = [pat for pat in external_patterns if re.search(pat, docs, re.IGNORECASE)]
    assert found, (
        'FAQ does not address how to handle external APIs that cannot be faked directly. '
        'This is a common practical concern for developers with real-world integrations.'
    )


@then('each answer is substantive not dismissive')
def step_substantive_answers(context: Context) -> None:
    faq_content = context.faq_content or context.all_faq_docs_text
    code_blocks_in_faq = _count_code_blocks(faq_content)
    assert code_blocks_in_faq >= 3, (
        f'FAQ answers should include code examples to be substantive. '
        f'Found {code_blocks_in_faq} code blocks. '
        'Answers should demonstrate, not just assert.'
    )
    faq_word_count = len(faq_content.split())
    assert faq_word_count >= 200, (
        f'FAQ section has only {faq_word_count} words. '
        'Substantive answers require enough depth to address skepticism meaningfully.'
    )
