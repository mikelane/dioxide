"""Tests for strict mode side-effect detection in scan().

Strict mode uses AST analysis to detect potential module-level side effects
before importing modules, warning developers about patterns that may cause
unexpected behavior during scan().
"""

from __future__ import annotations

import sys
import textwrap
import warnings
from pathlib import Path

from dioxide import (
    Container,
    Profile,
)
from dioxide.exceptions import SideEffectWarning


class DescribeScanStrictParameter:
    """scan() accepts a strict parameter."""

    def it_accepts_strict_false_without_error(self) -> None:
        container = Container()
        container.scan(profile=Profile.TEST, strict=False)

    def it_accepts_strict_true_without_error(self) -> None:
        container = Container()
        container.scan(profile=Profile.TEST, strict=True)

    def it_defaults_strict_to_false(self) -> None:
        container = Container()
        container.scan(profile=Profile.TEST)


class DescribeDetectModuleLevelCalls:
    """AST detection of module-level function calls."""

    def it_detects_a_bare_function_call(self) -> None:
        from dioxide._strict import detect_side_effects

        source = textwrap.dedent("""\
            import os
            os.makedirs("/tmp/foo")
        """)
        findings = detect_side_effects(source, 'test_module.py')
        assert len(findings) == 1
        assert findings[0].line == 2
        assert 'os.makedirs' in findings[0].description

    def it_detects_an_assignment_from_a_function_call(self) -> None:
        from dioxide._strict import detect_side_effects

        source = textwrap.dedent("""\
            import psycopg2
            connection = psycopg2.connect("postgresql://localhost/mydb")
        """)
        findings = detect_side_effects(source, 'test_module.py')
        assert len(findings) == 1
        assert findings[0].line == 2
        assert 'psycopg2.connect' in findings[0].description

    def it_allows_safe_calls_like_logging_get_logger(self) -> None:
        from dioxide._strict import detect_side_effects

        source = textwrap.dedent("""\
            import logging
            logger = logging.getLogger(__name__)
        """)
        findings = detect_side_effects(source, 'test_module.py')
        assert len(findings) == 0

    def it_allows_os_environ_get(self) -> None:
        from dioxide._strict import detect_side_effects

        source = textwrap.dedent("""\
            import os
            DB_URL = os.environ.get("DATABASE_URL", "sqlite:///dev.db")
        """)
        findings = detect_side_effects(source, 'test_module.py')
        assert len(findings) == 0

    def it_allows_type_alias_definitions(self) -> None:
        from dioxide._strict import detect_side_effects

        source = textwrap.dedent("""\
            from typing import TypeVar
            T = TypeVar("T")
        """)
        findings = detect_side_effects(source, 'test_module.py')
        assert len(findings) == 0

    def it_allows_decorator_usage(self) -> None:
        from dioxide._strict import detect_side_effects

        source = textwrap.dedent("""\
            from dioxide import service

            @service
            class MyService:
                pass
        """)
        findings = detect_side_effects(source, 'test_module.py')
        assert len(findings) == 0

    def it_returns_empty_for_clean_module(self) -> None:
        from dioxide._strict import detect_side_effects

        source = textwrap.dedent("""\
            from typing import Protocol

            class EmailPort(Protocol):
                async def send(self, to: str) -> None: ...
        """)
        findings = detect_side_effects(source, 'test_module.py')
        assert len(findings) == 0

    def it_detects_print_at_module_level(self) -> None:
        from dioxide._strict import detect_side_effects

        source = textwrap.dedent("""\
            print("initializing module")
        """)
        findings = detect_side_effects(source, 'test_module.py')
        assert len(findings) == 1
        assert 'print' in findings[0].description

    def it_ignores_calls_inside_functions(self) -> None:
        from dioxide._strict import detect_side_effects

        source = textwrap.dedent("""\
            def setup():
                print("this is fine")

            class MyClass:
                def __init__(self):
                    open("file.txt")
        """)
        findings = detect_side_effects(source, 'test_module.py')
        assert len(findings) == 0

    def it_detects_annotated_assignment_with_side_effect(self) -> None:
        from dioxide._strict import detect_side_effects

        source = textwrap.dedent("""\
            import psycopg2
            connection: psycopg2.Connection = psycopg2.connect("postgresql://localhost/mydb")
        """)
        findings = detect_side_effects(source, 'test_module.py')
        assert len(findings) == 1
        assert 'psycopg2.connect' in findings[0].description

    def it_detects_open_at_module_level(self) -> None:
        from dioxide._strict import detect_side_effects

        source = textwrap.dedent("""\
            config = open("config.json").read()
        """)
        findings = detect_side_effects(source, 'test_module.py')
        assert len(findings) == 1
        assert 'open' in findings[0].description

    def it_detects_side_effects_in_keyword_arguments(self) -> None:
        from dioxide._strict import detect_side_effects

        source = textwrap.dedent("""\
            config = dict(connection=db.connect())
        """)
        findings = detect_side_effects(source, 'test_module.py')
        assert len(findings) >= 1
        descriptions = [f.description for f in findings]
        assert any('db.connect' in d for d in descriptions)


class DescribeFindingDetails:
    """Side-effect findings include useful details."""

    def it_includes_the_filename(self) -> None:
        from dioxide._strict import detect_side_effects

        source = "print('hello')\n"
        findings = detect_side_effects(source, 'myapp/database.py')
        assert findings[0].filename == 'myapp/database.py'

    def it_includes_a_suggestion(self) -> None:
        from dioxide._strict import detect_side_effects

        source = "print('hello')\n"
        findings = detect_side_effects(source, 'test.py')
        assert findings[0].suggestion is not None
        assert len(findings[0].suggestion) > 0


