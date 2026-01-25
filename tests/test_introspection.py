"""Tests for container introspection API (#316, #349).

The introspection API provides methods to inspect container state for debugging:
- list_registered(): List all registered ports
- is_registered(port): Check if a port has an adapter
- get_adapters_for(port): Get adapters by profile for a port
- active_profile: Get the current container profile
- debug(): Print a summary of all registered components (#349)
- explain(cls): Show resolution tree for a type (#349)
- graph(format): Generate dependency graph in Mermaid or DOT format (#349)
"""

from typing import Protocol

from dioxide import (
    Container,
    Profile,
    adapter,
    service,
)


class EmailPort(Protocol):
    """Test protocol for email functionality."""

    async def send(self, to: str, subject: str, body: str) -> None:
        """Send an email."""
        ...


class CachePort(Protocol):
    """Test protocol for cache functionality."""

    def get(self, key: str) -> str | None:
        """Get a cached value."""
        ...

    def set(self, key: str, value: str) -> None:
        """Set a cached value."""
        ...


class DescribeListRegistered:
    """Tests for Container.list_registered() method."""

    def it_returns_empty_list_for_empty_container(self) -> None:
        """list_registered() returns empty list when no types are registered."""
        container = Container()

        result = container.list_registered()

        assert result == []

    def it_returns_registered_port_types(self) -> None:
        """list_registered() returns ports that have registered adapters."""

        @adapter.for_(EmailPort, profile=Profile.PRODUCTION)
        class SendGridAdapter:
            async def send(self, to: str, subject: str, body: str) -> None:
                pass

        container = Container()
        container.scan(profile=Profile.PRODUCTION)

        result = container.list_registered()

        assert EmailPort in result

    def it_returns_registered_service_types(self) -> None:
        """list_registered() returns services that are registered."""

        @service
        class UserService:
            pass

        container = Container()
        container.scan(profile=Profile.PRODUCTION)

        result = container.list_registered()

        assert UserService in result

    def it_returns_all_registered_types(self) -> None:
        """list_registered() returns both services and port types."""

        @adapter.for_(EmailPort, profile=Profile.PRODUCTION)
        class SendGridAdapter:
            async def send(self, to: str, subject: str, body: str) -> None:
                pass

        @service
        class UserService:
            pass

        container = Container()
        container.scan(profile=Profile.PRODUCTION)

        result = container.list_registered()

        assert EmailPort in result
        assert UserService in result
        assert len(result) == 2


class DescribeIsRegistered:
    """Tests for Container.is_registered() method."""

    def it_returns_false_for_unregistered_type(self) -> None:
        """is_registered() returns False for types not in the container."""
        container = Container()

        result = container.is_registered(EmailPort)

        assert result is False

    def it_returns_true_for_registered_port(self) -> None:
        """is_registered() returns True for registered ports."""

        @adapter.for_(EmailPort, profile=Profile.PRODUCTION)
        class SendGridAdapter:
            async def send(self, to: str, subject: str, body: str) -> None:
                pass

        container = Container()
        container.scan(profile=Profile.PRODUCTION)

        result = container.is_registered(EmailPort)

        assert result is True

    def it_returns_true_for_registered_service(self) -> None:
        """is_registered() returns True for registered services."""

        @service
        class UserService:
            pass

        container = Container()
        container.scan(profile=Profile.PRODUCTION)

        result = container.is_registered(UserService)

        assert result is True


