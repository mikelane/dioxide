"""Tests for multi-binding / collection injection feature (#255).

Multi-binding allows registering multiple adapters for the same port
and injecting them as a collection via list[Port] type hint.

Use case: Plugin systems where multiple implementations should be collected
rather than selecting one based on profile.
"""

from typing import Protocol

from dioxide import (
    Container,
    Profile,
    adapter,
    service,
)


class GremlinOperator(Protocol):
    """Test protocol for mutation operators."""

    def can_mutate(self, node: str) -> bool:
        """Check if this operator can mutate the given node type."""
        ...

    def mutate(self, node: str) -> list[str]:
        """Produce mutations for the given node."""
        ...


class DescribeMultiBindingDecorator:
    """Tests for @adapter.for_() with multi=True parameter."""

    def it_stores_multi_flag_on_class(self) -> None:
        """The multi=True parameter stores __dioxide_multi__ = True on the class."""

        @adapter.for_(GremlinOperator, multi=True)
        class ComparisonOperator:
            def can_mutate(self, node: str) -> bool:
                return node == 'comparison'

            def mutate(self, node: str) -> list[str]:
                return ['mutated']

        assert hasattr(ComparisonOperator, '__dioxide_multi__')
        assert ComparisonOperator.__dioxide_multi__ is True  # pyright: ignore[reportAttributeAccessIssue]

    def it_defaults_multi_to_false(self) -> None:
        """Without multi=True, __dioxide_multi__ defaults to False."""

        @adapter.for_(GremlinOperator, profile='production')
        class SingleAdapter:
            def can_mutate(self, node: str) -> bool:
                return True

            def mutate(self, node: str) -> list[str]:
                return []

        assert hasattr(SingleAdapter, '__dioxide_multi__')
        assert SingleAdapter.__dioxide_multi__ is False  # pyright: ignore[reportAttributeAccessIssue]

    def it_stores_priority_on_class(self) -> None:
        """The priority=N parameter stores __dioxide_priority__ = N on the class."""

        @adapter.for_(GremlinOperator, multi=True, priority=10)
        class PriorityOperator:
            def can_mutate(self, node: str) -> bool:
                return True

            def mutate(self, node: str) -> list[str]:
                return []

        assert hasattr(PriorityOperator, '__dioxide_priority__')
        assert PriorityOperator.__dioxide_priority__ == 10  # pyright: ignore[reportAttributeAccessIssue]

    def it_defaults_priority_to_zero(self) -> None:
        """Without priority parameter, __dioxide_priority__ defaults to 0."""

        @adapter.for_(GremlinOperator, multi=True)
        class DefaultPriorityOperator:
            def can_mutate(self, node: str) -> bool:
                return True

            def mutate(self, node: str) -> list[str]:
                return []

        assert hasattr(DefaultPriorityOperator, '__dioxide_priority__')
        assert DefaultPriorityOperator.__dioxide_priority__ == 0  # pyright: ignore[reportAttributeAccessIssue]


