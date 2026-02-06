"""Tests for deprecation warning infrastructure (#407)."""

from __future__ import annotations

import warnings

import pytest


class DescribeDioxideDeprecationWarning:
    """DioxideDeprecationWarning is a custom warning class for dioxide deprecations."""

    def it_is_importable_from_dioxide(self) -> None:
        from dioxide import DioxideDeprecationWarning

        assert DioxideDeprecationWarning is not None

    def it_is_a_subclass_of_deprecation_warning(self) -> None:
        from dioxide import DioxideDeprecationWarning

        assert issubclass(DioxideDeprecationWarning, DeprecationWarning)

    def it_can_be_filtered_separately_from_other_deprecation_warnings(self) -> None:
        from dioxide import DioxideDeprecationWarning

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter('always')
            warnings.filterwarnings('ignore', category=DioxideDeprecationWarning)

            warnings.warn('dioxide thing', DioxideDeprecationWarning, stacklevel=1)
            warnings.warn('other thing', DeprecationWarning, stacklevel=1)

        assert len(caught) == 1
        assert caught[0].category is DeprecationWarning
        assert 'other thing' in str(caught[0].message)


class DescribeDeprecatedDecorator:
    """The deprecated() decorator marks functions/methods as deprecated."""

    def it_is_importable_from_dioxide(self) -> None:
        from dioxide import deprecated

        assert callable(deprecated)

    def it_emits_warning_when_decorated_function_is_called(self) -> None:
        from dioxide import (
            DioxideDeprecationWarning,
            deprecated,
        )

        @deprecated(since='2.0.0', removed_in='3.0.0')
        def old_function() -> str:
            return 'result'

        with pytest.warns(DioxideDeprecationWarning):
            result = old_function()

        assert result == 'result'

    def it_includes_since_version_in_warning_message(self) -> None:
        from dioxide import deprecated

        @deprecated(since='2.0.0', removed_in='3.0.0')
        def old_function() -> None:
            pass

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter('always')
            old_function()

        assert len(caught) == 1
        assert 'v2.0.0' in str(caught[0].message)

    def it_includes_removed_in_version_in_warning_message(self) -> None:
        from dioxide import deprecated

        @deprecated(since='2.0.0', removed_in='3.0.0')
        def old_function() -> None:
            pass

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter('always')
            old_function()

        assert len(caught) == 1
        assert 'v3.0.0' in str(caught[0].message)

    def it_includes_alternative_in_warning_message(self) -> None:
        from dioxide import deprecated

        @deprecated(since='2.0.0', removed_in='3.0.0', alternative='new_function()')
        def old_function() -> None:
            pass

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter('always')
            old_function()

        assert len(caught) == 1
        assert 'new_function()' in str(caught[0].message)

    def it_includes_function_name_in_warning_message(self) -> None:
        from dioxide import deprecated

        @deprecated(since='2.0.0', removed_in='3.0.0')
        def specific_old_function() -> None:
            pass

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter('always')
            specific_old_function()

        assert len(caught) == 1
        assert 'specific_old_function' in str(caught[0].message)

    def it_omits_alternative_text_when_not_provided(self) -> None:
        from dioxide import deprecated

        @deprecated(since='2.0.0', removed_in='3.0.0')
        def old_function() -> None:
            pass

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter('always')
            old_function()

        assert len(caught) == 1
        assert 'instead' not in str(caught[0].message)

    def it_preserves_function_name(self) -> None:
        from dioxide import deprecated

        @deprecated(since='2.0.0', removed_in='3.0.0')
        def old_function() -> None:
            pass

        assert old_function.__name__ == 'old_function'

    def it_preserves_function_docstring(self) -> None:
        from dioxide import deprecated

        @deprecated(since='2.0.0', removed_in='3.0.0')
        def old_function() -> None:
            """Original docstring."""

        assert old_function.__doc__ == 'Original docstring.'

    def it_works_on_methods(self) -> None:
        from dioxide import (
            DioxideDeprecationWarning,
            deprecated,
        )

        class MyClass:
            @deprecated(since='1.0.0', removed_in='2.0.0', alternative='new_method()')
            def old_method(self) -> str:
                return 'method_result'

        obj = MyClass()

        with pytest.warns(DioxideDeprecationWarning, match='old_method'):
            result = obj.old_method()

        assert result == 'method_result'

    def it_uses_dioxide_deprecation_warning_category(self) -> None:
        from dioxide import (
            DioxideDeprecationWarning,
            deprecated,
        )

        @deprecated(since='2.0.0', removed_in='3.0.0')
        def old_function() -> None:
            pass

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter('always')
            old_function()

        assert len(caught) == 1
        assert caught[0].category is DioxideDeprecationWarning

    def it_points_warning_to_caller_not_decorator(self) -> None:
        from dioxide import deprecated

        @deprecated(since='2.0.0', removed_in='3.0.0')
        def old_function() -> None:
            pass

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter('always')
            old_function()

        assert len(caught) == 1
        assert 'test_deprecation_infra.py' in caught[0].filename