class DescribeActiveProfile:
    """Tests for Container.active_profile property."""

    def it_returns_none_before_scan(self) -> None:
        """active_profile is None before scan is called."""
        container = Container()

        result = container.active_profile

        assert result is None

    def it_returns_profile_after_scan(self) -> None:
        """active_profile returns the profile used in scan()."""
        container = Container()
        container.scan(profile=Profile.PRODUCTION)

        result = container.active_profile

        assert result == Profile.PRODUCTION

    def it_returns_test_profile_when_scanned_with_test(self) -> None:
        """active_profile returns TEST when scanned with Profile.TEST."""
        container = Container()
        container.scan(profile=Profile.TEST)

        result = container.active_profile

        assert result == Profile.TEST

    def it_returns_profile_when_initialized_with_profile(self) -> None:
        """active_profile returns profile when container created with profile."""
        container = Container(profile=Profile.DEVELOPMENT)

        result = container.active_profile

        assert result == Profile.DEVELOPMENT

    def it_returns_profile_for_custom_string_profile(self) -> None:
        """active_profile returns Profile instance for custom string profiles."""
        container = Container()
        # Manually set a custom profile (extensible Profile supports any string)
        container._active_profile = 'custom-environment'

        result = container.active_profile

        # Custom profiles are valid Profile instances (Profile is extensible)
        assert result == Profile('custom-environment')
        assert isinstance(result, Profile)


class DescribeGetAdaptersFor:
    """Tests for Container.get_adapters_for() method."""

    def it_returns_empty_dict_for_unregistered_port(self) -> None:
        """get_adapters_for() returns empty dict for unregistered ports."""
        container = Container()

        result = container.get_adapters_for(EmailPort)

        assert result == {}

    def it_returns_adapter_for_active_profile(self) -> None:
        """get_adapters_for() returns the adapter for the active profile."""

        @adapter.for_(EmailPort, profile=Profile.PRODUCTION)
        class SendGridAdapter:
            async def send(self, to: str, subject: str, body: str) -> None:
                pass

        container = Container()
        container.scan(profile=Profile.PRODUCTION)

        result = container.get_adapters_for(EmailPort)

        assert Profile.PRODUCTION in result
        assert result[Profile.PRODUCTION] is SendGridAdapter

    def it_shows_all_profile_adapters_from_global_registry(self) -> None:
        """get_adapters_for() shows adapters from all profiles in global registry."""

        @adapter.for_(EmailPort, profile=Profile.PRODUCTION)
        class SendGridAdapter:
            async def send(self, to: str, subject: str, body: str) -> None:
                pass

        @adapter.for_(EmailPort, profile=Profile.TEST)
        class FakeEmailAdapter:
            async def send(self, to: str, subject: str, body: str) -> None:
                pass

        # Even with only production profile scanned, show all registered adapters
        container = Container()
        container.scan(profile=Profile.PRODUCTION)

        result = container.get_adapters_for(EmailPort)

        # Both adapters should be visible for debugging
        assert Profile.PRODUCTION in result
        assert result[Profile.PRODUCTION] is SendGridAdapter
        assert Profile.TEST in result
        assert result[Profile.TEST] is FakeEmailAdapter

    def it_returns_empty_dict_for_service_type(self) -> None:
        """get_adapters_for() returns empty dict for service types (not ports)."""

        @service
        class UserService:
            pass

        container = Container()
        container.scan(profile=Profile.PRODUCTION)

        result = container.get_adapters_for(UserService)

        assert result == {}


# =============================================================================
# Issue #349: Container Introspection API - debug(), explain(), graph()
# =============================================================================