class DescribeMultiBindingResolution:
    """Tests for resolving multi-bindings via list[Port] type hint."""

    def it_resolves_all_multi_adapters_as_list(self) -> None:
        """Container resolves list[Port] to list containing all multi=True adapters."""

        class PluginPort(Protocol):
            def name(self) -> str: ...

        @adapter.for_(PluginPort, multi=True)
        class PluginA:
            def name(self) -> str:
                return 'A'

        @adapter.for_(PluginPort, multi=True)
        class PluginB:
            def name(self) -> str:
                return 'B'

        container = Container()
        container.scan(profile=Profile.PRODUCTION)

        plugins: list[PluginPort] = container.resolve(list[PluginPort])

        assert isinstance(plugins, list)
        assert len(plugins) == 2
        names = {p.name() for p in plugins}
        assert names == {'A', 'B'}

    def it_injects_multi_bindings_into_service_constructor(self) -> None:
        """Services with list[Port] type hints receive all multi=True adapters."""

        class OperatorPort(Protocol):
            def operate(self) -> str: ...

        @adapter.for_(OperatorPort, multi=True)
        class AddOperator:
            def operate(self) -> str:
                return 'add'

        @adapter.for_(OperatorPort, multi=True)
        class SubtractOperator:
            def operate(self) -> str:
                return 'subtract'

        @service
        class Calculator:
            def __init__(self, operators: list[OperatorPort]) -> None:
                self.operators = operators

            def available_operations(self) -> set[str]:
                return {op.operate() for op in self.operators}

        container = Container()
        container.scan(profile=Profile.PRODUCTION)

        calc = container.resolve(Calculator)

        assert calc.available_operations() == {'add', 'subtract'}

    def it_orders_multi_bindings_by_priority_ascending(self) -> None:
        """Multi-bindings are ordered by priority (lower values first)."""

        class PipelineStep(Protocol):
            def name(self) -> str: ...

        @adapter.for_(PipelineStep, multi=True, priority=30)
        class LastStep:
            def name(self) -> str:
                return 'last'

        @adapter.for_(PipelineStep, multi=True, priority=10)
        class FirstStep:
            def name(self) -> str:
                return 'first'

        @adapter.for_(PipelineStep, multi=True, priority=20)
        class MiddleStep:
            def name(self) -> str:
                return 'middle'

        container = Container()
        container.scan(profile=Profile.PRODUCTION)

        steps: list[PipelineStep] = container.resolve(list[PipelineStep])

        names = [s.name() for s in steps]
        assert names == ['first', 'middle', 'last']


class DescribeMultiBindingProfileFiltering:
    """Tests for profile filtering with multi-bindings."""

    def it_filters_multi_bindings_by_active_profile(self) -> None:
        """Only multi-bindings matching active profile are included."""

        class ProcessorPort(Protocol):
            def process(self) -> str: ...

        @adapter.for_(ProcessorPort, multi=True, profile=Profile.PRODUCTION)
        class ProductionProcessor:
            def process(self) -> str:
                return 'production'

        @adapter.for_(ProcessorPort, multi=True, profile=Profile.TEST)
        class TestProcessor:
            def process(self) -> str:
                return 'test'

        @adapter.for_(ProcessorPort, multi=True, profile=Profile.ALL)
        class UniversalProcessor:
            def process(self) -> str:
                return 'universal'

        # Production profile should only get production and universal
        prod_container = Container()
        prod_container.scan(profile=Profile.PRODUCTION)
        prod_processors: list[ProcessorPort] = prod_container.resolve(list[ProcessorPort])
        prod_results = {p.process() for p in prod_processors}
        assert prod_results == {'production', 'universal'}

        # Test profile should only get test and universal
        test_container = Container()
        test_container.scan(profile=Profile.TEST)
        test_processors: list[ProcessorPort] = test_container.resolve(list[ProcessorPort])
        test_results = {p.process() for p in test_processors}
        assert test_results == {'test', 'universal'}


class DescribeMultiBindingErrors:
    """Tests for error conditions with multi-bindings."""

    def it_raises_error_when_port_has_both_single_and_multi_adapters(self) -> None:
        """Error at startup if same port has single and multi registrations."""
        import pytest

        class MixedPort(Protocol):
            def action(self) -> str: ...

        @adapter.for_(MixedPort, profile=Profile.PRODUCTION)  # Single binding
        class SingleAdapter:
            def action(self) -> str:
                return 'single'

        @adapter.for_(MixedPort, multi=True, profile=Profile.PRODUCTION)  # Multi binding
        class MultiAdapter:
            def action(self) -> str:
                return 'multi'

        container = Container()

        with pytest.raises(ValueError, match=r'has both single adapters.*and multi-binding adapters'):
            container.scan(profile=Profile.PRODUCTION)