class DescribeScanStrictWithPackage:
    """scan() with strict=True emits warnings for side-effect modules."""

    def it_emits_side_effect_warnings_with_custom_category(self, tmp_path: Path) -> None:
        pkg_dir = tmp_path / 'warning_category_pkg'
        pkg_dir.mkdir()
        (pkg_dir / '__init__.py').write_text('')
        (pkg_dir / 'bad_module.py').write_text("print('side effect')\n")

        sys.path.insert(0, str(tmp_path))
        try:
            container = Container()
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter('always')
                container.scan(package='warning_category_pkg', profile=Profile.TEST, strict=True)

            side_effect_warnings = [w for w in caught if issubclass(w.category, SideEffectWarning)]
            assert len(side_effect_warnings) >= 1
        finally:
            sys.path.remove(str(tmp_path))
            for key in list(sys.modules.keys()):
                if key.startswith('warning_category_pkg'):
                    del sys.modules[key]

    def it_allows_filtering_side_effect_warnings(self, tmp_path: Path) -> None:
        pkg_dir = tmp_path / 'filter_warning_pkg'
        pkg_dir.mkdir()
        (pkg_dir / '__init__.py').write_text('')
        (pkg_dir / 'bad_module.py').write_text("print('side effect')\n")

        sys.path.insert(0, str(tmp_path))
        try:
            container = Container()
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter('always')
                warnings.filterwarnings('ignore', category=SideEffectWarning)
                container.scan(package='filter_warning_pkg', profile=Profile.TEST, strict=True)

            side_effect_warnings = [w for w in caught if issubclass(w.category, SideEffectWarning)]
            assert len(side_effect_warnings) == 0
        finally:
            sys.path.remove(str(tmp_path))
            for key in list(sys.modules.keys()):
                if key.startswith('filter_warning_pkg'):
                    del sys.modules[key]

    def it_emits_warnings_for_side_effect_modules(self, tmp_path: Path) -> None:
        pkg_dir = tmp_path / 'strict_test_pkg'
        pkg_dir.mkdir()
        (pkg_dir / '__init__.py').write_text('')
        (pkg_dir / 'bad_module.py').write_text(
            textwrap.dedent("""\
                print("side effect at module level")
            """)
        )

        sys.path.insert(0, str(tmp_path))
        try:
            container = Container()
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter('always')
                container.scan(package='strict_test_pkg', profile=Profile.TEST, strict=True)

            side_effect_warnings = [w for w in caught if 'side effect' in str(w.message).lower()]
            assert len(side_effect_warnings) >= 1
            assert 'bad_module' in str(side_effect_warnings[0].message)
        finally:
            sys.path.remove(str(tmp_path))
            for key in list(sys.modules.keys()):
                if key.startswith('strict_test_pkg'):
                    del sys.modules[key]

    def it_emits_no_warnings_for_clean_modules(self, tmp_path: Path) -> None:
        pkg_dir = tmp_path / 'clean_test_pkg'
        pkg_dir.mkdir()
        (pkg_dir / '__init__.py').write_text('')
        (pkg_dir / 'clean_module.py').write_text(
            textwrap.dedent("""\
                import logging
                logger = logging.getLogger(__name__)

                MY_CONSTANT = 42
            """)
        )

        sys.path.insert(0, str(tmp_path))
        try:
            container = Container()
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter('always')
                container.scan(package='clean_test_pkg', profile=Profile.TEST, strict=True)

            side_effect_warnings = [w for w in caught if 'side effect' in str(w.message).lower()]
            assert len(side_effect_warnings) == 0
        finally:
            sys.path.remove(str(tmp_path))
            for key in list(sys.modules.keys()):
                if key.startswith('clean_test_pkg'):
                    del sys.modules[key]

    def it_checks_init_py_for_side_effects_before_importing(self, tmp_path: Path) -> None:
        pkg_dir = tmp_path / 'init_side_effect_pkg'
        pkg_dir.mkdir()
        (pkg_dir / '__init__.py').write_text("print('init side effect')\n")
        (pkg_dir / 'clean_module.py').write_text('MY_CONSTANT = 42\n')

        sys.path.insert(0, str(tmp_path))
        try:
            container = Container()
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter('always')
                container.scan(package='init_side_effect_pkg', profile=Profile.TEST, strict=True)

            side_effect_warnings = [w for w in caught if issubclass(w.category, SideEffectWarning)]
            assert len(side_effect_warnings) >= 1
            assert 'init_side_effect_pkg' in str(side_effect_warnings[0].message)
        finally:
            sys.path.remove(str(tmp_path))
            for key in list(sys.modules.keys()):
                if key.startswith('init_side_effect_pkg'):
                    del sys.modules[key]

    def it_does_not_emit_warnings_when_strict_is_false(self, tmp_path: Path) -> None:
        pkg_dir = tmp_path / 'nostrict_test_pkg'
        pkg_dir.mkdir()
        (pkg_dir / '__init__.py').write_text('')
        (pkg_dir / 'bad_module.py').write_text("print('side effect')\n")

        sys.path.insert(0, str(tmp_path))
        try:
            container = Container()
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter('always')
                container.scan(package='nostrict_test_pkg', profile=Profile.TEST, strict=False)

            side_effect_warnings = [w for w in caught if 'side effect' in str(w.message).lower()]
            assert len(side_effect_warnings) == 0
        finally:
            sys.path.remove(str(tmp_path))
            for key in list(sys.modules.keys()):
                if key.startswith('nostrict_test_pkg'):
                    del sys.modules[key]