class DescribeContainerDebug:
    """Tests for Container.debug() method.

    The debug() method returns a human-readable summary of all registered
    components, including services, adapters, and active profile.
    """

    def it_returns_string_with_container_summary(self) -> None:
        """debug() returns a formatted string summary."""
        container = Container()
        container.scan(profile=Profile.TEST)

        output = container.debug()

        assert isinstance(output, str)
        assert '=== dioxide Container Debug ===' in output
        assert 'Active Profile: test' in output

    def it_shows_none_profile_when_not_scanned(self) -> None:
        """debug() shows 'none' for profile when container is not scanned."""
        container = Container()

        output = container.debug()

        assert 'Active Profile: none' in output

    def it_lists_registered_services(self) -> None:
        """debug() lists services that are registered."""

        @service
        class UserService:
            pass

        container = Container()
        container.scan(profile=Profile.TEST)

        output = container.debug()

        assert 'Services' in output
        assert 'UserService' in output

    def it_shows_service_scope(self) -> None:
        """debug() shows the scope of each service."""
        from dioxide import Scope

        @service(scope=Scope.FACTORY)
        class RequestHandler:
            pass

        container = Container()
        container.scan(profile=Profile.TEST)

        output = container.debug()

        assert 'RequestHandler' in output
        assert 'FACTORY' in output

    def it_groups_adapters_by_port(self) -> None:
        """debug() groups adapters by their port type."""

        @adapter.for_(EmailPort, profile=Profile.TEST)
        class FakeEmail:
            async def send(self, to: str, subject: str, body: str) -> None:
                pass

        container = Container()
        container.scan(profile=Profile.TEST)

        output = container.debug()

        assert 'Adapters by Port' in output
        assert 'EmailPort' in output
        assert 'FakeEmail' in output

    def it_shows_adapter_profiles(self) -> None:
        """debug() shows which profiles each adapter is registered for."""

        @adapter.for_(EmailPort, profile=[Profile.TEST, Profile.DEVELOPMENT])
        class FakeEmail:
            async def send(self, to: str, subject: str, body: str) -> None:
                pass

        container = Container()
        container.scan(profile=Profile.TEST)

        output = container.debug()

        assert 'FakeEmail' in output
        assert 'test' in output.lower()

    def it_shows_lifecycle_indicator(self) -> None:
        """debug() indicates components with lifecycle management."""
        from dioxide import lifecycle

        @adapter.for_(EmailPort, profile=Profile.TEST)
        @lifecycle
        class FakeEmail:
            async def send(self, to: str, subject: str, body: str) -> None:
                pass

            async def initialize(self) -> None:
                pass

            async def dispose(self) -> None:
                pass

        container = Container()
        container.scan(profile=Profile.TEST)

        output = container.debug()

        assert 'lifecycle' in output.lower()


class DescribeContainerExplain:
    """Tests for Container.explain() method.

    The explain() method shows how a type would be resolved, including
    the resolution path, which adapter/service is selected, and all
    transitive dependencies.
    """

    def it_shows_resolution_tree_for_service(self) -> None:
        """explain() shows the resolution tree for a service."""

        @service
        class UserService:
            pass

        container = Container()
        container.scan(profile=Profile.TEST)

        output = container.explain(UserService)

        assert isinstance(output, str)
        assert 'UserService' in output

    def it_shows_service_dependencies(self) -> None:
        """explain() shows dependencies of a service."""

        @adapter.for_(EmailPort, profile=Profile.TEST)
        class FakeEmail:
            async def send(self, to: str, subject: str, body: str) -> None:
                pass

        @service
        class UserService:
            def __init__(self, email: EmailPort):
                self.email = email

        container = Container()
        container.scan(profile=Profile.TEST)

        output = container.explain(UserService)

        assert 'UserService' in output
        assert 'EmailPort' in output
        assert 'FakeEmail' in output

    def it_shows_port_resolution_with_adapter(self) -> None:
        """explain() shows which adapter implements a port."""

        @adapter.for_(EmailPort, profile=Profile.TEST)
        class FakeEmail:
            async def send(self, to: str, subject: str, body: str) -> None:
                pass

        container = Container()
        container.scan(profile=Profile.TEST)

        output = container.explain(EmailPort)

        assert 'EmailPort' in output
        assert 'FakeEmail' in output

    def it_shows_scope_information(self) -> None:
        """explain() shows the scope of each component."""

        @service
        class UserService:
            pass

        container = Container()
        container.scan(profile=Profile.TEST)

        output = container.explain(UserService)

        assert 'SINGLETON' in output

    def it_shows_transitive_dependencies(self) -> None:
        """explain() shows nested/transitive dependencies."""

        @service
        class Config:
            pass

        @adapter.for_(EmailPort, profile=Profile.TEST)
        class FakeEmail:
            def __init__(self, config: Config):
                self.config = config

            async def send(self, to: str, subject: str, body: str) -> None:
                pass

        @service
        class UserService:
            def __init__(self, email: EmailPort):
                self.email = email

        container = Container()
        container.scan(profile=Profile.TEST)

        output = container.explain(UserService)

        assert 'UserService' in output
        assert 'EmailPort' in output
        assert 'FakeEmail' in output
        assert 'Config' in output

    def it_handles_unregistered_type(self) -> None:
        """explain() provides helpful message for unregistered types."""
        container = Container()
        container.scan(profile=Profile.TEST)

        output = container.explain(EmailPort)

        assert 'not registered' in output.lower() or 'EmailPort' in output


