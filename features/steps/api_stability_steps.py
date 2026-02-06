"""Step definitions for API stability and migration support tests."""

from __future__ import annotations

import re
import warnings
from pathlib import Path

from behave import given, then, when
from behave.runner import Context

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DOCS_DIR = PROJECT_ROOT / 'docs'


# ---------------------------------------------------------------------------
# Scenario: v2.0 migration guide exists and is complete
# ---------------------------------------------------------------------------


@given('I search for migration documentation')
def step_search_for_migration_docs(context: Context) -> None:
    """Search the docs directory for migration-related files."""
    context.migration_files = sorted(DOCS_DIR.rglob('*migration*v2*'))
    context.all_migration_files = sorted(DOCS_DIR.rglob('*migration*'))


@when('I find the v1.x to v2.0 migration guide')
def step_find_v2_migration_guide(context: Context) -> None:
    """Locate the specific v1-to-v2 migration guide."""
    v2_candidates = [
        f for f in context.all_migration_files if 'v2' in f.name or 'v1-to-v2' in f.name or '1-to-2' in f.name
    ]
    # Also check for a general migration guide that covers v2
    general_candidates = [
        f for f in context.all_migration_files if f.suffix in {'.md', '.rst'} and '_build' not in str(f)
    ]

    context.v2_migration_guide = None
    for candidate in v2_candidates + general_candidates:
        if candidate.is_file() and '_build' not in str(candidate):
            content = candidate.read_text()
            if '2.0' in content or 'v2' in content.lower():
                context.v2_migration_guide = candidate
                context.migration_content = content
                break

    assert context.v2_migration_guide is not None, (
        'No v1.x to v2.0 migration guide found in docs/. Expected a file like docs/migration-v1-to-v2.md'
    )


@then('the guide acknowledges the breaking change')
def step_guide_acknowledges_breaking_change(context: Context) -> None:
    """Verify the migration guide mentions breaking changes."""
    content_lower = context.migration_content.lower()
    assert any(phrase in content_lower for phrase in ['breaking change', 'breaking', 'incompatible', 'renamed']), (
        f'Migration guide at {context.v2_migration_guide} does not acknowledge '
        "breaking changes. Expected mentions of 'breaking change', "
        "'incompatible', or 'renamed'."
    )


@then('the guide lists all breaking changes itemized')
def step_guide_lists_breaking_changes(context: Context) -> None:
    """Verify breaking changes are listed as distinct items."""
    content = context.migration_content
    # Look for list markers (markdown or rst) near breaking-change content
    lines = content.split('\n')
    breaking_items = [
        line
        for line in lines
        if line.strip().startswith(('- ', '* ', '1.', '2.', '3.'))
        and any(
            kw in line.lower()
            for kw in [
                'profile',
                'import',
                'rename',
                'rivet',
                'dioxide',
                'broken',
                'removed',
                'changed',
                'str(',
                '.value',
                '.name',
            ]
        )
    ]
    assert len(breaking_items) >= 1, (
        f'Migration guide at {context.v2_migration_guide} does not list '
        'breaking changes as itemized entries. Expected bullet points or '
        'numbered items describing specific changes.'
    )


@then('each breaking change has before/after code examples')
def step_breaking_changes_have_code_examples(context: Context) -> None:
    """Verify code examples showing old vs new patterns."""
    content = context.migration_content
    has_code_blocks = '```' in content or '.. code-block::' in content
    has_before_after = any(
        marker in content.lower() for marker in ['before', 'after', 'old', 'new', 'was:', 'now:', 'instead']
    )
    assert has_code_blocks, (
        f'Migration guide at {context.v2_migration_guide} has no code examples. '
        'Expected fenced code blocks (```) or rst code-block directives.'
    )
    assert has_before_after, (
        f'Migration guide at {context.v2_migration_guide} has code blocks but '
        "no before/after framing. Expected words like 'before', 'after', "
        "'old', 'new' to frame migration examples."
    )


