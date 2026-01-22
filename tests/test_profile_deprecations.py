"""Tests for Profile deprecation warnings (Issue #311).

Tests for deprecation warnings when using non-canonical profile patterns.

Canonical patterns (no warnings):
- profile=Profile.PRODUCTION (single enum)
- profile=[Profile.TEST, Profile.DEVELOPMENT] (list of enums)
- profile=Profile.ALL (all profiles)

Deprecated patterns (emit warnings):
- profile="production" (string instead of enum)
- profile='*' (star string instead of Profile.ALL)
"""

from __future__ import annotations

import warnings
from typing import Protocol

from dioxide import (
    Profile,
    adapter,
)


class DescribeProfileDeprecations:
    """Deprecation warnings for non-canonical profile patterns."""

    class DescribeStringProfiles:
        """When using string instead of Profile enum."""

        def it_emits_deprecation_warning_for_string_profile(self) -> None:
            """Using profile='production' emits deprecation warning."""

            class EmailPort(Protocol):
                def send(self) -> None: ...

            with warnings.catch_warnings(record=True) as caught_warnings:
                warnings.simplefilter('always')

                @adapter.for_(EmailPort, profile='production')
                class StringProfileAdapter:
                    def send(self) -> None:
                        pass

            deprecation_warnings = [w for w in caught_warnings if issubclass(w.category, DeprecationWarning)]
            assert len(deprecation_warnings) == 1
            assert 'Profile.PRODUCTION' in str(deprecation_warnings[0].message)

        def it_emits_deprecation_warning_for_test_string(self) -> None:
            """Using profile='test' emits deprecation warning suggesting Profile.TEST."""

            class CachePort(Protocol):
                def get(self, key: str) -> str | None: ...

            with warnings.catch_warnings(record=True) as caught_warnings:
                warnings.simplefilter('always')

                @adapter.for_(CachePort, profile='test')
                class StringTestAdapter:
                    def get(self, key: str) -> str | None:
                        return None

            deprecation_warnings = [w for w in caught_warnings if issubclass(w.category, DeprecationWarning)]
            assert len(deprecation_warnings) == 1
            assert 'Profile.TEST' in str(deprecation_warnings[0].message)

        def it_emits_deprecation_warning_for_development_string(self) -> None:
            """Using profile='development' emits deprecation warning."""

            class LogPort(Protocol):
                def log(self, msg: str) -> None: ...

            with warnings.catch_warnings(record=True) as caught_warnings:
                warnings.simplefilter('always')

                @adapter.for_(LogPort, profile='development')
                class DevLogAdapter:
                    def log(self, msg: str) -> None:
                        pass

            deprecation_warnings = [w for w in caught_warnings if issubclass(w.category, DeprecationWarning)]
            assert len(deprecation_warnings) == 1
            assert 'Profile.DEVELOPMENT' in str(deprecation_warnings[0].message)

        def it_emits_deprecation_warning_for_staging_string(self) -> None:
            """Using profile='staging' emits deprecation warning."""

            class QueuePort(Protocol):
                def push(self, item: str) -> None: ...

            with warnings.catch_warnings(record=True) as caught_warnings:
                warnings.simplefilter('always')

                @adapter.for_(QueuePort, profile='staging')
                class StagingQueueAdapter:
                    def push(self, item: str) -> None:
                        pass

            deprecation_warnings = [w for w in caught_warnings if issubclass(w.category, DeprecationWarning)]
            assert len(deprecation_warnings) == 1
            assert 'Profile.STAGING' in str(deprecation_warnings[0].message)

        def it_emits_deprecation_warning_for_ci_string(self) -> None:
            """Using profile='ci' emits deprecation warning."""

            class MetricsPort(Protocol):
                def record(self, name: str, value: float) -> None: ...

            with warnings.catch_warnings(record=True) as caught_warnings:
                warnings.simplefilter('always')

                @adapter.for_(MetricsPort, profile='ci')
                class CIMetricsAdapter:
                    def record(self, name: str, value: float) -> None:
                        pass

            deprecation_warnings = [w for w in caught_warnings if issubclass(w.category, DeprecationWarning)]
            assert len(deprecation_warnings) == 1
            assert 'Profile.CI' in str(deprecation_warnings[0].message)

        def it_emits_warning_for_custom_string_profile(self) -> None:
            """Using profile='custom' emits generic deprecation warning."""

            class StoragePort(Protocol):
                def store(self, data: str) -> None: ...

            with warnings.catch_warnings(record=True) as caught_warnings:
                warnings.simplefilter('always')

                @adapter.for_(StoragePort, profile='custom')
                class CustomStorageAdapter:
                    def store(self, data: str) -> None:
                        pass

            deprecation_warnings = [w for w in caught_warnings if issubclass(w.category, DeprecationWarning)]
            assert len(deprecation_warnings) == 1
            assert 'Profile enum' in str(deprecation_warnings[0].message)

        def it_emits_warnings_for_list_of_strings(self) -> None:
            """Using profile=['test', 'development'] emits deprecation warnings."""

            class NotificationPort(Protocol):
                def notify(self, msg: str) -> None: ...

            with warnings.catch_warnings(record=True) as caught_warnings:
                warnings.simplefilter('always')

                @adapter.for_(NotificationPort, profile=['test', 'development'])
                class StringListAdapter:
                    def notify(self, msg: str) -> None:
                        pass

            deprecation_warnings = [w for w in caught_warnings if issubclass(w.category, DeprecationWarning)]
            # Should emit one warning about using Profile enum instead
            assert len(deprecation_warnings) >= 1
            warning_text = str(deprecation_warnings[0].message)
            assert 'Profile' in warning_text

    class DescribeStarWildcard:
        """When using '*' instead of Profile.ALL."""

        def it_emits_deprecation_warning_for_star_string(self) -> None:
            """Using profile='*' emits deprecation warning suggesting Profile.ALL."""

            class UtilityPort(Protocol):
                def run(self) -> None: ...

            with warnings.catch_warnings(record=True) as caught_warnings:
                warnings.simplefilter('always')

                @adapter.for_(UtilityPort, profile='*')
                class StarWildcardAdapter:
                    def run(self) -> None:
                        pass

            deprecation_warnings = [w for w in caught_warnings if issubclass(w.category, DeprecationWarning)]
            assert len(deprecation_warnings) == 1
            assert 'Profile.ALL' in str(deprecation_warnings[0].message)


