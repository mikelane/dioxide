"""Tests for the @lifecycle decorator."""

from typing import Protocol

import pytest

from dioxide import (
    Profile,
    adapter,
    lifecycle,
    service,
)


class DescribeLifecycleDecorator:
    """Tests for @lifecycle decorator functionality."""

    def it_marks_class_with_lifecycle_attribute(self) -> None:
        """Decorator adds _dioxide_lifecycle attribute to class."""

        @lifecycle
        class Database:
            async def initialize(self) -> None:
                pass

            async def dispose(self) -> None:
                pass

        assert hasattr(Database, '_dioxide_lifecycle')
        assert Database._dioxide_lifecycle is True

    def it_validates_initialize_method_exists(self) -> None:
        """Decorator raises TypeError if initialize() method is missing."""

        with pytest.raises(TypeError, match=r'must implement.*initialize'):

            @lifecycle  # type: ignore[arg-type]
            class Database:
                async def dispose(self) -> None:
                    pass

    def it_validates_initialize_is_async(self) -> None:
        """Decorator raises TypeError if initialize() is not async."""

        with pytest.raises(TypeError, match=r'initialize.*must be async'):

            @lifecycle  # type: ignore[arg-type]
            class Database:
                def initialize(self) -> None:  # Not async!
                    pass

                async def dispose(self) -> None:
                    pass

    def it_validates_dispose_method_exists(self) -> None:
        """Decorator raises TypeError if dispose() method is missing."""

        with pytest.raises(TypeError, match=r'must implement.*dispose'):

            @lifecycle  # type: ignore[arg-type]
            class Database:
                async def initialize(self) -> None:
                    pass

    def it_validates_dispose_is_async(self) -> None:
        """Decorator raises TypeError if dispose() is not async."""

        with pytest.raises(TypeError, match=r'dispose.*must be async'):

            @lifecycle  # type: ignore[arg-type]
            class Database:
                async def initialize(self) -> None:
                    pass

                def dispose(self) -> None:  # Not async!
                    pass

    def it_works_with_service_decorator(self) -> None:
        """Decorator can be stacked with @service decorator."""

        @service
        @lifecycle
        class Database:
            async def initialize(self) -> None:
                pass

            async def dispose(self) -> None:
                pass

        assert hasattr(Database, '_dioxide_lifecycle')
        assert Database._dioxide_lifecycle is True

    def it_works_with_adapter_decorator(self) -> None:
        """Decorator can be stacked with @adapter.for_() decorator."""

        class CachePort(Protocol):
            async def get(self, key: str) -> str | None: ...

        @adapter.for_(CachePort, profile=Profile.PRODUCTION)
        @lifecycle
        class RedisAdapter:
            async def initialize(self) -> None:
                pass

            async def dispose(self) -> None:
                pass

            async def get(self, key: str) -> str | None:
                return None

        assert hasattr(RedisAdapter, '_dioxide_lifecycle')
        assert RedisAdapter._dioxide_lifecycle is True
