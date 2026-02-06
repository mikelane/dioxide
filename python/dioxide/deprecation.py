"""Deprecation warning infrastructure for dioxide.

Provides the ``deprecated()`` decorator for marking functions and methods
as deprecated with structured warning messages that include version
information and migration guidance.
"""

from __future__ import annotations

import functools
import warnings
from typing import (
    TYPE_CHECKING,
    TypeVar,
)

from dioxide.exceptions import DioxideDeprecationWarning

if TYPE_CHECKING:
    from collections.abc import Callable

    F = TypeVar('F', bound=Callable[..., object])


def deprecated(
    *,
    since: str,
    removed_in: str,
    alternative: str | None = None,
) -> Callable[[F], F]:
    """Mark a function or method as deprecated.

    Args:
        since: The version when this was deprecated (e.g., '2.0.0').
        removed_in: The version when this will be removed (e.g., '3.0.0').
        alternative: What to use instead (e.g., 'str(profile)').

    Returns:
        A decorator that wraps the function to emit a DioxideDeprecationWarning
        when called.
    """

    def decorator(func: F) -> F:
        name = getattr(func, '__qualname__', func.__name__)
        parts = [f'{name} is deprecated since v{since} and will be removed in v{removed_in}.']
        if alternative:
            parts.append(f'Use {alternative} instead.')
        message = ' '.join(parts)

        @functools.wraps(func)
        def wrapper(*args: object, **kwargs: object) -> object:
            warnings.warn(message, DioxideDeprecationWarning, stacklevel=2)
            return func(*args, **kwargs)

        return wrapper  # type: ignore[return-value]

    return decorator


__all__ = ['deprecated']