@then('the guide includes find-replace patterns or codemod instructions')
def step_guide_has_find_replace_or_codemod(context: Context) -> None:
    """Verify migration tooling or patterns are documented."""
    content_lower = context.migration_content.lower()
    has_tooling = any(
        phrase in content_lower
        for phrase in [
            'find',
            'replace',
            'search',
            'sed ',
            'codemod',
            'automated',
            'regex',
            'pattern',
        ]
    )
    assert has_tooling, (
        f'Migration guide at {context.v2_migration_guide} does not include '
        'find-replace patterns or codemod instructions. Developers need '
        'actionable migration tooling.'
    )


# ---------------------------------------------------------------------------
# Scenario: API stability policy is documented
# ---------------------------------------------------------------------------


@given('I navigate to the documentation directory')
def step_navigate_to_docs(context: Context) -> None:
    """Verify the docs directory exists."""
    assert DOCS_DIR.is_dir(), f'Documentation directory not found at {DOCS_DIR}'
    context.docs_dir = DOCS_DIR


@when('I look for stability or versioning information')
def step_look_for_stability_info(context: Context) -> None:
    """Search for an API stability policy document."""
    stability_patterns = [
        'stability*',
        'api-stability*',
        'api_stability*',
        'versioning-policy*',
        'compatibility*',
    ]
    context.stability_files = []
    for pattern in stability_patterns:
        context.stability_files.extend(f for f in DOCS_DIR.rglob(pattern) if '_build' not in str(f))


@then('I find an API stability policy document')
def step_find_stability_policy(context: Context) -> None:
    """Verify a stability policy document exists."""
    assert len(context.stability_files) > 0, (
        'No API stability policy document found in docs/. '
        'Expected a file like docs/api-stability.md or docs/stability-policy.md'
    )
    context.stability_doc = context.stability_files[0]
    context.stability_content = context.stability_doc.read_text()


@then('it explains the semantic versioning commitment')
def step_explains_semver(context: Context) -> None:
    """Verify the stability policy explains semver."""
    content_lower = context.stability_content.lower()
    assert any(phrase in content_lower for phrase in ['semantic versioning', 'semver', 'major.minor.patch']), (
        f'Stability policy at {context.stability_doc} does not explain semantic versioning commitment.'
    )


@then('it lists which APIs are stable versus internal')
def step_lists_stable_vs_internal(context: Context) -> None:
    """Verify the policy distinguishes stable from internal APIs."""
    content_lower = context.stability_content.lower()
    has_stable_section = any(phrase in content_lower for phrase in ['stable', 'public api', 'public interface'])
    has_internal_section = any(
        phrase in content_lower for phrase in ['internal', 'private', 'unstable', 'no guarantee']
    )
    assert has_stable_section and has_internal_section, (
        f'Stability policy at {context.stability_doc} does not clearly '
        'distinguish stable (public) APIs from internal (private) APIs.'
    )


@then('it explains the deprecation process')
def step_explains_deprecation_process(context: Context) -> None:
    """Verify the policy explains how deprecation works."""
    content_lower = context.stability_content.lower()
    assert any(
        phrase in content_lower
        for phrase in [
            'deprecat',
            'removal',
            'sunset',
            'end of life',
            'migration period',
        ]
    ), f'Stability policy at {context.stability_doc} does not explain the deprecation process.'


# ---------------------------------------------------------------------------
# Scenario: Stable APIs are clearly marked in documentation
# ---------------------------------------------------------------------------


@given('I read the API reference documentation')
def step_read_api_reference(context: Context) -> None:
    """Locate API reference documentation."""
    api_dir = DOCS_DIR / 'api'
    api_files = sorted(api_dir.rglob('*.md')) + sorted(api_dir.rglob('*.rst'))
    # Also check top-level docs for API reference
    top_level_api = [f for f in DOCS_DIR.glob('api*') if f.suffix in {'.md', '.rst'} and '_build' not in str(f)]
    context.api_files = [f for f in api_files + top_level_api if '_build' not in str(f)]
    context.api_content = {}
    for f in context.api_files:
        context.api_content[f.name] = f.read_text()


@when('I look at a public API like Container or adapter')
def step_look_at_public_api(context: Context) -> None:
    """Search API docs for public API stability markings."""
    context.public_api_mentions = {}
    for filename, content in context.api_content.items():
        content_lower = content.lower()
        if 'container' in content_lower or 'adapter' in content_lower:
            context.public_api_mentions[filename] = content


