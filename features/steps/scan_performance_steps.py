"""Step definitions for scan performance acceptance tests."""

import importlib
import os
import shutil
import sys
import tempfile
import time
import warnings
from pathlib import Path

from behave import given, then, when
from behave.runner import Context

from dioxide import Container, Profile, _clear_registry

TEMP_DIR: str | None = None
PKG_ROOT: str = 'scan_perf_pkg'


def _ensure_temp_dir(context: Context) -> str:
    global TEMP_DIR
    if TEMP_DIR is None:
        TEMP_DIR = tempfile.mkdtemp(prefix='dioxide_bdd_')
        sys.path.insert(0, TEMP_DIR)
    return TEMP_DIR


def _cleanup_temp_dir() -> None:
    global TEMP_DIR
    if TEMP_DIR is not None:
        if TEMP_DIR in sys.path:
            sys.path.remove(TEMP_DIR)
        shutil.rmtree(TEMP_DIR, ignore_errors=True)
        TEMP_DIR = None


def _cleanup_modules(prefix: str) -> None:
    to_remove = [key for key in sys.modules if key.startswith(prefix)]
    for key in to_remove:
        del sys.modules[key]


def _create_package(base_dir: str, pkg_path: str) -> Path:
    parts = pkg_path.split('.')
    current = Path(base_dir)
    for part in parts:
        current = current / part
        current.mkdir(exist_ok=True)
        init_file = current / '__init__.py'
        if not init_file.exists():
            init_file.write_text('')
    return current


def _write_module(base_dir: str, module_path: str, content: str) -> None:
    parts = module_path.split('.')
    pkg_parts = parts[:-1]
    module_name = parts[-1]

    pkg_dir = _create_package(base_dir, '.'.join(pkg_parts))
    module_file = pkg_dir / f'{module_name}.py'
    module_file.write_text(content)


# ---------------------------------------------------------------------------
# Background steps
# ---------------------------------------------------------------------------


@given('a fresh dioxide container')
def step_fresh_container(context: Context) -> None:
    _clear_registry()
    context.container = Container()
    context.import_tracker = {}
    context.scan_stats = None
    context.warnings_captured = []


@given('a test package "{pkg_name}" with multiple modules')
def step_create_test_package(context: Context, pkg_name: str) -> None:
    base = _ensure_temp_dir(context)
    _cleanup_modules(pkg_name)
    pkg_path = Path(base) / pkg_name.replace('.', '/')
    if pkg_path.exists():
        shutil.rmtree(pkg_path)
    _create_package(base, pkg_name)
    context.pkg_name = pkg_name
    context.base_dir = base


# ---------------------------------------------------------------------------
# Scenario: Lazy scanning avoids importing unused modules
# ---------------------------------------------------------------------------


@given('"{module_path}" contains a decorator that tracks when it is imported')
def step_module_tracks_import(context: Context, module_path: str) -> None:
    base = _ensure_temp_dir(context)
    content = f"""\
import sys
from typing import Protocol

from dioxide import adapter, Profile

_IMPORT_MARKER = '{module_path}'
sys.modules['{module_path}'].__dict__['_was_imported'] = True


class ExpensivePort(Protocol):
    def do_work(self) -> str: ...


@adapter.for_(ExpensivePort, profile=Profile.ALL)
class ExpensiveAdapter:
    def do_work(self) -> str:
        return 'expensive'
"""
    _write_module(base, module_path, content)
    context.import_tracker[module_path] = False


@given('"{module_path}" contains a simple adapter')
def step_module_simple_adapter(context: Context, module_path: str) -> None:
    base = _ensure_temp_dir(context)
    content = """\
from typing import Protocol

from dioxide import adapter, Profile


class CheapPort(Protocol):
    def do_work(self) -> str: ...


@adapter.for_(CheapPort, profile=Profile.ALL)
class CheapAdapter:
    def do_work(self) -> str:
        return 'cheap'
"""
    _write_module(base, module_path, content)


