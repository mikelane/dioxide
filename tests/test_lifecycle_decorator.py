"""Tests for the @lifecycle decorator."""

import pytest

from dioxide import lifecycle


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

            @lifecycle
            class Database:
                async def dispose(self) -> None:
                    pass
