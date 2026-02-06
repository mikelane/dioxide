"""Tests for the pure Python container prototype."""

import pytest

from dioxide._python_container import PythonContainer


class DescribePythonContainer:
    """Tests for the pure Python container implementation."""

    def it_creates_an_empty_container(self) -> None:
        container = PythonContainer()
        assert container.is_empty()

    def it_reports_length_zero_when_empty(self) -> None:
        container = PythonContainer()
        assert len(container) == 0


class DescribeRegisterInstance:
    """Tests for registering pre-created instances."""

    def it_registers_and_resolves_an_instance(self) -> None:
        container = PythonContainer()

        class Config:
            def __init__(self, value: str) -> None:
                self.value = value

        config = Config('test')
        container.register_instance(Config, config)
        resolved = container.resolve(Config)

        assert resolved is config
        assert resolved.value == 'test'

    def it_marks_container_as_not_empty_after_registration(self) -> None:
        container = PythonContainer()

        class MyService:
            pass

        container.register_instance(MyService, MyService())
        assert not container.is_empty()
        assert len(container) == 1


class DescribeRegisterSingletonFactory:
    """Tests for registering singleton factory providers."""

    def it_calls_factory_once_and_caches_result(self) -> None:
        container = PythonContainer()
        call_count = 0

        class Database:
            def __init__(self) -> None:
                nonlocal call_count
                call_count += 1

        container.register_singleton_factory(Database, Database)
        first = container.resolve(Database)
        second = container.resolve(Database)

        assert first is second
        assert call_count == 1


class DescribeRegisterTransientFactory:
    """Tests for registering transient factory providers."""

    def it_creates_new_instance_on_each_resolve(self) -> None:
        container = PythonContainer()
        call_count = 0

        class RequestContext:
            def __init__(self) -> None:
                nonlocal call_count
                call_count += 1
                self.request_id = call_count

        container.register_transient_factory(RequestContext, RequestContext)
        first = container.resolve(RequestContext)
        second = container.resolve(RequestContext)

        assert first is not second
        assert call_count == 2
        assert first.request_id == 1
        assert second.request_id == 2


class DescribeRegisterClass:
    """Tests for registering class providers."""

    def it_creates_new_instance_on_each_resolve(self) -> None:
        container = PythonContainer()

        class Worker:
            pass

        container.register_class(Worker, Worker)
        first = container.resolve(Worker)
        second = container.resolve(Worker)

        assert isinstance(first, Worker)
        assert isinstance(second, Worker)
        assert first is not second


class DescribeReset:
    """Tests for clearing singleton cache."""

    def it_clears_singleton_cache_but_keeps_registrations(self) -> None:
        container = PythonContainer()
        call_count = 0

        class Service:
            def __init__(self) -> None:
                nonlocal call_count
                call_count += 1

        container.register_singleton_factory(Service, Service)
        first = container.resolve(Service)
        container.reset()
        second = container.resolve(Service)

        assert first is not second
        assert call_count == 2
        assert not container.is_empty()


class DescribeContains:
    """Tests for checking type registration."""

    def it_returns_false_for_unregistered_type(self) -> None:
        container = PythonContainer()

        class Unknown:
            pass

        assert not container.contains(Unknown)

    def it_returns_true_for_registered_type(self) -> None:
        container = PythonContainer()

        class Known:
            pass

        container.register_instance(Known, Known())
        assert container.contains(Known)


class DescribeGetRegisteredTypes:
    """Tests for listing registered types."""

    def it_returns_empty_list_for_empty_container(self) -> None:
        container = PythonContainer()
        assert container.get_registered_types() == []

    def it_returns_all_registered_types(self) -> None:
        container = PythonContainer()

        class A:
            pass

        class B:
            pass

        container.register_instance(A, A())
        container.register_singleton_factory(B, B)
        registered = container.get_registered_types()

        assert set(registered) == {A, B}


class DescribeDuplicateRegistration:
    """Tests for duplicate registration errors."""

    def it_raises_key_error_for_duplicate_instance(self) -> None:
        container = PythonContainer()

        class Service:
            pass

        container.register_instance(Service, Service())
        with pytest.raises(KeyError, match='Duplicate'):
            container.register_instance(Service, Service())

    def it_raises_key_error_for_duplicate_singleton_factory(self) -> None:
        container = PythonContainer()

        class Service:
            pass

        container.register_singleton_factory(Service, Service)
        with pytest.raises(KeyError, match='Duplicate'):
            container.register_singleton_factory(Service, Service)


class DescribeResolveUnregistered:
    """Tests for resolving unregistered types."""

    def it_raises_key_error_for_unregistered_type(self) -> None:
        container = PythonContainer()

        class Unknown:
            pass

        with pytest.raises(KeyError, match='not registered'):
            container.resolve(Unknown)


class DescribeConvenienceAliases:
    """Tests for register_singleton and register_factory convenience methods."""

    def it_register_singleton_delegates_to_singleton_factory(self) -> None:
        container = PythonContainer()

        class Cache:
            pass

        container.register_singleton(Cache, Cache)
        first = container.resolve(Cache)
        second = container.resolve(Cache)

        assert first is second

    def it_register_factory_delegates_to_transient_factory(self) -> None:
        container = PythonContainer()

        class Handler:
            pass

        container.register_factory(Handler, Handler)
        first = container.resolve(Handler)
        second = container.resolve(Handler)

        assert first is not second
