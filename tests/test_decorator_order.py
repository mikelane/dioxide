"""Tests verifying that dioxide decorator order is irrelevant.

dioxide decorators (@service, @adapter.for_(), @lifecycle) work in any order because
they only add attributes to the decorated class without wrapping or modifying behavior.

This test module explicitly verifies both decorator orderings work identically, serving as:
1. Regression tests ensuring order-independence is maintained
2. Living documentation of the order-agnostic design
3. Verification that users can apply decorators in any order

Why Order Does Not Matter:
    Unlike decorators that wrap classes (metaclasses, class transformers), dioxide
    decorators simply add metadata attributes:
    - @lifecycle adds _dioxide_lifecycle = True
    - @service adds __dioxide_profiles__ and __dioxide_scope__
    - @adapter.for_() adds __dioxide_port__, __dioxide_profiles__, __dioxide_scope__

    Since each decorator only reads the class and adds its own attributes, the decorators
    are fully commutative - order of application is irrelevant to functionality.

Recommended Convention:
    For consistency and readability, we recommend @lifecycle as the innermost decorator:

        @adapter.for_(Port, profile=Profile.PRODUCTION)
        @lifecycle
        class MyAdapter: ...

        @service
        @lifecycle
        class MyService: ...

    This convention reads naturally: "register an adapter that has lifecycle management."
"""

from typing import Protocol

import pytest

from dioxide import (
    Container,
    Profile,
    adapter,
    lifecycle,
    service,
)


class DescribeDecoratorOrderWithAdapter:
    """Verify @adapter.for_() and @lifecycle work in any order."""

    @pytest.mark.asyncio
    async def it_works_with_lifecycle_innermost(self) -> None:
        """@adapter.for_() outer, @lifecycle inner works correctly."""
        events: list[str] = []

        class DatabasePort(Protocol):
            def query(self) -> str: ...

        @adapter.for_(DatabasePort, profile=Profile.PRODUCTION)
        @lifecycle
        class LifecycleInnermost:
            async def initialize(self) -> None:
                events.append('initialized')

            async def dispose(self) -> None:
                events.append('disposed')

            def query(self) -> str:
                return 'result'

        container = Container()
        container.scan(profile=Profile.PRODUCTION)

        async with container:
            instance = container.resolve(DatabasePort)
            assert instance.query() == 'result'
            assert 'initialized' in events

        assert 'disposed' in events

    @pytest.mark.asyncio
    async def it_works_with_lifecycle_outermost(self) -> None:
        """@lifecycle outer, @adapter.for_() inner works correctly."""
        events: list[str] = []

        class CachePort(Protocol):
            def get(self) -> str: ...

        @lifecycle
        @adapter.for_(CachePort, profile=Profile.TEST)
        class LifecycleOutermost:
            async def initialize(self) -> None:
                events.append('initialized')

            async def dispose(self) -> None:
                events.append('disposed')

            def get(self) -> str:
                return 'cached'

        container = Container()
        container.scan(profile=Profile.TEST)

        async with container:
            instance = container.resolve(CachePort)
            assert instance.get() == 'cached'
            assert 'initialized' in events

        assert 'disposed' in events

    def it_sets_same_attributes_regardless_of_order(self) -> None:
        """Both orders set identical class attributes."""

        class EmailPort(Protocol):
            def send(self) -> None: ...

        @adapter.for_(EmailPort, profile=Profile.DEVELOPMENT)
        @lifecycle
        class OrderA:
            async def initialize(self) -> None:
                pass

            async def dispose(self) -> None:
                pass

            def send(self) -> None:
                pass

        @lifecycle
        @adapter.for_(EmailPort, profile=Profile.DEVELOPMENT)
        class OrderB:
            async def initialize(self) -> None:
                pass

            async def dispose(self) -> None:
                pass

            def send(self) -> None:
                pass

        # Both have lifecycle attribute
        assert getattr(OrderA, '_dioxide_lifecycle', None) is True
        assert getattr(OrderB, '_dioxide_lifecycle', None) is True

        # Both have adapter attributes
        assert getattr(OrderA, '__dioxide_port__', None) is EmailPort
        assert getattr(OrderB, '__dioxide_port__', None) is EmailPort

        # Both have same profiles
        assert getattr(OrderA, '__dioxide_profiles__', None) == frozenset({'development'})
        assert getattr(OrderB, '__dioxide_profiles__', None) == frozenset({'development'})