class DescribeCanonicalPatterns:
    """Canonical patterns work without warnings."""

    def it_accepts_profile_enum_without_warning(self) -> None:
        """Using profile=Profile.PRODUCTION does not emit warning."""

        class EmailPort(Protocol):
            def send(self) -> None: ...

        with warnings.catch_warnings(record=True) as caught_warnings:
            warnings.simplefilter('always')

            @adapter.for_(EmailPort, profile=Profile.PRODUCTION)
            class EnumProfileAdapter:
                def send(self) -> None:
                    pass

        deprecation_warnings = [w for w in caught_warnings if issubclass(w.category, DeprecationWarning)]
        assert len(deprecation_warnings) == 0

    def it_accepts_profile_test_enum_without_warning(self) -> None:
        """Using profile=Profile.TEST does not emit warning."""

        class CachePort(Protocol):
            def get(self, key: str) -> str | None: ...

        with warnings.catch_warnings(record=True) as caught_warnings:
            warnings.simplefilter('always')

            @adapter.for_(CachePort, profile=Profile.TEST)
            class TestEnumAdapter:
                def get(self, key: str) -> str | None:
                    return None

        deprecation_warnings = [w for w in caught_warnings if issubclass(w.category, DeprecationWarning)]
        assert len(deprecation_warnings) == 0

    def it_accepts_profile_list_of_enums_without_warning(self) -> None:
        """Using profile=[Profile.TEST, Profile.DEVELOPMENT] does not emit warning."""

        class LogPort(Protocol):
            def log(self, msg: str) -> None: ...

        with warnings.catch_warnings(record=True) as caught_warnings:
            warnings.simplefilter('always')

            @adapter.for_(LogPort, profile=[Profile.TEST, Profile.DEVELOPMENT])
            class EnumListAdapter:
                def log(self, msg: str) -> None:
                    pass

        deprecation_warnings = [w for w in caught_warnings if issubclass(w.category, DeprecationWarning)]
        assert len(deprecation_warnings) == 0

    def it_accepts_profile_all_enum_without_warning(self) -> None:
        """Using profile=Profile.ALL does not emit warning."""

        class UtilityPort(Protocol):
            def run(self) -> None: ...

        with warnings.catch_warnings(record=True) as caught_warnings:
            warnings.simplefilter('always')

            @adapter.for_(UtilityPort, profile=Profile.ALL)
            class AllEnumAdapter:
                def run(self) -> None:
                    pass

        deprecation_warnings = [w for w in caught_warnings if issubclass(w.category, DeprecationWarning)]
        assert len(deprecation_warnings) == 0

    def it_accepts_single_enum_in_list_without_warning(self) -> None:
        """Using profile=[Profile.PRODUCTION] does not emit warning."""

        class DatabasePort(Protocol):
            def query(self, sql: str) -> list[dict[str, object]]: ...

        with warnings.catch_warnings(record=True) as caught_warnings:
            warnings.simplefilter('always')

            @adapter.for_(DatabasePort, profile=[Profile.PRODUCTION])
            class SingleEnumListAdapter:
                def query(self, sql: str) -> list[dict[str, object]]:
                    return []

        deprecation_warnings = [w for w in caught_warnings if issubclass(w.category, DeprecationWarning)]
        assert len(deprecation_warnings) == 0


class DescribeDeprecationWarningStackLevel:
    """Deprecation warnings point to user code, not dioxide internals."""

    def it_points_to_decorator_usage_not_dioxide_internals(self) -> None:
        """Warning stacklevel points to the @adapter.for_() usage."""

        class TestPort(Protocol):
            def test(self) -> None: ...

        with warnings.catch_warnings(record=True) as caught_warnings:
            warnings.simplefilter('always')

            @adapter.for_(TestPort, profile='production')
            class StackLevelTestAdapter:
                def test(self) -> None:
                    pass

        deprecation_warnings = [w for w in caught_warnings if issubclass(w.category, DeprecationWarning)]
        assert len(deprecation_warnings) == 1
        # The warning should come from this test file, not from adapter.py
        assert 'test_profile_deprecations.py' in deprecation_warnings[0].filename


class DescribeMixedPatterns:
    """Mixed patterns with both valid and deprecated values."""

    def it_emits_warning_for_mixed_enum_and_string_list(self) -> None:
        """Using profile=[Profile.TEST, 'development'] emits warning for string."""

        class MixedPort(Protocol):
            def process(self) -> None: ...

        with warnings.catch_warnings(record=True) as caught_warnings:
            warnings.simplefilter('always')

            @adapter.for_(MixedPort, profile=[Profile.TEST, 'development'])
            class MixedListAdapter:
                def process(self) -> None:
                    pass

        deprecation_warnings = [w for w in caught_warnings if issubclass(w.category, DeprecationWarning)]
        # Should emit warning for the string 'development'
        assert len(deprecation_warnings) >= 1
        warning_text = str(deprecation_warnings[0].message)
        assert 'development' in warning_text.lower() or 'Profile' in warning_text