@when('I scan "{pkg_name}" with lazy loading enabled')
def step_scan_lazy(context: Context, pkg_name: str) -> None:
    _cleanup_modules(pkg_name)
    _clear_registry()
    try:
        context.container.scan(package=pkg_name, lazy=True)
    except TypeError:
        context.lazy_not_supported = True


@when('I only resolve components from "{module_path}"')
def step_resolve_from_module(context: Context, module_path: str) -> None:
    if getattr(context, 'lazy_not_supported', False):
        return
    mod = importlib.import_module(module_path)
    cheap_port = getattr(mod, 'CheapPort', None)
    if cheap_port is not None:
        try:
            context.container.resolve(cheap_port)
        except Exception:
            pass


@then('"{module_path}" has not been imported')
def step_module_not_imported(context: Context, module_path: str) -> None:
    if getattr(context, 'lazy_not_supported', False):
        raise AssertionError(
            'container.scan() does not support lazy=True parameter yet. Lazy scanning is not implemented.'
        )
    was_imported = module_path in sys.modules
    assert not was_imported, (
        f'{module_path} was imported but should not have been (lazy scanning should defer import until resolution)'
    )


# ---------------------------------------------------------------------------
# Scenario: Scan plan shows modules without importing
# ---------------------------------------------------------------------------


@given('"{pkg_name}" contains {count:d} modules with adapters')
def step_create_modules_with_adapters(context: Context, pkg_name: str, count: int) -> None:
    base = _ensure_temp_dir(context)
    _cleanup_modules(pkg_name)
    pkg_path = Path(base) / pkg_name.replace('.', '/')
    if pkg_path.exists():
        shutil.rmtree(pkg_path)
    _create_package(base, pkg_name)

    for i in range(count):
        content = f"""\
from typing import Protocol

from dioxide import adapter, Profile


class Port{i}(Protocol):
    def action(self) -> str: ...


@adapter.for_(Port{i}, profile=Profile.ALL)
class Adapter{i}:
    def action(self) -> str:
        return 'adapter_{i}'
"""
        _write_module(base, f'{pkg_name}.mod_{i}', content)

    context.pkg_name = pkg_name
    context.expected_module_count = count


@when('I call container.scan_plan for "{pkg_name}"')
def step_call_scan_plan(context: Context, pkg_name: str) -> None:
    _cleanup_modules(pkg_name)
    _clear_registry()
    try:
        context.scan_plan_result = context.container.scan_plan(package=pkg_name)
        context.scan_plan_supported = True
    except AttributeError:
        context.scan_plan_supported = False
        context.scan_plan_result = None


@then('I receive a list of {count:d} module paths')
def step_verify_module_count(context: Context, count: int) -> None:
    if not getattr(context, 'scan_plan_supported', False):
        raise AssertionError('container.scan_plan() method does not exist yet. The scan_plan API is not implemented.')
    result = context.scan_plan_result
    modules = result.modules
    # Filter to only child modules (exclude the package root itself)
    child_modules = [m for m in modules if m != context.pkg_name]
    assert len(child_modules) == count, (
        f'Expected {count} child module paths, got {len(child_modules)}: {child_modules}'
    )


@then('no adapters are registered yet')
def step_no_adapters_registered(context: Context) -> None:
    if not getattr(context, 'scan_plan_supported', False):
        raise AssertionError(
            'container.scan_plan() method does not exist yet. Cannot verify adapter registration state.'
        )
    from dioxide._registry import _get_registered_components

    components = _get_registered_components()
    assert len(components) == 0, (
        f'No adapters should be registered after scan_plan(), but found {len(components)} components'
    )


@then('calling scan afterward registers the adapters')
def step_scan_after_plan_registers(context: Context) -> None:
    if not getattr(context, 'scan_plan_supported', False):
        raise AssertionError('container.scan_plan() method does not exist yet. Cannot test scan after plan.')
    context.container.scan(package=context.pkg_name)
    from dioxide.adapter import _adapter_registry

    registered_count = len(_adapter_registry)
    assert registered_count > 0, f'scan() after scan_plan() should register adapters, but found {registered_count}'