class DescribeContainerGraph:
    """Tests for Container.graph() method.

    The graph() method generates a dependency graph visualization
    in Mermaid or DOT format.
    """

    def it_returns_mermaid_format_by_default(self) -> None:
        """graph() returns Mermaid format by default."""
        container = Container()
        container.scan(profile=Profile.TEST)

        output = container.graph()

        assert isinstance(output, str)
        assert 'graph TD' in output

    def it_supports_dot_format(self) -> None:
        """graph() supports DOT format when requested."""
        container = Container()
        container.scan(profile=Profile.TEST)

        output = container.graph(format='dot')

        assert 'digraph' in output

    def it_includes_services_in_graph(self) -> None:
        """graph() includes registered services."""

        @service
        class UserService:
            pass

        container = Container()
        container.scan(profile=Profile.TEST)

        output = container.graph()

        assert 'UserService' in output

    def it_includes_ports_in_graph(self) -> None:
        """graph() includes ports (protocols)."""

        @adapter.for_(EmailPort, profile=Profile.TEST)
        class FakeEmail:
            async def send(self, to: str, subject: str, body: str) -> None:
                pass

        container = Container()
        container.scan(profile=Profile.TEST)

        output = container.graph()

        assert 'EmailPort' in output

    def it_shows_dependency_edges(self) -> None:
        """graph() shows edges between components and their dependencies."""

        @adapter.for_(EmailPort, profile=Profile.TEST)
        class FakeEmail:
            async def send(self, to: str, subject: str, body: str) -> None:
                pass

        @service
        class UserService:
            def __init__(self, email: EmailPort):
                self.email = email

        container = Container()
        container.scan(profile=Profile.TEST)

        output = container.graph()

        # Mermaid edge syntax: ServiceA --> PortB
        assert 'UserService' in output
        assert 'EmailPort' in output
        assert '-->' in output

    def it_uses_subgraphs_to_organize_components(self) -> None:
        """graph() uses subgraphs to separate services, ports, and adapters."""

        @adapter.for_(EmailPort, profile=Profile.TEST)
        class FakeEmail:
            async def send(self, to: str, subject: str, body: str) -> None:
                pass

        @service
        class UserService:
            pass

        container = Container()
        container.scan(profile=Profile.TEST)

        output = container.graph()

        assert 'subgraph' in output

    def it_shows_port_adapter_edges_with_dotted_lines(self) -> None:
        """graph() shows port-to-adapter edges with dotted line style."""

        @adapter.for_(EmailPort, profile=Profile.TEST)
        class FakeEmail:
            async def send(self, to: str, subject: str, body: str) -> None:
                pass

        container = Container()
        container.scan(profile=Profile.TEST)

        output = container.graph()

        # Mermaid uses -.-> for dotted edges
        assert '-.->' in output

    def it_generates_dot_format_with_subgraphs(self) -> None:
        """graph(format='dot') generates DOT format with cluster subgraphs."""

        @adapter.for_(EmailPort, profile=Profile.TEST)
        class FakeEmail:
            async def send(self, to: str, subject: str, body: str) -> None:
                pass

        @service
        class UserService:
            pass

        container = Container()
        container.scan(profile=Profile.TEST)

        output = container.graph(format='dot')

        assert 'digraph Container' in output
        assert 'cluster_services' in output
        assert 'cluster_ports' in output
        assert 'cluster_adapters' in output

    def it_generates_dot_format_with_service_nodes(self) -> None:
        """graph(format='dot') includes service nodes with scope labels."""

        @service
        class UserService:
            pass

        container = Container()
        container.scan(profile=Profile.TEST)

        output = container.graph(format='dot')

        assert 'UserService' in output
        assert 'label=' in output

    def it_generates_dot_format_with_port_nodes(self) -> None:
        """graph(format='dot') includes port nodes with diamond shape."""

        @adapter.for_(EmailPort, profile=Profile.TEST)
        class FakeEmail:
            async def send(self, to: str, subject: str, body: str) -> None:
                pass

        container = Container()
        container.scan(profile=Profile.TEST)

        output = container.graph(format='dot')

        assert 'EmailPort' in output
        assert 'shape=diamond' in output

    def it_generates_dot_format_with_adapter_nodes(self) -> None:
        """graph(format='dot') includes adapter nodes with profile labels."""

        @adapter.for_(EmailPort, profile=Profile.TEST)
        class FakeEmail:
            async def send(self, to: str, subject: str, body: str) -> None:
                pass

        container = Container()
        container.scan(profile=Profile.TEST)

        output = container.graph(format='dot')

        assert 'FakeEmail' in output

    def it_generates_dot_format_with_dependency_edges(self) -> None:
        """graph(format='dot') includes edges between services and ports."""

        @adapter.for_(EmailPort, profile=Profile.TEST)
        class FakeEmail:
            async def send(self, to: str, subject: str, body: str) -> None:
                pass

        @service
        class UserService:
            def __init__(self, email: EmailPort):
                self.email = email

        container = Container()
        container.scan(profile=Profile.TEST)

        output = container.graph(format='dot')

        # DOT syntax: ServiceA -> PortB;
        assert 'UserService -> EmailPort' in output

    def it_generates_dot_format_with_dashed_port_adapter_edges(self) -> None:
        """graph(format='dot') shows port-to-adapter edges with dashed style."""

        @adapter.for_(EmailPort, profile=Profile.TEST)
        class FakeEmail:
            async def send(self, to: str, subject: str, body: str) -> None:
                pass

        container = Container()
        container.scan(profile=Profile.TEST)

        output = container.graph(format='dot')

        # DOT syntax for dashed edges
        assert 'style=dashed' in output

    def it_filters_out_of_profile_adapters_in_dot(self) -> None:
        """graph(format='dot') filters adapters not matching current profile."""

        @adapter.for_(EmailPort, profile=Profile.PRODUCTION)
        class ProdEmail:
            async def send(self, to: str, subject: str, body: str) -> None:
                pass

        @adapter.for_(CachePort, profile=Profile.TEST)
        class TestCache:
            def get(self, key: str) -> str | None:
                return None

            def set(self, key: str, value: str) -> None:
                pass

        container = Container()
        container.scan(profile=Profile.TEST)

        output = container.graph(format='dot')

        # ProdEmail should be filtered out (wrong profile)
        assert 'ProdEmail' not in output
        # TestCache should be included
        assert 'TestCache' in output


