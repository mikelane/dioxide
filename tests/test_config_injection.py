"""Tests for config injection patterns with Pydantic Settings.

This test module validates the config-as-service pattern where:
1. Config classes can be decorated with @service (singleton, stateless)
2. Pre-created instances can be registered with register_instance()
3. Type safety ensures registered instances match declared types
"""

from abc import (
    ABC,
    abstractmethod,
)
from typing import Protocol

import pytest

from dioxide import (
    Container,
    service,
)


class DescribeConfigAsService:
    """Tests for using @service decorator on config classes."""

    def it_registers_config_class_as_singleton_service(self) -> None:
        """Config classes decorated with @service resolve as singletons."""

        @service
        class DatabaseConfig:
            host: str = 'localhost'
            port: int = 5432

        container = Container()
        container.scan()

        config1 = container.resolve(DatabaseConfig)
        config2 = container.resolve(DatabaseConfig)

        assert config1 is config2
        assert config1.host == 'localhost'
        assert config1.port == 5432

    def it_injects_config_into_service_dependencies(self) -> None:
        """Config classes can be injected into other services."""

        @service
        class AppConfig:
            debug: bool = True

        @service
        class UserService:
            def __init__(self, config: AppConfig) -> None:
                self.config = config

        container = Container()
        container.scan()

        user_service = container.resolve(UserService)

        assert user_service.config is not None
        assert user_service.config.debug is True


class DescribeRegisterInstance:
    """Tests for registering pre-created instances."""

    def it_registers_and_resolves_pre_created_instance(self) -> None:
        """Pre-created instances are returned as-is when resolved."""

        class DatabaseSettings:
            def __init__(self, host: str, port: int) -> None:
                self.host = host
                self.port = port

        container = Container()
        settings = DatabaseSettings(host='db.example.com', port=5433)
        container.register_instance(DatabaseSettings, settings)

        resolved = container.resolve(DatabaseSettings)

        assert resolved is settings
        assert resolved.host == 'db.example.com'
        assert resolved.port == 5433

    def it_injects_registered_instance_into_services(self) -> None:
        """Registered instances are injected into service dependencies."""

        class Config:
            def __init__(self, env: str) -> None:
                self.env = env

        @service
        class Application:
            def __init__(self, config: Config) -> None:
                self.config = config

        container = Container()
        config = Config(env='production')
        container.register_instance(Config, config)
        container.scan()

        app = container.resolve(Application)

        assert app.config is config
        assert app.config.env == 'production'


class DescribeRegisterInstanceTypeSafety:
    """Tests for type checking on register_instance."""

    def it_rejects_instance_that_does_not_match_type(self) -> None:
        """Registering an instance of wrong type raises TypeError."""

        class ExpectedType:
            pass

        class WrongType:
            pass

        container = Container()
        wrong_instance = WrongType()

        with pytest.raises(TypeError, match='instance must be of type'):
            container.register_instance(ExpectedType, wrong_instance)

    def it_accepts_subclass_instance(self) -> None:
        """Subclass instances are accepted for the parent type."""

        class BaseConfig:
            pass

        class ExtendedConfig(BaseConfig):
            extra: str = 'value'

        container = Container()
        extended = ExtendedConfig()
        container.register_instance(BaseConfig, extended)

        resolved = container.resolve(BaseConfig)

        assert resolved is extended
        assert isinstance(resolved, ExtendedConfig)

    def it_accepts_protocol_implementation(self) -> None:
        """Protocol implementations are accepted for the protocol type."""

        class EmailPort(Protocol):
            def send(self, to: str, message: str) -> None: ...

        class FakeEmailAdapter:
            def send(self, to: str, message: str) -> None:
                pass

        container = Container()
        fake = FakeEmailAdapter()
        container.register_instance(EmailPort, fake)

        resolved = container.resolve(EmailPort)

        assert resolved is fake

    def it_rejects_protocol_instance_missing_required_method(self) -> None:
        """Protocol implementations missing required methods raise TypeError."""

        class EmailPort(Protocol):
            def send(self, to: str, message: str) -> None: ...

        class IncompleteAdapter:
            pass  # Missing send method

        container = Container()

        with pytest.raises(TypeError, match='instance must be of type'):
            container.register_instance(EmailPort, IncompleteAdapter())

    def it_rejects_protocol_instance_with_non_callable_attribute(self) -> None:
        """Protocol implementations with non-callable attributes raise TypeError."""

        class EmailPort(Protocol):
            def send(self, to: str, message: str) -> None: ...

        class BrokenAdapter:
            send = 'not a method'  # Attribute exists but is not callable

        container = Container()

        with pytest.raises(TypeError, match='instance must be of type'):
            container.register_instance(EmailPort, BrokenAdapter())

    def it_accepts_abc_implementation(self) -> None:
        """ABC implementations are accepted for the abstract base class type."""

        class StoragePort(ABC):
            @abstractmethod
            def save(self, key: str, value: str) -> None: ...

        class FakeStorage(StoragePort):
            def save(self, key: str, value: str) -> None:
                pass

        container = Container()
        fake = FakeStorage()
        container.register_instance(StoragePort, fake)

        resolved = container.resolve(StoragePort)

        assert resolved is fake