# ---------------------------------------------------------------------------
# Scenario: Narrow scanning only imports specified packages
# ---------------------------------------------------------------------------


@given('I have "{module_path}" with a ProductionAdapter')
def step_create_prod_adapter(context: Context, module_path: str) -> None:
    base = _ensure_temp_dir(context)
    content = """\
from typing import Protocol

from dioxide import adapter, Profile


class NarrowPort(Protocol):
    def handle(self) -> str: ...


@adapter.for_(NarrowPort, profile=Profile.PRODUCTION)
class ProductionAdapter:
    def handle(self) -> str:
        return 'production'
"""
    _write_module(base, module_path, content)


@given('I have "{module_path}" with a DevelopmentAdapter')
def step_create_dev_adapter(context: Context, module_path: str) -> None:
    base = _ensure_temp_dir(context)
    content = """\
from typing import Protocol

from dioxide import adapter, Profile


class DevPort(Protocol):
    def handle(self) -> str: ...


@adapter.for_(DevPort, profile=Profile.DEVELOPMENT)
class DevelopmentAdapter:
    def handle(self) -> str:
        return 'development'
"""
    _write_module(base, module_path, content)


@when('I scan only "{pkg_name}"')
def step_scan_narrow(context: Context, pkg_name: str) -> None:
    _cleanup_modules(PKG_ROOT)
    _clear_registry()
    context.container.scan(package=pkg_name, profile=Profile.PRODUCTION)


@then('ProductionAdapter is registered')
def step_prod_adapter_registered(context: Context) -> None:
    from dioxide.adapter import _adapter_registry

    adapter_names = [cls.__name__ for cls in _adapter_registry]
    assert 'ProductionAdapter' in adapter_names, (
        f'ProductionAdapter should be registered. Found adapters: {adapter_names}'
    )


@then('DevelopmentAdapter is not registered')
def step_dev_adapter_not_registered(context: Context) -> None:
    from dioxide.adapter import _adapter_registry

    for cls in _adapter_registry:
        registered_module = cls.__module__
        if registered_module.startswith('scan_perf_pkg.adapters.dev'):
            raise AssertionError(
                'DevelopmentAdapter module was scanned but should not have been. '
                'Narrow scanning should only import the specified package.'
            )


# ---------------------------------------------------------------------------
# Scenario: Scan statistics report what was registered
# ---------------------------------------------------------------------------


@given('I have a package with {service_count:d} services and {adapter_count:d} adapters')
def step_create_services_and_adapters(context: Context, service_count: int, adapter_count: int) -> None:
    base = _ensure_temp_dir(context)
    pkg_name = 'scan_perf_stats_pkg'
    _cleanup_modules(pkg_name)
    pkg_path = Path(base) / pkg_name
    if pkg_path.exists():
        shutil.rmtree(pkg_path)
    _create_package(base, pkg_name)

    for i in range(service_count):
        content = f"""\
from dioxide import service


@service
class StatsService{i}:
    def work(self) -> str:
        return 'service_{i}'
"""
        _write_module(base, f'{pkg_name}.svc_{i}', content)

    for i in range(adapter_count):
        content = f"""\
from typing import Protocol

from dioxide import adapter, Profile


class StatsPort{i}(Protocol):
    def action(self) -> str: ...


@adapter.for_(StatsPort{i}, profile=Profile.ALL)
class StatsAdapter{i}:
    def action(self) -> str:
        return 'adapter_{i}'
"""
        _write_module(base, f'{pkg_name}.adp_{i}', content)

    context.stats_pkg_name = pkg_name
    context.expected_service_count = service_count
    context.expected_adapter_count = adapter_count


@when('I scan the package with statistics enabled')
def step_scan_with_stats(context: Context) -> None:
    _cleanup_modules(context.stats_pkg_name)
    _clear_registry()
    try:
        context.scan_stats = context.container.scan(
            package=context.stats_pkg_name,
            statistics=True,
        )
        context.stats_supported = True
    except TypeError:
        context.stats_supported = False
        context.scan_stats = None


