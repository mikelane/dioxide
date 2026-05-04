"""Adversarial QA tests for primitive type handling in auto-injecting factory.

Tests edge cases that might be missed by the implementation of Issues #489 and #490.
"""

from __future__ import annotations

from typing import (
    Protocol,
)

import pytest

from dioxide import (
    Container,
    Profile,
    adapter,
    service,
)
from dioxide.exceptions import (
    ServiceNotFoundError,
)

# ---------- Bug 1: Optional[primitive] not treated as primitive ----------


class DescribeOptionalStrParameters:
    """Optional[str] should be treated as a primitive and not resolved from container."""

    def it_uses_default_for_optional_str_parameter(self) -> None:
        """Optional[str] with a default should use the default, not try to resolve."""

        @service
        class AppConfig:
            def __init__(self, name: str | None = None) -> None:
                self.name = name

        container = Container()
        container.scan()

        config = container.resolve(AppConfig)
        assert config.name is None

    def it_uses_default_for_optional_int_parameter(self) -> None:
        """Optional[int] with a default should use the default, not try to resolve."""

        @service
        class IntConfig:
            def __init__(self, timeout: int | None = 60) -> None:
                self.timeout = timeout

        container = Container()
        container.scan()

        config = container.resolve(IntConfig)
        assert config.timeout == 60

    def it_uses_default_for_optional_bool_parameter(self) -> None:
        """Optional[bool] with a default should use the default."""

        @service
        class BoolConfig:
            def __init__(self, debug: bool | None = False) -> None:
                self.debug = debug

        container = Container()
        container.scan()

        config = container.resolve(BoolConfig)
        assert config.debug is False


# ---------- Bug 2: Union[primitive, ...] not treated as primitive ----------


class DescribeUnionWithPrimitiveParameters:
    """Union types containing primitives should be treated as primitives."""

    def it_uses_default_for_union_str_int_parameter(self) -> None:
        """Union[str, int] with default should use the default."""

        @service
        class UnionConfig:
            def __init__(self, value: str | int = 'default') -> None:
                self.value = value

        container = Container()
        container.scan()

        config = container.resolve(UnionConfig)
        assert config.value == 'default'

    def it_uses_default_for_union_str_none_parameter(self) -> None:
        """Union[str, None] (equivalent to Optional[str]) should use default."""

        @service
        class NullableConfig:
            def __init__(self, label: str | None = None) -> None:
                self.label = label

        container = Container()
        container.scan()

        config = container.resolve(NullableConfig)
        assert config.label is None


# ---------- Bug 3: Service with ONLY primitive parameters ----------


class DescribeServiceWithOnlyPrimitiveParams:
    """A service whose __init__ has ONLY primitive-typed parameters."""

    def it_instantiates_service_with_only_primitive_params(self) -> None:
        """Service with only primitive defaults should instantiate without error."""

        @service
        class DatabaseConfig:
            def __init__(
                self,
                host: str = 'localhost',
                port: int = 5432,
                debug: bool = False,
                timeout: float = 30.0,
            ) -> None:
                self.host = host
                self.port = port
                self.debug = debug
                self.timeout = timeout

        container = Container()
        container.scan()

        config = container.resolve(DatabaseConfig)
        assert config.host == 'localhost'
        assert config.port == 5432
        assert config.debug is False
        assert config.timeout == 30.0

    def it_instantiates_service_with_only_str_params(self) -> None:
        """Service with only str params (all with defaults)."""

        @service
        class StringConfig:
            def __init__(self, env: str = 'dev', region: str = 'us-east-1') -> None:
                self.env = env
                self.region = region

        container = Container()
        container.scan()

        config = container.resolve(StringConfig)
        assert config.env == 'dev'
        assert config.region == 'us-east-1'


# ---------- Bug 4: Typed **kwargs ----------


class DescribeTypedVarKeywordParams:
    """Typed **kwargs (e.g. **kwargs: int) should be handled gracefully."""

    def it_handles_typed_kwargs_int(self) -> None:
        """Class with **kwargs: int should instantiate without error."""

        @service
        class FilterConfig:
            def __init__(self, **kwargs: int) -> None:
                self.filters = kwargs

        container = Container()
        container.scan()

        config = container.resolve(FilterConfig)
        assert isinstance(config, FilterConfig)
        assert config.filters == {}


