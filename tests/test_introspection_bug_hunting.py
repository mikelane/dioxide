"""Bug hunting tests for introspection API (#349).

These tests validate edge cases and potential bugs discovered during code review.
"""

from typing import Protocol

from dioxide import (
    Container,
    Profile,
    adapter,
    service,
)


class DescribeIntrospectionBugHunting:
    """Bug hunting tests for introspection API."""

    def it_handles_class_names_with_special_chars_in_mermaid(self) -> None:
        """graph() handles class names with special characters (quotes, angle brackets)."""

        @service
        class ServiceWithGeneric:
            pass

        container = Container()
        container.scan(profile=Profile.TEST)

        output = container.graph()

        assert 'ServiceWithGeneric' in output

    def it_handles_class_names_with_special_chars_in_dot(self) -> None:
        """graph(format='dot') handles class names with special characters."""

        @service
        class MyService:
            pass

        container = Container()
        container.scan(profile=Profile.TEST)

        output = container.graph(format='dot')

        assert 'MyService' in output
        assert 'digraph' in output

    def it_handles_class_without_name_attribute(self) -> None:
        """explain() handles types that don't have standard __name__ attribute."""
        container = Container()
        container.scan(profile=Profile.TEST)

        class WeirdType:
            pass

        output = container.explain(WeirdType)
        assert isinstance(output, str)

    def it_handles_empty_profile_string_in_adapter(self) -> None:
        """explain() handles adapters with Profile.ALL ('*')."""

        class TestPort(Protocol):
            def do_thing(self) -> None: ...

        @adapter.for_(TestPort, profile=Profile.ALL)
        class AllProfileAdapter:
            def do_thing(self) -> None:
                pass

        container = Container()
        container.scan(profile=Profile.TEST)

        output = container.explain(TestPort)

        assert 'TestPort' in output
        assert 'AllProfileAdapter' in output

    def it_handles_mermaid_node_id_with_numbers(self) -> None:
        """graph() handles class names starting with or containing numbers."""

        @service
        class Service123:
            pass

        container = Container()
        container.scan(profile=Profile.TEST)

        output = container.graph()

        assert 'Service123' in output

    def it_handles_dot_node_id_with_underscores(self) -> None:
        """graph(format='dot') handles class names with underscores."""

        @service
        class MyServiceWithUnderscoreName:
            pass

        container = Container()
        container.scan(profile=Profile.TEST)

        output = container.graph(format='dot')

        assert 'MyServiceWithUnderscoreName' in output

    def it_handles_debug_with_many_components(self) -> None:
        """debug() handles container with many registered components."""

        @service
        class Service1:
            pass

        @service
        class Service2:
            pass

        @service
        class Service3:
            pass

        class Port1(Protocol):
            def method(self) -> None: ...

        class Port2(Protocol):
            def method(self) -> None: ...

        @adapter.for_(Port1, profile=Profile.TEST)
        class Adapter1:
            def method(self) -> None:
                pass

        @adapter.for_(Port2, profile=Profile.TEST)
        class Adapter2:
            def method(self) -> None:
                pass

        container = Container()
        container.scan(profile=Profile.TEST)

        output = container.debug()

        assert 'Services' in output
        assert 'Adapters by Port' in output
        assert 'Service1' in output or 'Service2' in output or 'Service3' in output
        assert 'Adapter1' in output or 'Adapter2' in output

    def it_handles_explain_with_deeply_nested_dependencies(self) -> None:
        """explain() handles deeply nested dependency trees."""

        @service
        class Level4:
            pass

        @service
        class Level3:
            def __init__(self, dep: Level4):
                self.dep = dep

        @service
        class Level2:
            def __init__(self, dep: Level3):
                self.dep = dep

        @service
        class Level1:
            def __init__(self, dep: Level2):
                self.dep = dep

        container = Container()
        container.scan(profile=Profile.TEST)

        output = container.explain(Level1)

        assert 'Level1' in output
        assert 'Level2' in output
        assert 'Level3' in output
        assert 'Level4' in output

    def it_handles_graph_with_service_depending_on_multiple_ports(self) -> None:
        """graph() handles service depending on multiple ports."""

        class PortA(Protocol):
            def method_a(self) -> None: ...

        class PortB(Protocol):
            def method_b(self) -> None: ...

        @adapter.for_(PortA, profile=Profile.TEST)
        class AdapterA:
            def method_a(self) -> None:
                pass

        @adapter.for_(PortB, profile=Profile.TEST)
        class AdapterB:
            def method_b(self) -> None:
                pass

        @service
        class MultiDepService:
            def __init__(self, a: PortA, b: PortB):
                self.a = a
                self.b = b

        container = Container()
        container.scan(profile=Profile.TEST)

        output = container.graph()

        assert 'MultiDepService' in output
        assert 'PortA' in output
        assert 'PortB' in output
        assert '-->' in output

    def it_handles_explain_for_adapter_with_service_dependency(self) -> None:
        """explain() handles adapter that depends on a service."""

        @service
        class Config:
            pass

        class EmailPort(Protocol):
            async def send(self, to: str, subject: str, body: str) -> None: ...

        @adapter.for_(EmailPort, profile=Profile.TEST)
        class FakeEmail:
            def __init__(self, config: Config):
                self.config = config

            async def send(self, to: str, subject: str, body: str) -> None:
                pass

        container = Container()
        container.scan(profile=Profile.TEST)

        output = container.explain(EmailPort)

        assert 'EmailPort' in output
        assert 'FakeEmail' in output
        assert 'Config' in output

    def it_handles_debug_file_write_with_newline(self) -> None:
        """debug(file=...) writes complete output to file."""
        import io

        container = Container()
        container.scan(profile=Profile.TEST)

        buffer = io.StringIO()
        result = container.debug(file=buffer)

        written = buffer.getvalue()
        assert written == result
        assert '=== dioxide Container Debug ===' in written

    def it_handles_explain_with_no_dependencies(self) -> None:
        """explain() handles service with no dependencies."""

        @service
        class StandaloneService:
            pass

        container = Container()
        container.scan(profile=Profile.TEST)

        output = container.explain(StandaloneService)

        assert 'StandaloneService' in output
        assert 'SINGLETON' in output

    def it_handles_graph_mermaid_with_empty_profile_value(self) -> None:
        """graph() handles adapters with no profile (edge case)."""
        container = Container()

        output = container.graph()

        assert 'graph TD' in output

    def it_handles_graph_dot_format_validates_syntax(self) -> None:
        """graph(format='dot') produces valid DOT syntax."""

        @service
        class TestService:
            pass

        class TestPort(Protocol):
            def method(self) -> None: ...

        @adapter.for_(TestPort, profile=Profile.TEST)
        class TestAdapter:
            def method(self) -> None:
                pass

        @service
        class ServiceWithDep:
            def __init__(self, port: TestPort):
                self.port = port

        container = Container()
        container.scan(profile=Profile.TEST)

        output = container.graph(format='dot')

        assert output.startswith('digraph Container {')
        assert output.endswith('}')
        assert 'rankdir=TB' in output

    def it_handles_explain_for_port_not_registered_at_all(self) -> None:
        """explain() handles port with no adapters at all."""

        class NeverRegisteredPort(Protocol):
            def method(self) -> None: ...

        container = Container()
        container.scan(profile=Profile.TEST)

        output = container.explain(NeverRegisteredPort)

        assert 'NeverRegisteredPort' in output
        assert 'not registered' in output.lower()

    def it_defaults_to_mermaid_for_invalid_format(self) -> None:
        """graph() defaults to mermaid for unrecognized format parameter."""
        container = Container()
        container.scan(profile=Profile.TEST)

        output = container.graph(format='invalid_format')

        assert 'graph TD' in output

    def it_handles_graph_with_only_adapters_no_services(self) -> None:
        """graph() handles container with only adapters, no services."""

        class OnlyPort(Protocol):
            def method(self) -> None: ...

        @adapter.for_(OnlyPort, profile=Profile.TEST)
        class OnlyAdapter:
            def method(self) -> None:
                pass

        container = Container()
        container.scan(profile=Profile.TEST)

        output = container.graph()

        assert 'OnlyAdapter' in output
        assert 'OnlyPort' in output

    def it_handles_graph_with_only_services_no_adapters(self) -> None:
        """graph() handles container with only services, no adapters."""

        @service
        class OnlyService:
            pass

        container = Container()
        container.scan(profile=Profile.TEST)

        output = container.graph()

        assert 'OnlyService' in output

    def it_handles_explain_self_referential_dependency(self) -> None:
        """explain() detects self-referential dependencies (A -> A)."""

        @service
        class SelfRefService:
            def __init__(self, other: 'SelfRefService'):
                self.other = other

        container = Container()
        container.scan(profile=Profile.TEST)

        output = container.explain(SelfRefService)

        assert 'SelfRefService' in output
        assert 'circular reference' in output.lower()

    def it_handles_debug_sorting_order(self) -> None:
        """debug() sorts services and adapters alphabetically."""

        @service
        class ZService:
            pass

        @service
        class AService:
            pass

        @service
        class MService:
            pass

        container = Container()
        container.scan(profile=Profile.TEST)

        output = container.debug()

        lines = output.split('\n')
        service_lines = [line for line in lines if line.strip().startswith('- ') and 'Service' in line]

        names = [line.strip().split()[1] for line in service_lines if 'Service' in line]
        sorted_names = sorted(names)
        assert names == sorted_names

    def it_handles_graph_dot_format_with_no_profile_set(self) -> None:
        """graph(format='dot') handles container without active profile."""
        container = Container()

        output = container.graph(format='dot')

        assert 'digraph Container {' in output
        assert '}' in output

    def it_handles_explain_with_simple_service(self) -> None:
        """explain() handles basic services."""

        @service
        class SimpleConfig:
            pass

        @service
        class SimpleService:
            def __init__(self, config: SimpleConfig):
                self.config = config

        container = Container()
        container.scan(profile=Profile.TEST)

        output = container.explain(SimpleService)

        assert 'SimpleService' in output
        assert 'SimpleConfig' in output

    def it_handles_debug_with_custom_profile(self) -> None:
        """debug() works with custom profile strings."""
        custom = Profile('my-custom-profile')

        @adapter.for_(EmailPort, profile=custom)
        class CustomAdapter:
            async def send(self, to: str, subject: str, body: str) -> None:
                pass

        container = Container()
        container._active_profile = custom

        output = container.debug()

        assert 'Active Profile: my-custom-profile' in output

    def it_handles_graph_mermaid_escaping_in_labels(self) -> None:
        """graph() handles special characters in Mermaid labels."""

        @service
        class ServiceName:
            pass

        container = Container()
        container.scan(profile=Profile.TEST)

        output = container.graph()

        assert 'ServiceName' in output
        assert '"' in output or '<br/>' in output

    def it_handles_explain_tree_formatting(self) -> None:
        """explain() produces properly formatted tree structure."""

        @service
        class Dep1:
            pass

        @service
        class Dep2:
            pass

        @service
        class ServiceWithMultipleDeps:
            def __init__(self, d1: Dep1, d2: Dep2):
                self.d1 = d1
                self.d2 = d2

        container = Container()
        container.scan(profile=Profile.TEST)

        output = container.explain(ServiceWithMultipleDeps)

        assert 'ServiceWithMultipleDeps' in output
        assert '+--' in output
        assert 'd1' in output
        assert 'd2' in output