class DescribeContainerDebugEdgeCases:
    """Additional edge case tests for Container.debug() method."""

    def it_writes_output_to_file_when_provided(self) -> None:
        """debug() writes output to file object when file parameter provided."""
        import io

        container = Container()
        container.scan(profile=Profile.TEST)

        output_buffer = io.StringIO()
        result = container.debug(file=output_buffer)

        # Should both write to file and return string
        assert result == output_buffer.getvalue()
        assert '=== dioxide Container Debug ===' in output_buffer.getvalue()

    def it_shows_all_adapters_from_registry_for_debugging(self) -> None:
        """debug() shows all adapters from global registry for debugging visibility."""

        @adapter.for_(EmailPort, profile=Profile.PRODUCTION)
        class ProdEmail:
            async def send(self, to: str, subject: str, body: str) -> None:
                pass

        container = Container()
        container.scan(profile=Profile.TEST)

        output = container.debug()

        # debug() shows all adapters for debugging, even from other profiles
        # This is intentional - helps debug why resolution might fail
        assert 'ProdEmail' in output
        assert 'production' in output.lower()


class DescribeContainerExplainEdgeCases:
    """Additional edge case tests for Container.explain() method."""

    def it_detects_circular_dependencies(self) -> None:
        """explain() shows circular reference when cycles detected."""
        # We need to create classes where both types are resolvable
        # The circular detection happens when explain recursively visits
        # a type that was already visited in the current path

        # Create a service that depends on itself (self-referencing)
        @service
        class SelfRefService:
            def __init__(self, other: 'SelfRefService'):
                self.other = other

        container = Container()
        container.scan(profile=Profile.TEST)

        output = container.explain(SelfRefService)

        # The first appearance will show the service
        # The second (recursive) appearance will show circular reference
        assert 'SelfRefService' in output
        assert 'circular reference' in output.lower()

    def it_shows_no_adapter_message_for_missing_adapter(self) -> None:
        """explain() shows 'no adapter' when port has no adapter for profile."""

        class UnimplementedPort(Protocol):
            def do_something(self) -> None: ...

        # Register an adapter for a different profile
        @adapter.for_(UnimplementedPort, profile=Profile.PRODUCTION)
        class ProdOnlyAdapter:
            def do_something(self) -> None:
                pass

        container = Container()
        container.scan(profile=Profile.TEST)

        output = container.explain(UnimplementedPort)

        assert 'no adapter' in output.lower()

    def it_handles_type_hint_errors_gracefully(self) -> None:
        """explain() handles classes with problematic type hints gracefully."""

        @service
        class ServiceWithNoInit:
            pass

        container = Container()
        container.scan(profile=Profile.TEST)

        # Should not raise, should produce output
        output = container.explain(ServiceWithNoInit)

        assert 'ServiceWithNoInit' in output


