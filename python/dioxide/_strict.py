"""AST-based side-effect detection for strict mode scanning.

Analyzes Python source code to detect potential module-level side effects
before importing modules. This is a best-effort heuristic -- false positives
are acceptable, false negatives are expected.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass


@dataclass(frozen=True)
class SideEffectFinding:
    """A detected potential side effect in a module."""

    filename: str
    line: int
    description: str
    suggestion: str


# Function calls that are safe at module level (no side effects)
_SAFE_CALLS: frozenset[str] = frozenset(
    {
        'logging.getLogger',
        'os.environ.get',
        'os.environ.setdefault',
        'os.path.join',
        'os.path.dirname',
        'os.path.abspath',
        'os.path.basename',
        'os.path.exists',
        'os.path.expanduser',
        'pathlib.Path',
        'Path',
        'TypeVar',
        'typing.TypeVar',
        'typing.NewType',
        'NewType',
        'namedtuple',
        'collections.namedtuple',
        'dataclass',
        'dataclasses.dataclass',
        'enum.Enum',
        'int',
        'str',
        'float',
        'bool',
        'list',
        'dict',
        'set',
        'tuple',
        'frozenset',
        'type',
        'object',
        'super',
        'property',
        'staticmethod',
        'classmethod',
        'abstractmethod',
    }
)


def _get_call_name(node: ast.Call) -> str | None:
    """Extract the full dotted name from a Call node's func attribute."""
    func = node.func
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        parts: list[str] = [func.attr]
        current = func.value
        while isinstance(current, ast.Attribute):
            parts.append(current.attr)
            current = current.value
        if isinstance(current, ast.Name):
            parts.append(current.id)
            return '.'.join(reversed(parts))
    return None


def _is_safe_call(call_name: str) -> bool:
    """Check if a function call is known to be safe at module level."""
    return call_name in _SAFE_CALLS


def _find_calls_in_node(node: ast.AST) -> list[ast.Call]:
    """Find all Call nodes within an expression (handles chained calls)."""
    calls: list[ast.Call] = []
    if isinstance(node, ast.Call):
        calls.append(node)
        # Also check for chained calls like open("f").read()
        calls.extend(_find_calls_in_node(node.func))
        for arg in node.args:
            calls.extend(_find_calls_in_node(arg))
    elif isinstance(node, ast.Attribute):
        calls.extend(_find_calls_in_node(node.value))
    return calls


def detect_side_effects(source: str, filename: str) -> list[SideEffectFinding]:
    """Analyze Python source code for potential module-level side effects.

    Args:
        source: Python source code to analyze.
        filename: Filename for error reporting.

    Returns:
        List of detected side-effect findings.
    """
    try:
        tree = ast.parse(source, filename=filename)
    except SyntaxError:
        return []

    findings: list[SideEffectFinding] = []

    for node in ast.iter_child_nodes(tree):
        # Only examine top-level statements (not inside functions/classes)
        calls_to_check: list[ast.Call] = []

        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
            # Bare function call: print("hello")
            calls_to_check = _find_calls_in_node(node.value)
        elif isinstance(node, (ast.Assign, ast.AnnAssign)) and node.value is not None:
            # Assignment from function call: conn = db.connect(...)
            # Also handles annotated: conn: Connection = db.connect(...)
            calls_to_check = _find_calls_in_node(node.value)

        for call in calls_to_check:
            call_name = _get_call_name(call)
            if call_name is None:
                continue
            if _is_safe_call(call_name):
                continue
            findings.append(
                SideEffectFinding(
                    filename=filename,
                    line=call.lineno,
                    description=f'Module-level call: {call_name}()',
                    suggestion="Move to a function, @lifecycle initialize(), or if __name__ == '__main__' block",
                )
            )

    return findings