# ---------- Bug 5: Transitive dependency chains ----------


class DescribeDeepTransitiveChains:
    """Transitive failure chains of depth > 2 (A -> B -> C)."""

    def it_reports_chain_for_a_to_b_to_c_adapter_failure(self) -> None:
        """Error shows full chain when A -> B adapter -> C (missing)."""

        class LevelCPort(Protocol):
            def ping(self) -> str: ...

        class LevelBPort(Protocol):
            def query(self) -> str: ...

        @adapter.for_(LevelBPort, profile=Profile.DEVELOPMENT)
        class LevelBAdapter:
            def __init__(self, c: LevelCPort) -> None:
                self.c = c

            def query(self) -> str:
                return self.c.ping()

        container = Container()
        container.scan(profile=Profile.DEVELOPMENT)

        from dioxide.exceptions import AdapterNotFoundError

        with pytest.raises(AdapterNotFoundError) as exc_info:
            container.resolve(LevelBPort)

        error_msg = str(exc_info.value)
        # Should mention the port being resolved
        assert 'LevelBPort' in error_msg
        # Should mention the adapter that was found
        assert 'LevelBAdapter' in error_msg
        # Should mention the missing transitive dependency
        assert 'LevelCPort' in error_msg

    def it_reports_chain_for_a_to_b_to_c_service_failure(self) -> None:
        """Error shows full chain when service A -> service B -> missing C."""

        class CPort(Protocol):
            def ping(self) -> str: ...

        @service
        class BService:
            def __init__(self, c: CPort) -> None:
                self.c = c

            def query(self) -> str:
                return self.c.ping()

        @service
        class AService:
            def __init__(self, b: BService) -> None:
                self.b = b

        container = Container()
        container.scan(profile=Profile.DEVELOPMENT)

        with pytest.raises(ServiceNotFoundError) as exc_info:
            container.resolve(AService)

        error_msg = str(exc_info.value)
        # Should include the top-level service
        assert 'AService' in error_msg
        # Should include the intermediate service
        assert 'BService' in error_msg
        # Should include the missing dependency
        assert 'CPort' in error_msg

    def it_handles_optional_before_failing_dep_in_chain(self) -> None:
        """Optional[primitive] before failing dep should not cause TypeError crash."""

        class SettingsPort(Protocol):
            database_url: str

        class AuthPort(Protocol):
            def authenticate(self, token: str) -> bool: ...

        @adapter.for_(AuthPort, profile=Profile.DEVELOPMENT)
        class ClerkAdapter:
            def __init__(
                self,
                settings: SettingsPort,
                name: str | None = 'default',
            ) -> None:
                self.name = name
                self.settings = settings

            def authenticate(self, token: str) -> bool:
                return True

        container = Container()
        container.scan(profile=Profile.DEVELOPMENT)

        from dioxide.exceptions import AdapterNotFoundError

        with pytest.raises(AdapterNotFoundError) as exc_info:
            container.resolve(AuthPort)

        error_msg = str(exc_info.value)
        assert 'AuthPort' in error_msg
        assert 'ClerkAdapter' in error_msg
        assert 'SettingsPort' in error_msg

    def it_handles_none_default_with_optional_str(self) -> None:
        """Optional[str] with None default should not cause TypeError crash."""

        @service
        class ConfigService:
            def __init__(self, log_level: str | None = None) -> None:
                self.log_level = log_level

        container = Container()
        container.scan()

        config = container.resolve(ConfigService)
        assert config.log_level is None


# ---------- Bug 3: Circular dependency probing ----------


class DescribeCircularDependencyProbing:
    """Circular dependencies during error probing produce a clear error, not infinite recursion."""

    def it_handles_circular_dependency_gracefully(self) -> None:
        """Mutually dependent services produce ServiceNotFoundError, not RecursionError."""

        @service
        class ServiceX:
            def __init__(self, b: ServiceY) -> None:
                self.b = b

        @service
        class ServiceY:
            def __init__(self, a: ServiceX) -> None:
                self.a = a

        container = Container()
        container.scan()

        # Should raise ServiceNotFoundError (circular), not RecursionError
        with pytest.raises(ServiceNotFoundError):
            container.resolve(ServiceX)