@then('the statistics show {count:d} services registered')
def step_verify_service_count(context: Context, count: int) -> None:
    if not getattr(context, 'stats_supported', False):
        raise AssertionError(
            'container.scan() does not support statistics=True parameter yet. Scan statistics are not implemented.'
        )
    assert context.scan_stats is not None, 'scan() should return statistics when statistics=True'
    actual = getattr(context.scan_stats, 'services_registered', None)
    assert actual == count, f'Expected {count} services registered, got {actual}'


@then('the statistics show {count:d} adapters registered')
def step_verify_adapter_count(context: Context, count: int) -> None:
    if not getattr(context, 'stats_supported', False):
        raise AssertionError(
            'container.scan() does not support statistics=True parameter yet. Scan statistics are not implemented.'
        )
    actual = getattr(context.scan_stats, 'adapters_registered', None)
    assert actual == count, f'Expected {count} adapters registered, got {actual}'


@then('the statistics include scan duration in milliseconds')
def step_verify_duration(context: Context) -> None:
    if not getattr(context, 'stats_supported', False):
        raise AssertionError(
            'container.scan() does not support statistics=True parameter yet. Scan statistics are not implemented.'
        )
    duration = getattr(context.scan_stats, 'duration_ms', None)
    assert duration is not None, 'Statistics should include duration_ms'
    assert isinstance(duration, (int, float)), f'duration_ms should be numeric, got {type(duration)}'
    assert duration >= 0, f'duration_ms should be non-negative, got {duration}'


# ---------------------------------------------------------------------------
# Scenario: Strict mode warns about module-level side effects
# ---------------------------------------------------------------------------


@given('"{module_path}" has module-level code that prints to stdout')
def step_create_side_effect_module(context: Context, module_path: str) -> None:
    base = _ensure_temp_dir(context)
    content = """\
import sys
from typing import Protocol

from dioxide import adapter, Profile

print('SIDE EFFECT: module-level print executed')
sys.stdout.flush()


class SideEffectPort(Protocol):
    def action(self) -> str: ...


@adapter.for_(SideEffectPort, profile=Profile.ALL)
class SideEffectAdapter:
    def action(self) -> str:
        return 'side_effect'
"""
    _write_module(base, module_path, content)


@when('I scan "{pkg_name}" with strict mode enabled')
def step_scan_strict(context: Context, pkg_name: str) -> None:
    _cleanup_modules(pkg_name)
    _clear_registry()
    try:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter('always')
            context.container.scan(package=pkg_name, strict=True)
            context.warnings_captured = caught
        context.strict_supported = True
    except TypeError:
        context.strict_supported = False
        context.warnings_captured = []


@then('I see a warning mentioning "{module_path}"')
def step_warning_mentions_module(context: Context, module_path: str) -> None:
    if not getattr(context, 'strict_supported', False):
        raise AssertionError(
            'container.scan() does not support strict=True parameter yet. Strict mode is not implemented.'
        )
    warning_messages = [str(w.message) for w in context.warnings_captured]
    found = any(module_path in msg for msg in warning_messages)
    assert found, f'Expected a warning mentioning "{module_path}". Warnings captured: {warning_messages}'


@then('the warning mentions "{text}"')
def step_warning_mentions_text(context: Context, text: str) -> None:
    if not getattr(context, 'strict_supported', False):
        raise AssertionError(
            'container.scan() does not support strict=True parameter yet. Strict mode is not implemented.'
        )
    warning_messages = [str(w.message) for w in context.warnings_captured]
    found = any(text in msg for msg in warning_messages)
    assert found, f'Expected a warning mentioning "{text}". Warnings captured: {warning_messages}'


# ---------------------------------------------------------------------------
# Scenario: Scanning without package parameter uses pre-imported modules
# ---------------------------------------------------------------------------