@then('it is marked as stable or has no instability warning')
def step_public_api_marked_stable(context: Context) -> None:
    """Verify public APIs are marked stable or have no instability warning."""
    assert len(context.public_api_mentions) > 0, (
        'No API documentation found that mentions Container or adapter. '
        'API reference docs should document public APIs with stability markers.'
    )
    for filename, content in context.public_api_mentions.items():
        content_lower = content.lower()
        has_unstable_warning = any(
            phrase in content_lower
            for phrase in [
                'unstable',
                'experimental',
                'may change without notice',
                'no stability guarantee',
            ]
        )
        assert not has_unstable_warning, (
            f'Public API in {filename} is marked as unstable. Public APIs like Container and adapter should be stable.'
        )


@then('when I look at internal APIs like _registry')
def step_look_at_internal_apis(context: Context) -> None:
    """Search for internal API documentation."""
    context.internal_api_mentions = {}
    for filename, content in context.api_content.items():
        if '_registry' in content or 'internal' in content.lower():
            context.internal_api_mentions[filename] = content


@then('internal APIs are marked with no stability guarantee')
def step_internal_apis_marked_no_guarantee(context: Context) -> None:
    """Verify internal APIs carry a no-stability-guarantee warning."""
    assert len(context.internal_api_mentions) > 0, (
        'No API documentation mentions internal APIs like _registry. '
        "Internal APIs should be documented with a 'no stability guarantee' warning."
    )
    found_warning = False
    for _filename, content in context.internal_api_mentions.items():
        content_lower = content.lower()
        if any(
            phrase in content_lower
            for phrase in [
                'internal',
                'no stability guarantee',
                'private',
                'not part of the public api',
                'may change',
            ]
        ):
            found_warning = True
            break
    assert found_warning, (
        'Internal APIs are documented but not marked with a stability warning. '
        "Expected phrases like 'internal', 'no stability guarantee', or "
        "'not part of the public API'."
    )


# ---------------------------------------------------------------------------
# Scenario: Deprecation warnings exist in code infrastructure
# ---------------------------------------------------------------------------


@given('the dioxide package is importable')
def step_dioxide_importable(context: Context) -> None:
    """Verify dioxide can be imported."""
    import dioxide  # noqa: PLC0415, F401

    context.dioxide_available = True


@when('I check for deprecation warning infrastructure')
def step_check_deprecation_infrastructure(context: Context) -> None:
    """Look for deprecation utility in the dioxide package."""
    python_src = PROJECT_ROOT / 'python' / 'dioxide'
    context.deprecation_files = []
    for py_file in python_src.rglob('*.py'):
        content = py_file.read_text()
        if 'deprecat' in content.lower() and ('def ' in content or 'class ' in content):
            context.deprecation_files.append(py_file)
    context.python_src = python_src


@then('a deprecation utility function exists')
def step_deprecation_utility_exists(context: Context) -> None:
    """Verify a deprecation utility is available."""
    # Check for a dedicated deprecation module or utility function
    deprecation_module = context.python_src / 'deprecation.py'
    has_dedicated_module = deprecation_module.exists()
    has_deprecation_code = len(context.deprecation_files) > 0

    assert has_dedicated_module or has_deprecation_code, (
        'No deprecation utility found in python/dioxide/. '
        'Expected a deprecation.py module or deprecation helper function '
        'that standardizes how dioxide emits deprecation warnings.'
    )

    if has_dedicated_module:
        context.deprecation_module_content = deprecation_module.read_text()
    else:
        context.deprecation_module_content = context.deprecation_files[0].read_text()


@then('the utility accepts a version and replacement message')
def step_utility_accepts_version_and_replacement(context: Context) -> None:
    """Verify the deprecation utility accepts version and replacement params."""
    content = context.deprecation_module_content
    has_version_param = any(kw in content for kw in ['version', 'since', 'removed_in', 'deprecated_in'])
    has_replacement_param = any(kw in content for kw in ['replacement', 'alternative', 'instead', 'use_instead'])
    assert has_version_param, (
        'Deprecation utility does not accept a version parameter. '
        'It should indicate which version deprecated the feature.'
    )
    assert has_replacement_param, (
        'Deprecation utility does not accept a replacement message. '
        'It should suggest what to use instead of the deprecated feature.'
    )


