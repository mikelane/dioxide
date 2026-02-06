"""Tests for Container.scan_plan() API."""

from __future__ import annotations

import sys

from dioxide import Container


class DescribeScanPlan:
    """Tests for scan_plan() method that previews what scan() would do."""

    def it_returns_a_scan_plan_object(self) -> None:
        container = Container()
        plan = container.scan_plan(package='tests.fixtures.test_package_a')

        assert plan is not None

    def it_lists_discovered_module_paths(self) -> None:
        container = Container()
        plan = container.scan_plan(package='tests.fixtures.test_package_a')

        assert 'tests.fixtures.test_package_a' in plan.modules

    def it_does_not_import_modules(self) -> None:
        modules_before = set(sys.modules.keys())

        container = Container()
        container.scan_plan(package='tests.fixtures.test_package_b')

        new_modules = set(sys.modules.keys()) - modules_before
        scan_plan_imported = [m for m in new_modules if m.startswith('tests.fixtures.test_package_b.subpkg')]
        assert scan_plan_imported == [], f'scan_plan() should not import modules, but imported: {scan_plan_imported}'

    def it_discovers_services_via_ast(self) -> None:
        container = Container()
        plan = container.scan_plan(package='tests.fixtures.test_package_a')

        service_names = [s.class_name for s in plan.services]
        assert 'ServiceA' in service_names

    def it_discovers_adapters_via_ast(self) -> None:
        container = Container()
        plan = container.scan_plan(package='tests.fixtures.test_package_d')

        adapter_names = [a.class_name for a in plan.adapters]
        assert len(adapter_names) > 0

    def it_includes_module_path_in_discovered_items(self) -> None:
        container = Container()
        plan = container.scan_plan(package='tests.fixtures.test_package_a')

        service_modules = [s.module for s in plan.services]
        assert any('test_package_a' in m for m in service_modules)

    def it_discovers_subpackage_modules(self) -> None:
        container = Container()
        plan = container.scan_plan(package='tests.fixtures.test_package_b')

        has_subpkg = any('subpkg' in m for m in plan.modules)
        assert has_subpkg, f'Expected subpackage modules, got: {plan.modules}'

    def it_does_not_register_anything(self) -> None:
        container = Container()
        container.scan_plan(package='tests.fixtures.test_package_a')

        assert container.is_empty()

    def it_validates_allowed_packages(self) -> None:
        import pytest

        container = Container(allowed_packages=['myapp'])
        with pytest.raises(ValueError, match='not in allowed_packages'):
            container.scan_plan(package='tests.fixtures.test_package_a')

    def it_has_repr_for_debugging(self) -> None:
        container = Container()
        plan = container.scan_plan(package='tests.fixtures.test_package_a')

        plan_repr = repr(plan)
        assert 'ScanPlan' in plan_repr
        assert 'modules' in plan_repr

    def it_handles_packages_with_syntax_errors_gracefully(self) -> None:
        container = Container()
        plan = container.scan_plan(package='tests.fixtures.test_package_with_errors')

        assert plan is not None
        assert isinstance(plan.modules, list)