class DescribeMultiBindingEmptyCollection:
    """Tests for empty collection handling with multi-bindings."""

    def it_returns_empty_list_when_no_multi_bindings_registered(self) -> None:
        """Resolving list[Port] returns empty list if no implementations exist."""

        class UnimplementedPort(Protocol):
            def do_something(self) -> None: ...

        container = Container()
        container.scan(profile=Profile.PRODUCTION)

        plugins: list[UnimplementedPort] = container.resolve(list[UnimplementedPort])

        assert isinstance(plugins, list)
        assert len(plugins) == 0


class DescribeMultiBindingEdgeCases:
    """Tests for edge cases with multi-bindings."""

    def it_supports_negative_priority_values(self) -> None:
        """Negative priority values are valid and sort before zero."""

        class StepPort(Protocol):
            def name(self) -> str: ...

        @adapter.for_(StepPort, multi=True, priority=-10)
        class EarlyStep:
            def name(self) -> str:
                return 'early'

        @adapter.for_(StepPort, multi=True, priority=0)
        class NormalStep:
            def name(self) -> str:
                return 'normal'

        container = Container()
        container.scan(profile=Profile.PRODUCTION)

        steps: list[StepPort] = container.resolve(list[StepPort])
        names = [s.name() for s in steps]
        assert names == ['early', 'normal']

    def it_injects_dependencies_into_multi_binding_adapters(self) -> None:
        """Multi-binding adapters can have their own dependencies injected."""

        class ConfigPort(Protocol):
            @property
            def value(self) -> str: ...

        @adapter.for_(ConfigPort, profile=Profile.PRODUCTION)
        class ProductionConfig:
            @property
            def value(self) -> str:
                return 'prod-config'

        class HandlerPort(Protocol):
            def handle(self) -> str: ...

        @adapter.for_(HandlerPort, multi=True)
        class ConfigAwareHandler:
            def __init__(self, config: ConfigPort) -> None:
                self.config = config

            def handle(self) -> str:
                return f'handled-{self.config.value}'

        container = Container()
        container.scan(profile=Profile.PRODUCTION)

        handlers: list[HandlerPort] = container.resolve(list[HandlerPort])
        assert len(handlers) == 1
        assert handlers[0].handle() == 'handled-prod-config'

    def it_maintains_stable_sort_order_for_same_priority(self) -> None:
        """Adapters with same priority maintain a consistent order (by registration order)."""

        class EqualPriorityPort(Protocol):
            def id(self) -> str: ...

        @adapter.for_(EqualPriorityPort, multi=True, priority=0)
        class HandlerA:
            def id(self) -> str:
                return 'A'

        @adapter.for_(EqualPriorityPort, multi=True, priority=0)
        class HandlerB:
            def id(self) -> str:
                return 'B'

        @adapter.for_(EqualPriorityPort, multi=True, priority=0)
        class HandlerC:
            def id(self) -> str:
                return 'C'

        container = Container()
        container.scan(profile=Profile.PRODUCTION)

        handlers: list[EqualPriorityPort] = container.resolve(list[EqualPriorityPort])
        ids = [h.id() for h in handlers]

        # Order should be consistent across calls
        handlers2: list[EqualPriorityPort] = container.resolve(list[EqualPriorityPort])
        ids2 = [h.id() for h in handlers2]

        assert ids == ids2
        assert set(ids) == {'A', 'B', 'C'}

    def it_supports_multi_binding_with_factory_scope(self) -> None:
        """Multi-bindings with FACTORY scope create new instances each resolution."""
        from dioxide import Scope

        class FactoryPort(Protocol):
            @property
            def instance_id(self) -> int: ...

        counter = {'value': 0}

        @adapter.for_(FactoryPort, multi=True, scope=Scope.FACTORY)
        class FactoryAdapter:
            def __init__(self) -> None:
                counter['value'] += 1
                self._id = counter['value']

            @property
            def instance_id(self) -> int:
                return self._id

        container = Container()
        container.scan(profile=Profile.PRODUCTION)

        first_list: list[FactoryPort] = container.resolve(list[FactoryPort])
        second_list: list[FactoryPort] = container.resolve(list[FactoryPort])

        # Each resolution creates new instances
        assert first_list[0].instance_id != second_list[0].instance_id
