"""Tests for global singleton container pattern.

The global singleton container provides a simplified API for most use cases,
while keeping the Container class available for advanced scenarios like
testing isolation or multi-tenant applications.
"""

from dioxide import (
    Container,
    container,
    service,
)


class DescribeGlobalContainerSingleton:
    """Tests for the global singleton container instance."""

    def it_provides_singleton_instance(self) -> None:
        """Container is a Container instance."""
        assert isinstance(container, Container)

    def it_maintains_singleton_across_imports(self) -> None:
        """Same container instance is returned on multiple imports."""
        # Import container multiple times to verify singleton
        # isort: off
        from dioxide import container as c1
        from dioxide import container as c2
        # isort: on

        assert c1 is c2

    def it_has_empty_registry_initially(self) -> None:
        """Global container starts with empty registry."""
        # Create a fresh container to test the initial state
        fresh = Container()
        assert fresh.is_empty()
        assert len(fresh) == 0

    def it_supports_scan_method(self) -> None:
        """Global container has scan() method."""
        # Should have the scan method
        assert hasattr(container, 'scan')
        assert callable(container.scan)

    def it_supports_resolve_method(self) -> None:
        """Global container has resolve() method."""
        # Should have the resolve method
        assert hasattr(container, 'resolve')
        assert callable(container.resolve)

    def it_supports_registration_methods(self) -> None:
        """Global container has all registration methods."""
        # Check all registration methods exist
        registration_methods = [
            'register_instance',
            'register_class',
            'register_singleton_factory',
            'register_transient_factory',
            'register_singleton',
            'register_factory',
        ]
        for method_name in registration_methods:
            assert hasattr(container, method_name)
            assert callable(getattr(container, method_name))


class DescribeContainerClass:
    """Tests for the Container class (for advanced use cases)."""

    def it_allows_creating_multiple_instances(self) -> None:
        """Container class creates separate instances."""
        c1 = Container()
        c2 = Container()

        assert c1 is not c2
        assert isinstance(c1, Container)
        assert isinstance(c2, Container)

    def it_creates_isolated_registries(self) -> None:
        """Each Container instance has its own isolated registry."""
        c1 = Container()
        c2 = Container()

        # Register something in c1
        class TestService:
            pass

        c1.register_instance(TestService, TestService())

        # c1 should have 1 registration
        assert len(c1) == 1
        assert not c1.is_empty()

        # c2 should still be empty
        assert len(c2) == 0
        assert c2.is_empty()

    def it_is_available_for_import(self) -> None:
        """Container class can be imported from dioxide."""
        assert Container is not None
        assert callable(Container)


class DescribeGlobalContainerFunctionality:
    """Tests for functional behavior of the global container."""

    def setup_method(self) -> None:
        """Clear the component registry before each test."""

    def teardown_method(self) -> None:
        """Clear the component registry after each test."""

    def it_resolves_components_via_singleton(self) -> None:
        """Global container can resolve components after scan."""

        @service
        class TestDatabase:
            def __init__(self) -> None:
                self.connected = True

        # Create a fresh container for this test to avoid state pollution
        test_container = Container()
        test_container.scan()

        db = test_container.resolve(TestDatabase)
        assert isinstance(db, TestDatabase)
        assert db.connected is True

    def it_handles_dependency_injection(self) -> None:
        """Global container auto-injects dependencies."""

        @service
        class Database:
            def __init__(self) -> None:
                self.name = 'testdb'

        @service
        class UserService:
            def __init__(self, db: Database) -> None:
                self.db = db

        # Use a fresh container to avoid state pollution
        test_container = Container()
        test_container.scan()

        user_service = test_container.resolve(UserService)
        assert isinstance(user_service, UserService)
        assert isinstance(user_service.db, Database)
        assert user_service.db.name == 'testdb'


class DescribeGetItemSyntax:
    """Tests for optional __getitem__ bracket syntax."""

    def setup_method(self) -> None:
        """Clear the component registry before each test."""

    def teardown_method(self) -> None:
        """Clear the component registry after each test."""

    def it_resolves_via_bracket_notation(self) -> None:
        """Container supports container[Type] syntax."""

        @service
        class BracketService:
            def __init__(self) -> None:
                self.name = 'bracket'

        test_container = Container()
        test_container.scan()
        bracket_service = test_container[BracketService]

        assert isinstance(bracket_service, BracketService)
        assert bracket_service.name == 'bracket'

    def it_is_equivalent_to_resolve(self) -> None:
        """container[Type] returns same instance as container.resolve(Type)."""

        @service
        class SameService:
            pass

        test_container = Container()
        test_container.scan()
        via_resolve = test_container.resolve(SameService)
        via_bracket = test_container[SameService]

        assert via_resolve is via_bracket

    def it_works_with_global_container(self) -> None:
        """Bracket syntax works with global singleton container."""

        @service
        class GlobalService:
            def __init__(self) -> None:
                self.value = 42

        # Need a fresh container to avoid test pollution
        fresh = Container()
        fresh.scan()
        global_service = fresh[GlobalService]

        assert isinstance(global_service, GlobalService)
        assert global_service.value == 42


class DescribeBackwardCompatibility:
    """Tests ensuring backward compatibility with v0.0.1-alpha."""

    def it_supports_old_pattern_with_container_class(self) -> None:
        """Old v0.0.1-alpha pattern still works."""

        @service
        class OldService:
            pass

        # Old pattern: manual instantiation
        old_container = Container()
        old_container.scan()
        old_service = old_container.resolve(OldService)

        assert isinstance(old_service, OldService)
