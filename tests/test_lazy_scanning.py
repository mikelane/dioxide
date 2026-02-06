"""Tests for lazy adapter discovery in Container.scan()."""

import sys

from dioxide import Container


class DescribeLazyScan:
    """Tests for lazy=True parameter in Container.scan()."""

    def it_does_not_import_modules_during_lazy_scan(self) -> None:
        # Ensure the module is not already imported
        sys.modules.pop('tests.fixtures.lazy_pkg.expensive_module', None)
        sys.modules.pop('tests.fixtures.lazy_pkg.cheap_module', None)

        container = Container()
        container.scan(package='tests.fixtures.lazy_pkg', lazy=True)

        assert 'tests.fixtures.lazy_pkg.expensive_module' not in sys.modules
        assert 'tests.fixtures.lazy_pkg.cheap_module' not in sys.modules

    def it_imports_module_on_first_resolve(self) -> None:
        from dioxide import Profile

        sys.modules.pop('tests.fixtures.lazy_pkg.cheap_module', None)
        sys.modules.pop('tests.fixtures.lazy_pkg.expensive_module', None)

        container = Container()
        container.scan(package='tests.fixtures.lazy_pkg', profile=Profile.PRODUCTION, lazy=True)

        assert 'tests.fixtures.lazy_pkg.cheap_module' not in sys.modules

        from tests.fixtures.lazy_pkg.cheap_module import CheapPort

        result = container.resolve(CheapPort)
        assert result.do_work() == 'cheap'

    def it_only_imports_the_needed_module_not_all(self) -> None:
        from dioxide import Profile

        sys.modules.pop('tests.fixtures.lazy_pkg.cheap_module', None)
        sys.modules.pop('tests.fixtures.lazy_pkg.expensive_module', None)

        container = Container()
        container.scan(package='tests.fixtures.lazy_pkg', profile=Profile.PRODUCTION, lazy=True)

        from tests.fixtures.lazy_pkg.cheap_module import CheapPort

        container.resolve(CheapPort)

        assert 'tests.fixtures.lazy_pkg.cheap_module' in sys.modules
        assert 'tests.fixtures.lazy_pkg.expensive_module' not in sys.modules

    def it_caches_singleton_instances_after_lazy_resolve(self) -> None:
        from dioxide import Profile

        sys.modules.pop('tests.fixtures.lazy_pkg.cheap_module', None)
        sys.modules.pop('tests.fixtures.lazy_pkg.expensive_module', None)

        container = Container()
        container.scan(package='tests.fixtures.lazy_pkg', profile=Profile.PRODUCTION, lazy=True)

        from tests.fixtures.lazy_pkg.cheap_module import CheapPort

        first = container.resolve(CheapPort)
        second = container.resolve(CheapPort)
        assert first is second

    def it_raises_adapter_not_found_for_unregistered_port(self) -> None:
        from typing import Protocol

        import pytest

        from dioxide import Profile
        from dioxide.exceptions import AdapterNotFoundError

        sys.modules.pop('tests.fixtures.lazy_pkg.cheap_module', None)
        sys.modules.pop('tests.fixtures.lazy_pkg.expensive_module', None)

        container = Container()
        container.scan(package='tests.fixtures.lazy_pkg', profile=Profile.PRODUCTION, lazy=True)

        class UnknownPort(Protocol):
            def unknown(self) -> str: ...

        with pytest.raises(AdapterNotFoundError):
            container.resolve(UnknownPort)

    def it_respects_profile_filtering_with_lazy_scan(self) -> None:
        import pytest

        from dioxide import Profile
        from dioxide.exceptions import AdapterNotFoundError

        sys.modules.pop('tests.fixtures.lazy_pkg.cheap_module', None)
        sys.modules.pop('tests.fixtures.lazy_pkg.expensive_module', None)

        container = Container()
        container.scan(package='tests.fixtures.lazy_pkg', profile=Profile.TEST, lazy=True)

        from tests.fixtures.lazy_pkg.cheap_module import CheapPort

        with pytest.raises(AdapterNotFoundError):
            container.resolve(CheapPort)

    def it_uses_correct_profile_per_package_when_multiple_lazy_scans_registered(self) -> None:
        from dioxide import Profile

        sys.modules.pop('tests.fixtures.lazy_pkg.cheap_module', None)
        sys.modules.pop('tests.fixtures.lazy_pkg.expensive_module', None)
        sys.modules.pop('tests.fixtures.lazy_pkg_test.test_adapter_module', None)

        container = Container()
        container.scan(package='tests.fixtures.lazy_pkg', profile=Profile.PRODUCTION, lazy=True)
        container.scan(package='tests.fixtures.lazy_pkg_test', profile=Profile.TEST, lazy=True)

        from tests.fixtures.lazy_pkg.cheap_module import CheapPort
        from tests.fixtures.lazy_pkg_test.test_adapter_module import TestPort

        production_result = container.resolve(CheapPort)
        assert production_result.do_work() == 'cheap'

        test_result = container.resolve(TestPort)
        assert test_result.do_work() == 'test'

    def it_ignores_lazy_flag_when_package_is_none(self) -> None:
        import tests.fixtures.test_package_a  # noqa: F401

        container = Container()
        container.scan(package=None, lazy=True)

        from tests.fixtures.test_package_a import ServiceA

        result = container.resolve(ServiceA)
        assert result is not None

    def it_validates_allowed_packages_in_lazy_mode(self) -> None:
        import pytest

        container = Container(allowed_packages=['myapp'])

        with pytest.raises(ValueError, match='not in allowed_packages list'):
            container.scan(package='tests.fixtures.lazy_pkg', lazy=True)

    def it_resolves_expensive_adapter_only_when_needed(self) -> None:
        from dioxide import Profile

        sys.modules.pop('tests.fixtures.lazy_pkg.cheap_module', None)
        sys.modules.pop('tests.fixtures.lazy_pkg.expensive_module', None)

        container = Container()
        container.scan(package='tests.fixtures.lazy_pkg', profile=Profile.PRODUCTION, lazy=True)

        from tests.fixtures.lazy_pkg.expensive_module import ExpensivePort

        result = container.resolve(ExpensivePort)
        assert result.do_work() == 'expensive'
        assert 'tests.fixtures.lazy_pkg.expensive_module' in sys.modules

    def it_handles_modules_with_syntax_errors_gracefully(self) -> None:
        import os
        import tempfile

        from dioxide import Profile

        with tempfile.TemporaryDirectory() as tmpdir:
            pkg_dir = os.path.join(tmpdir, 'bad_pkg')
            os.makedirs(pkg_dir)

            with open(os.path.join(pkg_dir, '__init__.py'), 'w') as f:
                f.write('')

            with open(os.path.join(pkg_dir, 'broken.py'), 'w') as f:
                f.write('def foo(:\n')  # Syntax error

            with open(os.path.join(pkg_dir, 'good.py'), 'w') as f:
                f.write(
                    'from typing import Protocol\n'
                    'from dioxide import adapter, Profile\n'
                    'class GoodPort(Protocol):\n'
                    '    def work(self) -> str: ...\n'
                    '@adapter.for_(GoodPort, profile=Profile.PRODUCTION)\n'
                    'class GoodAdapter:\n'
                    '    def work(self) -> str: return "good"\n'
                )

            # Add tmpdir to sys.path temporarily
            sys.path.insert(0, tmpdir)
            try:
                container = Container()
                container.scan(package='bad_pkg', profile=Profile.PRODUCTION, lazy=True)

                # Import the good module's port and verify it resolves
                from importlib import import_module

                good_mod = import_module('bad_pkg.good')
                result = container.resolve(good_mod.GoodPort)
                assert result.work() == 'good'
            finally:
                sys.path.remove(tmpdir)
                sys.modules.pop('bad_pkg', None)
                sys.modules.pop('bad_pkg.broken', None)
                sys.modules.pop('bad_pkg.good', None)


class DescribeEagerScanBackwardCompatibility:
    """Tests that lazy=False (default) retains eager import behavior."""

    def it_eagerly_imports_all_modules_by_default(self) -> None:
        sys.modules.pop('tests.fixtures.lazy_pkg.cheap_module', None)
        sys.modules.pop('tests.fixtures.lazy_pkg.expensive_module', None)

        container = Container()
        container.scan(package='tests.fixtures.lazy_pkg')

        assert 'tests.fixtures.lazy_pkg.cheap_module' in sys.modules
        assert 'tests.fixtures.lazy_pkg.expensive_module' in sys.modules

    def it_eagerly_imports_all_modules_with_explicit_lazy_false(self) -> None:
        sys.modules.pop('tests.fixtures.lazy_pkg.cheap_module', None)
        sys.modules.pop('tests.fixtures.lazy_pkg.expensive_module', None)

        container = Container()
        container.scan(package='tests.fixtures.lazy_pkg', lazy=False)

        assert 'tests.fixtures.lazy_pkg.cheap_module' in sys.modules
        assert 'tests.fixtures.lazy_pkg.expensive_module' in sys.modules