@given('I have already imported "{module_path}" containing ExplicitAdapter')
def step_import_explicit(context: Context, module_path: str) -> None:
    base = _ensure_temp_dir(context)
    content = """\
from typing import Protocol

from dioxide import adapter, Profile


class ExplicitPort(Protocol):
    def run(self) -> str: ...


@adapter.for_(ExplicitPort, profile=Profile.TEST)
class ExplicitAdapter:
    def run(self) -> str:
        return 'explicit'
"""
    _write_module(base, module_path, content)
    _cleanup_modules(module_path)
    importlib.import_module(module_path)


@given('"{module_path}" is not imported')
def step_module_not_pre_imported(context: Context, module_path: str) -> None:
    base = _ensure_temp_dir(context)
    content = """\
from typing import Protocol

from dioxide import adapter, Profile


class HiddenPort(Protocol):
    def run(self) -> str: ...


@adapter.for_(HiddenPort, profile=Profile.TEST)
class HiddenAdapter:
    def run(self) -> str:
        return 'hidden'
"""
    _write_module(base, module_path, content)
    _cleanup_modules(module_path)
    assert module_path not in sys.modules, f'{module_path} should not be imported yet'


@when('I call container.scan with profile TEST and no package parameter')
def step_scan_no_package(context: Context) -> None:
    context.container.scan(profile=Profile.TEST)


@then('ExplicitAdapter is registered')
def step_explicit_registered(context: Context) -> None:
    from dioxide.adapter import _adapter_registry

    adapter_names = [cls.__name__ for cls in _adapter_registry]
    assert 'ExplicitAdapter' in adapter_names, (
        f'ExplicitAdapter should be registered (it was pre-imported). Found adapters: {adapter_names}'
    )


@then('adapters in "{module_path}" are not registered')
def step_hidden_not_registered(context: Context, module_path: str) -> None:
    was_imported = module_path in sys.modules
    if was_imported:
        raise AssertionError(
            f'{module_path} was imported during scan() without package parameter. '
            f'When no package is specified, scan() should only discover '
            f'adapters from already-imported modules.'
        )


# ---------------------------------------------------------------------------
# Scenario: Large package scanning meets performance target
# ---------------------------------------------------------------------------


@given('I have a package with {count:d} modules containing adapters')
def step_create_large_package(context: Context, count: int) -> None:
    base = _ensure_temp_dir(context)
    pkg_name = 'scan_perf_large_pkg'
    _cleanup_modules(pkg_name)
    pkg_path = Path(base) / pkg_name
    if pkg_path.exists():
        shutil.rmtree(pkg_path)
    _create_package(base, pkg_name)

    for i in range(count):
        content = f"""\
from typing import Protocol

from dioxide import adapter, Profile


class LargePort{i}(Protocol):
    def action(self) -> str: ...


@adapter.for_(LargePort{i}, profile=Profile.ALL)
class LargeAdapter{i}:
    def action(self) -> str:
        return 'adapter_{i}'
"""
        _write_module(base, f'{pkg_name}.mod_{i}', content)

    context.large_pkg_name = pkg_name
    context.large_module_count = count


@when('I scan the package')
def step_scan_large_package(context: Context) -> None:
    pkg_name = getattr(context, 'large_pkg_name', context.pkg_name)
    _cleanup_modules(pkg_name)
    _clear_registry()

    start_time = time.perf_counter()
    context.container.scan(package=pkg_name)
    end_time = time.perf_counter()

    context.scan_duration_ms = (end_time - start_time) * 1000


@then('the scan completes in under {threshold:d} milliseconds')
def step_scan_under_threshold(context: Context, threshold: int) -> None:
    ci_multiplier = float(os.environ.get('DIOXIDE_PERF_MULTIPLIER', '1.0'))
    adjusted_threshold = threshold * ci_multiplier
    assert context.scan_duration_ms < adjusted_threshold, (
        f'Scan took {context.scan_duration_ms:.1f}ms, '
        f'exceeding threshold of {adjusted_threshold:.0f}ms '
        f'(base: {threshold}ms, CI multiplier: {ci_multiplier}x)'
    )
