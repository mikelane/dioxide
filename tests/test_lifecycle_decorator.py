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

    def it_validates_initialize_is_async(self) -> None:
        """Decorator raises TypeError if initialize() is not async."""

        with pytest.raises(TypeError, match=r'initialize.*must be async'):

            @lifecycle
            class Database:
                def initialize(self) -> None:  # Not async!
                    pass

                async def dispose(self) -> None:
                    pass

    def it_validates_dispose_method_exists(self) -> None:
        """Decorator raises TypeError if dispose() method is missing."""

        with pytest.raises(TypeError, match=r'must implement.*dispose'):

            @lifecycle
            class Database:
                async def initialize(self) -> None:
                    pass