@then('calling it emits a DeprecationWarning')
def step_calling_emits_deprecation_warning(context: Context) -> None:
    """Verify the deprecation infrastructure can emit warnings."""
    # Try to import and call the deprecation utility
    try:
        from dioxide.deprecation import emit_deprecation_warning  # noqa: PLC0415

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter('always')
            emit_deprecation_warning(
                feature='test_feature',
                removed_in='99.0.0',
                replacement='test_replacement',
            )
        deprecation_warnings = [w for w in caught if issubclass(w.category, DeprecationWarning)]
        assert len(deprecation_warnings) >= 1, 'emit_deprecation_warning() did not emit a DeprecationWarning.'
    except ImportError as err:
        raise AssertionError(
            'Could not import dioxide.deprecation.emit_deprecation_warning. '
            'A standardized deprecation utility module is needed.'
        ) from err


# ---------------------------------------------------------------------------
# Scenario: CHANGELOG marks breaking changes clearly
# ---------------------------------------------------------------------------


@given('I read the CHANGELOG file')
def step_read_changelog(context: Context) -> None:
    """Read the CHANGELOG.md file."""
    changelog_path = PROJECT_ROOT / 'CHANGELOG.md'
    assert changelog_path.exists(), f'CHANGELOG.md not found at {changelog_path}'
    context.changelog_content = changelog_path.read_text()
    context.changelog_path = changelog_path


@when('I look at major version entries')
def step_look_at_major_versions(context: Context) -> None:
    """Extract major version entries (>= 2.0.0) from the CHANGELOG.

    v1.0.0 is the initial stable release and does not represent a breaking
    change from a previous major version.  Only versions where the major
    number is 2 or higher are expected to document breaking changes.
    """
    version_header_re = re.compile(r'^## \[?v?(\d+)\.(\d+)\.(\d+)')

    lines = context.changelog_content.split('\n')
    context.major_version_sections: list[str] = []
    current_section: list[str] = []
    in_major_section = False

    for line in lines:
        match = version_header_re.match(line)
        if match or line.startswith('## [') or line.startswith('## v'):
            if in_major_section and current_section:
                context.major_version_sections.append('\n'.join(current_section))
            if match:
                major = int(match.group(1))
                minor = int(match.group(2))
                patch = int(match.group(3))
                is_major_breaking = major >= 2 and minor == 0 and patch == 0
            else:
                is_major_breaking = False

            if is_major_breaking:
                in_major_section = True
                current_section = [line]
            else:
                in_major_section = False
                current_section = []
        elif in_major_section:
            current_section.append(line)

    if in_major_section and current_section:
        context.major_version_sections.append('\n'.join(current_section))

    assert len(context.major_version_sections) > 0, 'No major version entries (>= 2.0.0) found in CHANGELOG.md'


@then('breaking changes are marked with a BREAKING indicator')
def step_breaking_changes_marked(context: Context) -> None:
    """Verify breaking changes have clear markers."""
    for section in context.major_version_sections:
        section_lower = section.lower()
        has_breaking_marker = any(marker in section_lower for marker in ['breaking', 'breaking change', 'incompatible'])
        assert has_breaking_marker, (
            'Major version entry in CHANGELOG does not mark breaking changes. '
            "Expected 'BREAKING', 'BREAKING CHANGE', or similar marker. "
            f'Section content: {section[:200]}...'
        )


@then('each breaking change links to migration instructions')
def step_breaking_changes_link_to_migration(context: Context) -> None:
    """Verify the BREAKING CHANGES subsection references migration docs.

    Only the breaking-changes subsection is checked, not the entire
    version entry.  A passing mention of 'migration' elsewhere in the
    release notes (e.g. in the Documentation section) is not sufficient.
    """
    for section in context.major_version_sections:
        lines = section.split('\n')
        breaking_lines: list[str] = []
        in_breaking = False
        for line in lines:
            header_lower = line.lower().strip()
            if header_lower.startswith('###') and 'breaking' in header_lower:
                in_breaking = True
                continue
            if header_lower.startswith('###') and in_breaking:
                break
            if in_breaking:
                breaking_lines.append(line)

        breaking_text = '\n'.join(breaking_lines).lower()
        has_migration_link = any(
            phrase in breaking_text
            for phrase in [
                'migration',
                'upgrade guide',
                'how to update',
                'see the migration',
                'migration guide',
            ]
        )
        assert has_migration_link, (
            'BREAKING CHANGES subsection in CHANGELOG does not link to '
            'migration instructions. Each breaking change entry should '
            'reference a migration guide.\n'
            f'Breaking subsection content: {breaking_text[:300]}...'
        )