class DescribeConfigWithPydanticSettings:
    """Tests for integration with Pydantic Settings pattern."""

    def it_works_with_pydantic_style_config(self) -> None:
        """Config classes following Pydantic pattern work correctly."""

        class DatabaseSettings:
            """Simulates Pydantic BaseSettings pattern."""

            def __init__(self) -> None:
                self.host: str = 'localhost'
                self.port: int = 5432

        @service
        class DatabaseService:
            def __init__(self, settings: DatabaseSettings) -> None:
                self.settings = settings

            def get_connection_string(self) -> str:
                return f'postgresql://{self.settings.host}:{self.settings.port}'

        container = Container()
        settings = DatabaseSettings()
        settings.host = 'db.prod.example.com'
        container.register_instance(DatabaseSettings, settings)
        container.scan()

        db_service = container.resolve(DatabaseService)

        assert db_service.get_connection_string() == 'postgresql://db.prod.example.com:5432'

    def it_supports_multiple_config_classes(self) -> None:
        """Multiple config classes can be registered independently."""

        class DatabaseConfig:
            host: str = 'localhost'

        class CacheConfig:
            ttl: int = 300

        @service
        class AppService:
            def __init__(self, db: DatabaseConfig, cache: CacheConfig) -> None:
                self.db = db
                self.cache = cache

        container = Container()
        container.register_instance(DatabaseConfig, DatabaseConfig())
        container.register_instance(CacheConfig, CacheConfig())
        container.scan()

        app = container.resolve(AppService)

        assert app.db.host == 'localhost'
        assert app.cache.ttl == 300


class DescribeRegisterInstanceWithServiceDecorator:
    """Tests for overriding @service decorated classes with register_instance."""

    def it_overrides_service_decorated_class_when_registered_before_scan(self) -> None:
        """A registered instance overrides the @service decorated class."""

        @service
        class AppConfig:
            def __init__(self) -> None:
                self.database_url = 'original://default'

        container = Container()
        override = AppConfig()
        override.database_url = 'override://test'
        container.register_instance(AppConfig, override)
        container.scan()

        resolved = container.resolve(AppConfig)

        assert resolved is override
        assert resolved.database_url == 'override://test'

    def it_injects_overridden_service_into_dependent_services(self) -> None:
        """Dependent services receive the overridden instance."""

        @service
        class DatabaseConfig:
            def __init__(self) -> None:
                self.host = 'production-db.example.com'
                self.port = 5432

        @service
        class DatabaseService:
            def __init__(self, config: DatabaseConfig) -> None:
                self.config = config

            def get_connection_string(self) -> str:
                return f'postgresql://{self.config.host}:{self.config.port}'

        container = Container()
        test_config = DatabaseConfig()
        test_config.host = 'localhost'
        test_config.port = 5433
        container.register_instance(DatabaseConfig, test_config)
        container.scan()

        db_service = container.resolve(DatabaseService)

        assert db_service.config is test_config
        assert db_service.get_connection_string() == 'postgresql://localhost:5433'


class DescribeRegisterInstanceAfterScan:
    """Tests for error behavior when registering after scan."""

    def it_raises_key_error_when_registering_already_scanned_type(self) -> None:
        """Registering an instance after scan raises KeyError for duplicate."""

        @service
        class Config:
            def __init__(self) -> None:
                self.value = 'original'

        container = Container()
        container.scan()

        override = Config()
        override.value = 'override'

        with pytest.raises(KeyError, match='Duplicate provider registration'):
            container.register_instance(Config, override)

    def it_allows_registering_unscanned_type_after_scan(self) -> None:
        """Types not in scan can still be registered after scan."""

        class NewConfig:
            def __init__(self, setting: str) -> None:
                self.setting = setting

        container = Container()
        container.scan()

        new_config = NewConfig(setting='added-after-scan')
        container.register_instance(NewConfig, new_config)

        resolved = container.resolve(NewConfig)

        assert resolved is new_config
        assert resolved.setting == 'added-after-scan'
