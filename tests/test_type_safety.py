"""Runtime tests for type safety and type inference."""


from dioxide import Container, Scope, component


class DescribeContainerResolveTypeInference:
    """Tests that Container.resolve() provides correct type inference."""

    def it_infers_the_correct_type_for_simple_classes(self) -> None:
        """Container.resolve() returns correctly typed instances."""
        container = Container()

        class UserService:
            def get_user(self, user_id: int) -> str:
                return f'User {user_id}'

        container.register_singleton(UserService, lambda: UserService())

        # This should work and mypy should infer service as UserService
        service = container.resolve(UserService)

        # Verify runtime behavior
        assert isinstance(service, UserService)
        assert service.get_user(1) == 'User 1'

        # This test passes if mypy infers the type correctly
        # mypy should know that service.get_user() exists

    def it_preserves_type_information_through_dependency_injection(self) -> None:
        """Type inference works through dependency chains."""
        container = Container()

        class UserRepository:
            def find(self, user_id: int) -> str:
                return f'User {user_id}'

        class UserService:
            def __init__(self, repo: UserRepository) -> None:
                self.repo = repo

            def get_user(self, user_id: int) -> str:
                return self.repo.find(user_id)

        container.register_singleton(UserRepository, lambda: UserRepository())
        container.register_singleton(UserService, lambda: UserService(container.resolve(UserRepository)))

        service = container.resolve(UserService)

        # mypy should infer service as UserService
        assert isinstance(service, UserService)
        assert service.get_user(1) == 'User 1'

        # mypy should know about service.repo
        assert isinstance(service.repo, UserRepository)


class DescribeDecoratorTypePreservation:
    """Tests that @component decorator preserves type information."""

    def it_preserves_class_type_information(self) -> None:
        """@component decorator doesn't erase type information."""

        @component
        class MyService:
            def do_something(self) -> str:
                return 'done'

        # Type should be preserved after decoration
        assert hasattr(MyService, 'do_something')

        instance = MyService()
        assert instance.do_something() == 'done'

    def it_preserves_type_information_with_scope_parameter(self) -> None:
        """@component(scope=...) preserves type information."""

        @component(scope=Scope.FACTORY)
        class MyFactory:
            def create(self) -> str:
                return 'created'

        # Type should be preserved
        assert hasattr(MyFactory, 'create')

        instance = MyFactory()
        assert instance.create() == 'created'


class DescribeConstructorInjectionTypeSafety:
    """Tests that constructor injection is type-safe."""

    def it_resolves_correctly_typed_dependencies(self) -> None:
        """Dependencies are resolved with correct types."""
        from dioxide.decorators import _clear_registry

        _clear_registry()

        @component
        class Database:
            def query(self) -> str:
                return 'result'

        @component
        class Service:
            def __init__(self, db: Database) -> None:
                self.db = db

            def execute(self) -> str:
                return self.db.query()

        container = Container()
        container.scan()

        service = container.resolve(Service)

        # Verify types at runtime
        assert isinstance(service, Service)
        assert isinstance(service.db, Database)
        assert service.execute() == 'result'