class DescribeDecoratorOrderWithService:
    """Verify @service and @lifecycle work in any order."""

    @pytest.mark.asyncio
    async def it_works_with_lifecycle_innermost(self) -> None:
        """@service outer, @lifecycle inner works correctly."""
        events: list[str] = []

        @service
        @lifecycle
        class ServiceLifecycleInner:
            async def initialize(self) -> None:
                events.append('initialized')

            async def dispose(self) -> None:
                events.append('disposed')

            def do_work(self) -> str:
                return 'done'

        container = Container()
        container.scan(profile=Profile.PRODUCTION)

        async with container:
            instance = container.resolve(ServiceLifecycleInner)
            assert instance.do_work() == 'done'
            assert 'initialized' in events

        assert 'disposed' in events

    @pytest.mark.asyncio
    async def it_works_with_lifecycle_outermost(self) -> None:
        """@lifecycle outer, @service inner works correctly."""
        events: list[str] = []

        @lifecycle
        @service
        class ServiceLifecycleOuter:
            async def initialize(self) -> None:
                events.append('initialized')

            async def dispose(self) -> None:
                events.append('disposed')

            def do_work(self) -> str:
                return 'done'

        container = Container()
        container.scan(profile=Profile.TEST)

        async with container:
            instance = container.resolve(ServiceLifecycleOuter)
            assert instance.do_work() == 'done'
            assert 'initialized' in events

        assert 'disposed' in events

    def it_sets_same_attributes_regardless_of_order(self) -> None:
        """Both orders set identical class attributes."""

        @service
        @lifecycle
        class ServiceOrderA:
            async def initialize(self) -> None:
                pass

            async def dispose(self) -> None:
                pass

        @lifecycle
        @service
        class ServiceOrderB:
            async def initialize(self) -> None:
                pass

            async def dispose(self) -> None:
                pass

        # Both have lifecycle attribute
        assert getattr(ServiceOrderA, '_dioxide_lifecycle', None) is True
        assert getattr(ServiceOrderB, '_dioxide_lifecycle', None) is True

        # Both have service profiles (wildcard for all profiles)
        assert getattr(ServiceOrderA, '__dioxide_profiles__', None) == frozenset(['*'])
        assert getattr(ServiceOrderB, '__dioxide_profiles__', None) == frozenset(['*'])


class DescribeDecoratorOrderDesign:
    """Document WHY decorator order is irrelevant (design verification)."""

    def it_demonstrates_decorators_only_add_attributes(self) -> None:
        """Decorators add attributes without wrapping or transforming the class."""

        class SamplePort(Protocol):
            def method(self) -> None: ...

        # Get original class identity
        class Original:
            async def initialize(self) -> None:
                pass

            async def dispose(self) -> None:
                pass

            def method(self) -> None:
                pass

        original_id = id(Original)

        # Apply lifecycle
        after_lifecycle = lifecycle(Original)
        # Same class object, just with attribute added
        assert id(after_lifecycle) == original_id
        assert after_lifecycle is Original

        # Now create fresh class for adapter test
        class Original2:
            async def initialize(self) -> None:
                pass

            async def dispose(self) -> None:
                pass

            def method(self) -> None:
                pass

        original2_id = id(Original2)

        # Apply adapter
        decorator = adapter.for_(SamplePort, profile=Profile.TEST)
        after_adapter = decorator(Original2)
        # Same class object, just with attributes added
        assert id(after_adapter) == original2_id
        assert after_adapter is Original2

    def it_demonstrates_decorators_are_commutative(self) -> None:
        """Order of application produces identical results (commutativity)."""

        class Port(Protocol):
            def run(self) -> None: ...

        # Order 1: adapter then lifecycle
        @adapter.for_(Port, profile=Profile.PRODUCTION)
        @lifecycle
        class Order1:
            async def initialize(self) -> None:
                pass

            async def dispose(self) -> None:
                pass

            def run(self) -> None:
                pass

        # Order 2: lifecycle then adapter
        @lifecycle
        @adapter.for_(Port, profile=Profile.PRODUCTION)
        class Order2:
            async def initialize(self) -> None:
                pass

            async def dispose(self) -> None:
                pass

            def run(self) -> None:
                pass

        # Extract all dioxide attributes
        dioxide_attrs = ['_dioxide_lifecycle', '__dioxide_port__', '__dioxide_profiles__', '__dioxide_scope__']

        for attr in dioxide_attrs:
            val1 = getattr(Order1, attr, 'MISSING')
            val2 = getattr(Order2, attr, 'MISSING')
            assert val1 == val2, f'{attr} differs: {val1} vs {val2}'
