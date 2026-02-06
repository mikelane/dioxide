"""Scan plan module for previewing what container.scan() would discover."""

from __future__ import annotations

import ast
import importlib.util
import logging
from dataclasses import (
    dataclass,
    field,
)
from pathlib import Path


@dataclass(frozen=True)
class ServiceInfo:
    """Information about a discovered @service-decorated class."""

    class_name: str
    module: str


@dataclass(frozen=True)
class AdapterInfo:
    """Information about a discovered @adapter.for_()-decorated class."""

    class_name: str
    module: str


@dataclass
class ScanPlan:
    """Preview of what container.scan() would discover and import.

    Created by ``container.scan_plan()`` to show which modules would be
    imported and which decorated classes would be found, without actually
    importing any modules or registering any components.

    Attributes:
        modules: List of fully-qualified module paths that would be imported.
        services: List of ``ServiceInfo`` objects for discovered @service classes.
        adapters: List of ``AdapterInfo`` objects for discovered @adapter classes.
    """

    modules: list[str] = field(default_factory=list)
    services: list[ServiceInfo] = field(default_factory=list)
    adapters: list[AdapterInfo] = field(default_factory=list)

    def __repr__(self) -> str:
        return f'ScanPlan(modules={len(self.modules)}, services={len(self.services)}, adapters={len(self.adapters)})'


def _discover_modules(package_name: str) -> list[str]:
    """Walk a package tree and return module paths without importing them.

    Uses importlib.util.find_spec to locate the package on disk, then
    walks the filesystem to find .py files. No modules are imported.
    """
    try:
        spec = importlib.util.find_spec(package_name)
    except (ModuleNotFoundError, ValueError):
        raise ImportError(f"Package '{package_name}' not found") from None

    if spec is None:
        raise ImportError(f"Package '{package_name}' not found")

    modules = [package_name]

    if spec.submodule_search_locations is None:
        return modules

    for search_path_str in spec.submodule_search_locations:
        search_path = Path(search_path_str)
        if not search_path.is_dir():
            continue
        _walk_package_dir(search_path, package_name, modules)

    return modules


def _walk_package_dir(directory: Path, prefix: str, modules: list[str]) -> None:
    """Recursively walk a directory to discover Python module paths."""
    for item in sorted(directory.iterdir()):
        if item.name.startswith('_') and item.name != '__init__.py':
            continue
        if item.is_file() and item.suffix == '.py' and item.name != '__init__.py':
            module_name = f'{prefix}.{item.stem}'
            modules.append(module_name)
        elif item.is_dir() and (item / '__init__.py').exists():
            subpackage_name = f'{prefix}.{item.name}'
            modules.append(subpackage_name)
            _walk_package_dir(item, subpackage_name, modules)


def _parse_decorators_from_source(source: str, module_path: str) -> tuple[list[ServiceInfo], list[AdapterInfo]]:
    """Parse a Python source file's AST to find dioxide decorator usage.

    Looks for @service and @adapter.for_() decorators without importing
    the module. Returns lists of discovered services and adapters.
    """
    services: list[ServiceInfo] = []
    adapters: list[AdapterInfo] = []

    try:
        tree = ast.parse(source)
    except SyntaxError:
        logging.warning(f'Failed to parse {module_path}: syntax error')
        return services, adapters

    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue

        for decorator in node.decorator_list:
            if _is_service_decorator(decorator):
                services.append(ServiceInfo(class_name=node.name, module=module_path))
            elif _is_adapter_decorator(decorator):
                adapters.append(AdapterInfo(class_name=node.name, module=module_path))

    return services, adapters


def _is_service_decorator(node: ast.expr) -> bool:
    """Check if an AST decorator node is @service or @service(...)."""
    if isinstance(node, ast.Name) and node.id == 'service':
        return True
    if isinstance(node, ast.Call):
        return _is_service_decorator(node.func)
    return False


def _is_adapter_decorator(node: ast.expr) -> bool:
    """Check if an AST decorator node is @adapter.for_(...)."""
    if isinstance(node, ast.Call):
        func = node.func
        if isinstance(func, ast.Attribute) and func.attr == 'for_':
            if isinstance(func.value, ast.Name) and func.value.id == 'adapter':
                return True
            if isinstance(func.value, ast.Attribute) and func.value.attr == 'adapter':
                return True
    return False


def build_scan_plan(package_name: str) -> ScanPlan:
    """Build a scan plan by walking a package and parsing AST.

    This discovers modules and their dioxide decorators without importing
    any modules. Uses ``importlib.util.find_spec`` for package location
    and ``ast.parse`` for decorator discovery.
    """
    module_paths = _discover_modules(package_name)

    all_services: list[ServiceInfo] = []
    all_adapters: list[AdapterInfo] = []

    for mod_path in module_paths:
        try:
            spec = importlib.util.find_spec(mod_path)
        except (ModuleNotFoundError, ValueError):
            continue

        if spec is None or spec.origin is None:
            continue

        try:
            with open(spec.origin) as f:
                source = f.read()
        except OSError:
            continue

        services, adapters = _parse_decorators_from_source(source, mod_path)
        all_services.extend(services)
        all_adapters.extend(adapters)

    return ScanPlan(
        modules=module_paths,
        services=all_services,
        adapters=all_adapters,
    )
