"""Tests for the @lifecycle decorator."""

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