class DescribeContainerGraphEdgeCases:
    """Additional edge case tests for Container.graph() method."""

    def it_handles_empty_container_mermaid(self) -> None:
        """graph() returns minimal Mermaid output for empty container."""
        container = Container()

        output = container.graph()

        assert 'graph TD' in output

    def it_handles_empty_container_dot(self) -> None:
        """graph(format='dot') returns minimal DOT output for empty container."""
        container = Container()

        output = container.graph(format='dot')

        assert 'digraph Container' in output
        assert '}' in output

    def it_filters_services_not_matching_profile_in_mermaid(self) -> None:
        """graph() filters services not matching the active profile."""

        @adapter.for_(EmailPort, profile=Profile.PRODUCTION)
        class ProdEmail:
            async def send(self, to: str, subject: str, body: str) -> None:
                pass

        container = Container()
        container.scan(profile=Profile.TEST)

        output = container.graph()

        # ProdEmail should be filtered out
        assert 'ProdEmail' not in output

    def it_filters_services_not_matching_profile_in_dot(self) -> None:
        """graph(format='dot') filters services not matching the active profile."""

        @adapter.for_(EmailPort, profile=Profile.PRODUCTION)
        class ProdEmail:
            async def send(self, to: str, subject: str, body: str) -> None:
                pass

        container = Container()
        container.scan(profile=Profile.TEST)

        output = container.graph(format='dot')

        # ProdEmail should be filtered out
        assert 'ProdEmail' not in output