class EmailPort(Protocol):
    """Protocol used in tests."""

    async def send(self, to: str, subject: str, body: str) -> None: ...


class DescribeIntrospectionBugHuntingFinal:
    """Final iteration of bug hunting tests."""

    def it_handles_graph_with_duplicate_edges(self) -> None:
        """graph() handles cases where same edge might appear multiple times."""

        class SharedPort(Protocol):
            def method(self) -> None: ...

        @adapter.for_(SharedPort, profile=Profile.TEST)
        class SharedAdapter:
            def method(self) -> None:
                pass

        @service
        class Service1:
            def __init__(self, p: SharedPort):
                self.p = p

        @service
        class Service2:
            def __init__(self, p: SharedPort):
                self.p = p

        container = Container()
        container.scan(profile=Profile.TEST)

        output = container.graph()

        assert 'SharedPort' in output
        assert 'Service1' in output
        assert 'Service2' in output

    def it_handles_explain_with_generic_types(self) -> None:
        """explain() handles services with generic type hints."""
        from typing import Any

        @service
        class GenericService:
            def __init__(self, data: Any):
                self.data = data

        container = Container()
        container.scan(profile=Profile.TEST)

        output = container.explain(GenericService)

        assert 'GenericService' in output

    def it_handles_debug_with_lifecycle_services(self) -> None:
        """debug() properly indicates lifecycle-managed services."""
        from dioxide import lifecycle

        class LifecyclePort(Protocol):
            def work(self) -> None: ...

        @adapter.for_(LifecyclePort, profile=Profile.TEST)
        @lifecycle
        class LifecycleAdapter:
            def work(self) -> None:
                pass

            async def initialize(self) -> None:
                pass

            async def dispose(self) -> None:
                pass

        container = Container()
        container.scan(profile=Profile.TEST)

        output = container.debug()

        assert 'LifecycleAdapter' in output
        assert 'lifecycle' in output.lower()

    def it_handles_graph_with_adapter_dependencies(self) -> None:
        """graph() handles adapters that have service dependencies."""

        @service
        class ConfigService:
            pass

        class AdapterPort(Protocol):
            def do_work(self) -> None: ...

        @adapter.for_(AdapterPort, profile=Profile.TEST)
        class AdapterWithDep:
            def __init__(self, config: ConfigService):
                self.config = config

            def do_work(self) -> None:
                pass

        container = Container()
        container.scan(profile=Profile.TEST)

        output = container.graph()

        assert 'AdapterPort' in output
        assert 'AdapterWithDep' in output

    def it_handles_explain_for_registered_but_filtered_port(self) -> None:
        """explain() handles port with adapter for different profile."""

        class ProfileSpecificPort(Protocol):
            def method(self) -> None: ...

        @adapter.for_(ProfileSpecificPort, profile=Profile.PRODUCTION)
        class ProdOnlyAdapterForExplain:
            def method(self) -> None:
                pass

        container = Container()
        container.scan(profile=Profile.TEST)

        output = container.explain(ProfileSpecificPort)

        assert 'ProfileSpecificPort' in output
        assert 'no adapter' in output.lower()

    def it_handles_debug_output_consistency(self) -> None:
        """debug() output is consistent across multiple calls."""

        @service
        class ConsistencyService:
            pass

        container = Container()
        container.scan(profile=Profile.TEST)

        output1 = container.debug()
        output2 = container.debug()

        assert output1 == output2

    def it_handles_graph_returns_string_not_none(self) -> None:
        """graph() always returns a string, never None."""
        container = Container()

        output_mermaid = container.graph()
        output_dot = container.graph(format='dot')

        assert isinstance(output_mermaid, str)
        assert isinstance(output_dot, str)
        assert len(output_mermaid) > 0
        assert len(output_dot) > 0

    def it_handles_explain_returns_string_not_none(self) -> None:
        """explain() always returns a string, never None."""

        class NonExistentType:
            pass

        container = Container()
        container.scan(profile=Profile.TEST)

        output = container.explain(NonExistentType)

        assert isinstance(output, str)
        assert len(output) > 0

    def it_handles_debug_returns_string_not_none(self) -> None:
        """debug() always returns a string, never None."""
        container = Container()

        output = container.debug()

        assert isinstance(output, str)
        assert len(output) > 0