@then('the affected API is clearly identified')
def step_affected_api_identified(context: Context) -> None:
    """Verify specific APIs are named in breaking change entries."""
    for section in context.major_version_sections:
        has_api_reference = any(
            api in section
            for api in [
                'Profile',
                'Container',
                'adapter',
                'service',
                'lifecycle',
                'Scope',
                '`',
                '``',
            ]
        )
        assert has_api_reference, (
            'Breaking changes in CHANGELOG do not identify which APIs are affected. '
            'Each entry should name the specific API that changed. '
            f'Section content: {section[:200]}...'
        )


# ---------------------------------------------------------------------------
# Scenario: Future migration has tooling support documentation
# ---------------------------------------------------------------------------


@given('a future major version may be released')
def step_future_version_possible(context: Context) -> None:
    """Acknowledge that future breaking changes are possible."""
    context.docs_dir = DOCS_DIR


@when('I look for migration support documentation')
def step_look_for_migration_support(context: Context) -> None:
    """Search for version-to-version migration documentation.

    This specifically looks for dioxide upgrade guides (v1 to v2, etc.),
    NOT migration guides from other frameworks (dependency-injector, mocks).
    """
    all_migration_files = [
        f for f in DOCS_DIR.rglob('*migration*') if f.suffix in {'.md', '.rst'} and '_build' not in str(f)
    ]
    # Exclude migration-from-other-tools docs
    version_migration_files = [f for f in all_migration_files if 'from-' not in f.stem and 'from_' not in f.stem]
    context.migration_docs = version_migration_files
    context.migration_contents = {}
    for f in version_migration_files:
        context.migration_contents[f.name] = f.read_text()


@then('I find documentation describing automated migration options')
def step_find_automated_migration_docs(context: Context) -> None:
    """Verify migration docs discuss automation."""
    found_automation_docs = False
    for filename, content in context.migration_contents.items():
        content_lower = content.lower()
        if any(
            phrase in content_lower
            for phrase in [
                'automat',
                'tooling',
                'codemod',
                'script',
                'find-replace',
                'find and replace',
            ]
        ):
            found_automation_docs = True
            context.migration_tooling_doc = filename
            context.migration_tooling_content = content
            break

    assert found_automation_docs, (
        'No migration documentation discusses automated migration options. '
        'Expected docs mentioning codemods, scripts, or find-replace patterns.'
    )


@then('there are at least find-replace patterns documented')
def step_find_replace_patterns_exist(context: Context) -> None:
    """Verify find-replace patterns are documented."""
    content_lower = context.migration_tooling_content.lower()
    has_patterns = any(
        phrase in content_lower
        for phrase in [
            'find',
            'replace',
            'sed ',
            'regex',
            'search and replace',
            'find-replace',
        ]
    )
    assert has_patterns, (
        f'Migration doc {context.migration_tooling_doc} discusses tooling '
        'but does not include concrete find-replace patterns.'
    )


@then('codemod tooling is mentioned as an option')
def step_codemod_mentioned(context: Context) -> None:
    """Verify codemod tooling is discussed."""
    content_lower = context.migration_tooling_content.lower()
    has_codemod = any(
        phrase in content_lower
        for phrase in [
            'codemod',
            'libcst',
            'ast',
            'automated refactoring',
            'jscodeshift',
            'rector',
            'bowler',
        ]
    )
    assert has_codemod, (
        f'Migration doc {context.migration_tooling_doc} does not mention '
        'codemod tooling as an option for automated migration. '
        'Expected mentions of codemod tools (libcst, bowler, etc.) '
        'or AST-based refactoring.'
    )
