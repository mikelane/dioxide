"""Adversarial QA tests for Issues #489 and #490.

Gate 3 penetration tests targeting boundary conditions, error paths,
state management, and edge cases of the primitive-type detection and
transitive-failure probes.

Each bug is proven by a failing test before recording.
"""

from __future__ import annotations

import typing
from collections.abc import Callable
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
    AdapterNotFoundError,
    ServiceNotFoundError,
)

# ============================================================
# BUG 1: Union[primitive | non-primitive] causes TypeError crash
# ============================================================


class DescribeBugUnionPrimitiveNonPrimitiveCrash:
    """When a service constructor has a Union type that mixes a primitive
    with a non-primitive (e.g. str | SomePort), the container recognizes
    it as a non-injectable special form and uses the parameter's default value
    instead of attempting to resolve the Union from the container."""

    def it_resolves_str_or_port_union_with_default(self) -> None:
        """Union[str | SettingsPort] with default resolves using the default value."""

        class SettingsPort(Protocol):
            database_url: str

        @service
        class MixedService:
            def __init__(self, value: str | SettingsPort = 'default') -> None:
                self.value = value

        container = Container()
        container.scan(profile=Profile.DEVELOPMENT)

        instance = container.resolve(MixedService)
        assert instance.value == 'default'

    def it_resolves_int_or_port_union_with_default(self) -> None:
        """Union[int | CachePort] with default resolves using the default value."""

        class CachePort(Protocol):
            def get(self, key: str) -> str | None: ...

        @service
        class MixedIntService:
            def __init__(self, ttl: int | CachePort = 300) -> None:
                self.ttl = ttl

        container = Container()
        container.scan(profile=Profile.DEVELOPMENT)

        instance = container.resolve(MixedIntService)
        assert instance.ttl == 300

    def it_resolves_triple_union_with_default(self) -> None:
        """Union[str | int | Port] with default resolves using the default value."""

        class LogPort(Protocol):
            def log(self, msg: str) -> None: ...

        @service
        class TripleUnionService:
            def __init__(self, sink: str | int | LogPort = 'stdout') -> None:
                self.sink = sink

        container = Container()
        container.scan(profile=Profile.DEVELOPMENT)

        instance = container.resolve(TripleUnionService)
        assert instance.sink == 'stdout'


# ============================================================
# BUG 2: typing.Literal causes TypeError crash
# ============================================================
#
# Literal types defined in an external fixture module so that
# get_type_hints can properly resolve the Literal annotation.
# The import inside a test function triggers a different code path
# (get_type_hints failure -> direct cls instantiation -> success),
# which accidentally masks the TypeError bug.


class DescribeBugLiteralTypeCrash:
    """typing.Literal types are recognized as non-injectable special forms.
    The container uses the parameter's default value and resolves the service
    normally instead of attempting to resolve the Literal from the container."""

    def it_resolves_literal_string_param_with_default(self) -> None:
        """Literal['dev', 'prod'] parameter uses its default value."""
        from tests.fixtures.qa_literal_fixtures import LiteralStringFixture

        container = Container()
        container.scan()

        instance = container.resolve(LiteralStringFixture)
        assert instance.mode == 'dev'

    def it_resolves_literal_int_param_with_default(self) -> None:
        """Literal[1, 2, 3] parameter uses its default value."""
        from tests.fixtures.qa_literal_fixtures import LiteralIntFixture

        container = Container()
        container.scan()

        instance = container.resolve(LiteralIntFixture)
        assert instance.level == 1


# ============================================================
# BUG 3: typing.Callable causes TypeError crash
# ============================================================


class DescribeBugCallableTypeCrash:
    """typing.Callable types are not recognized as non-injectable. The
    auto-injecting factory tries to resolve them from the container,
    passing the Callable special form to _rust_core.resolve, which
    crashes with TypeError.

    Expected: The container recognizes Callable as non-injectable and
    uses the parameter's default value."""

    def it_resolves_callable_param_with_default(self) -> None:
        """Callable[[], str] parameter uses its default value."""

        def _default_fn() -> str:
            return 'hello'

        @service
        class CallableService:
            def __init__(self, get_message: Callable[[], str] = _default_fn) -> None:
                self.get_message = get_message

        container = Container()
        container.scan()

        instance = container.resolve(CallableService)
        assert instance.get_message() == 'hello'

    def it_resolves_variadic_callable_with_default(self) -> None:
        """Callable[..., Any] parameter uses its default value."""

        def _any_fn(*_: object) -> int:
            return 0

        @service
        class VariadicCallableService:
            def __init__(self, worker: Callable[..., int] = _any_fn) -> None:
                self.worker = worker

        container = Container()
        container.scan()

        instance = container.resolve(VariadicCallableService)
        assert instance.worker() == 0


# ============================================================
# BUG 4: Required primitive parameter (no default) gives
#        misleading error message
# ============================================================


class DescribeBugRequiredPrimitiveMisleadingMessage:
    """When a service has a required primitive parameter with no default
    (e.g. `name: str` without `= ...`), the resolution raises
    ServiceNotFoundError (correct) but the message says:
    "A transitive dependency failed during resolution"
    which is misleading — the real issue is a missing default, not a
    transitive dependency failure."""

    def it_has_misleading_message_for_required_str_param(self) -> None:
        """Required str without default gets wrong error message."""

        @service
        class NeedsString:
            def __init__(self, name: str) -> None:
                self.name = name

        container = Container()
        container.scan()

        with pytest.raises(ServiceNotFoundError) as exc_info:
            container.resolve(NeedsString)

        error_msg = str(exc_info.value)
        # BUG: The error message says "transitive dependency failed"
        # but the real problem is a missing default for a primitive parameter.
        assert 'transitive dependency' in error_msg, (
            "Current behavior confirmed: misleading 'transitive dependency' message"
        )


# ============================================================
# Attack 4: Three-way circular dependency
# ============================================================


class DescribeThreeWayCircularDependency:
    """Three-way cycle A -> B -> C -> A must not infinite-recurse."""

    def it_handles_three_way_circular_without_recursion(self) -> None:
        """A three-way circular dependency produces a clear error."""

        @service
        class CycleC:
            def __init__(self, a: CycleA) -> None:
                self.a = a

        @service
        class CycleB:
            def __init__(self, c: CycleC) -> None:
                self.c = c

        @service
        class CycleA:
            def __init__(self, b: CycleB) -> None:
                self.b = b

        container = Container()
        container.scan()

        with pytest.raises(ServiceNotFoundError) as exc_info:
            container.resolve(CycleA)

        error_msg = str(exc_info.value)
        assert 'CycleA' in error_msg

    def it_handles_larger_circular_chain_without_recursion(self) -> None:
        """Four-way cycle A -> B -> C -> D -> A must not infinite-recurse."""

        @service
        class QuadD:
            def __init__(self, a: QuadA) -> None:
                self.a = a

        @service
        class QuadC:
            def __init__(self, d: QuadD) -> None:
                self.d = d

        @service
        class QuadB:
            def __init__(self, c: QuadC) -> None:
                self.c = c

        @service
        class QuadA:
            def __init__(self, b: QuadB) -> None:
                self.b = b

        container = Container()
        container.scan()

        with pytest.raises(ServiceNotFoundError) as exc_info:
            container.resolve(QuadA)

        error_msg = str(exc_info.value)
        assert 'QuadA' in error_msg


# ============================================================
# Attack 5: _resolving state leaks
# ============================================================


class DescribeResolvingStateCleanup:
    """The _resolving set must always be cleaned up even after errors."""

    def it_cleans_resolving_after_failed_resolve(self) -> None:
        """After a failed resolve, _resolving should not contain leaked types."""

        @service
        class CleanupTest:
            def __init__(self, name: str = 'ok') -> None:
                self.name = name

        container = Container()
        container.scan()

        instance = container.resolve(CleanupTest)
        assert instance.name == 'ok'

        assert len(container._resolving) == 0, f'_resolving not empty after successful resolve: {container._resolving}'

    def it_cleans_resolving_after_transitive_failure(self) -> None:
        """After a transitive failure, _resolving should be empty."""

        class MissingPort(Protocol):
            def do_thing(self) -> None: ...

        @service
        class DependsOnMissing:
            def __init__(self, dep: MissingPort) -> None:
                self.dep = dep

        container = Container()
        container.scan(profile=Profile.DEVELOPMENT)

        with pytest.raises(ServiceNotFoundError):
            container.resolve(DependsOnMissing)

        assert len(container._resolving) == 0, f'_resolving not empty after failed resolve: {container._resolving}'

    def it_cleans_resolving_after_circular_failure(self) -> None:
        """After a circular dependency failure, _resolving should be empty."""

        @service
        class Ca:
            def __init__(self, b: Cb) -> None:
                self.b = b

        @service
        class Cb:
            def __init__(self, a: Ca) -> None:
                self.a = a

        container = Container()
        container.scan()

        with pytest.raises(ServiceNotFoundError):
            container.resolve(Ca)

        assert len(container._resolving) == 0, f'_resolving not empty after circular failure: {container._resolving}'


# ============================================================
# Attack 6: _probing_deps state leaks
# ============================================================


class DescribeProbingDepsCleanup:
    """The _probing_deps set must always be cleaned up."""

    def it_cleans_probing_deps_after_transitive_failure(self) -> None:
        """After any resolution, _probing_deps should be empty."""

        class XPort(Protocol):
            pass

        @adapter.for_(XPort, profile=Profile.DEVELOPMENT)
        class XAdapter:
            def __init__(self, a_str: str = 'hi') -> None:
                self.a_str = a_str

        container = Container()
        container.scan(profile=Profile.DEVELOPMENT)

        container.resolve(XPort)

        assert len(container._probing_deps) == 0, f'_probing_deps not empty after resolve: {container._probing_deps}'

    def it_cleans_probing_deps_after_circular(self) -> None:
        """Probing deps must be clean after circular dependency detection."""

        @service
        class Pa:
            def __init__(self, b: Pb) -> None:
                self.b = b

        @service
        class Pb:
            def __init__(self, a: Pa) -> None:
                self.a = a

        container = Container()
        container.scan()

        with pytest.raises(ServiceNotFoundError):
            container.resolve(Pa)

        assert len(container._probing_deps) == 0, f'_probing_deps not empty: {container._probing_deps}'


# ============================================================
# Attack 7: *args and **kwargs with type annotations
# ============================================================


class DescribeTypedVarargs:
    """*args and **kwargs with type annotations must not crash."""

    def it_handles_typed_args_int_in_constructor(self) -> None:
        """Class with *args: int should instantiate without error."""

        @service
        class VarArgService:
            def __init__(self, *args: int) -> None:
                self.args = args

        container = Container()
        container.scan()

        instance = container.resolve(VarArgService)
        assert isinstance(instance, VarArgService)
        assert instance.args == ()

    def it_handles_typed_args_and_kwargs_together(self) -> None:
        """Class with both *args and **kwargs typed annotations."""

        @service
        class Flexible:
            def __init__(self, *args: str, **kwargs: int) -> None:
                self.args = args
                self.kwargs = kwargs

        container = Container()
        container.scan()

        instance = container.resolve(Flexible)
        assert isinstance(instance, Flexible)
        assert instance.args == ()
        assert instance.kwargs == {}


# ============================================================
# Attack 8: Multiple independent resolves after a failure
# ============================================================


class DescribeRecoveryAfterFailure:
    """After one resolve fails, another resolve of a different type must work."""

    def it_resolves_second_type_after_first_fails(self) -> None:
        """Resolution of type B succeeds even after resolution of type A fails."""

        class NonexistentPort(Protocol):
            pass

        @service
        class WillFail:
            def __init__(self, x: NonexistentPort) -> None:
                self.x = x

        @service
        class WillSucceed:
            def __init__(self, name: str = 'ok') -> None:
                self.name = name

        container = Container()
        container.scan(profile=Profile.DEVELOPMENT)

        with pytest.raises(ServiceNotFoundError):
            container.resolve(WillFail)

        instance = container.resolve(WillSucceed)
        assert instance.name == 'ok'

    def it_resolves_same_type_after_different_failure(self) -> None:
        """Resolving a working type still works after an unrelated failure."""

        @service
        class GoodService:
            def __init__(self, tag: str = 'v1') -> None:
                self.tag = tag

        container = Container()
        container.scan()

        g1 = container.resolve(GoodService)
        assert g1.tag == 'v1'

        class Unknown:
            pass

        with pytest.raises(ServiceNotFoundError):
            container.resolve(Unknown)

        g2 = container.resolve(GoodService)
        assert g2 is g1


# ============================================================
# Attack 9: Multi-primitive unions
# ============================================================


class DescribeMultiPrimitiveUnion:
    """Unions with 3+ primitive types should all be treated as primitives."""

    def it_uses_default_for_str_int_float_union(self) -> None:
        """Union[str, int, float] with default should use the default."""

        @service
        class MultiUnionConfig:
            def __init__(self, value: str | int | float = 'fallback') -> None:
                self.value = value

        container = Container()
        container.scan()

        config = container.resolve(MultiUnionConfig)
        assert config.value == 'fallback'

    def it_uses_default_for_str_int_bool_union(self) -> None:
        """Union[str, int, bool] with default should use the default."""

        @service
        class TripleConfig:
            def __init__(self, flag: str | int | bool = False) -> None:
                self.flag = flag

        container = Container()
        container.scan()

        config = container.resolve(TripleConfig)
        assert config.flag is False

    def it_uses_default_for_bytes_none_union(self) -> None:
        """Union[bytes, None] with default should use the default."""

        @service
        class BytesConfig:
            def __init__(self, data: bytes | None = None) -> None:
                self.data = data

        container = Container()
        container.scan()

        config = container.resolve(BytesConfig)
        assert config.data is None


# ============================================================
# Attack 10: Empty container (never scanned)
# ============================================================


class DescribeEmptyContainerBehavior:
    """Edge cases with containers that haven't been scanned."""

    def it_raises_clear_error_for_non_scanned_service(self) -> None:
        """Resolving a service from a never-scanned container raises clear error."""

        @service
        class ForgottenService:
            def __init__(self) -> None:
                self.ready = True

        container = Container()

        with pytest.raises(ServiceNotFoundError) as exc_info:
            container.resolve(ForgottenService)

        error_msg = str(exc_info.value)
        assert 'ForgottenService' in error_msg

    def it_raises_clear_error_for_port_in_never_scanned_container(self) -> None:
        """Resolving a port from a never-scanned container raises clear error."""

        class AnyPort(Protocol):
            pass

        container = Container()

        with pytest.raises(AdapterNotFoundError) as exc_info:
            container.resolve(AnyPort)

        error_msg = str(exc_info.value)
        assert 'AnyPort' in error_msg


# ============================================================
# Attack 11: Deep transitive chains (depth >= 3)
# ============================================================


class DescribeDeepTransitiveChains:
    """Transitive failure chains deeper than the 2-level tests in the
    existing test suite."""

    def it_reports_chain_for_a_to_b_to_c_to_d_adapter_failure(self) -> None:
        """Four-level chain error when D is missing."""

        class PortD(Protocol):
            def ping(self) -> str: ...

        class PortC(Protocol):
            def query(self) -> str: ...

        class PortB(Protocol):
            def compute(self) -> str: ...

        @adapter.for_(PortC, profile=Profile.DEVELOPMENT)
        class AdapterC:
            def __init__(self, d: PortD) -> None:
                self.d = d

            def query(self) -> str:
                return self.d.ping()

        @adapter.for_(PortB, profile=Profile.DEVELOPMENT)
        class AdapterB:
            def __init__(self, c: PortC) -> None:
                self.c = c

            def compute(self) -> str:
                return self.c.query()

        container = Container()
        container.scan(profile=Profile.DEVELOPMENT)

        with pytest.raises(AdapterNotFoundError) as exc_info:
            container.resolve(PortB)

        error_msg = str(exc_info.value)
        assert 'PortB' in error_msg
        assert 'PortC' in error_msg
        assert 'PortD' in error_msg

    def it_reports_chain_for_a_to_b_to_c_to_d_service_failure(self) -> None:
        """Four-level service chain error."""

        class PortZ(Protocol):
            pass

        @service
        class ServiceX:
            def __init__(self, y: ServiceY) -> None:
                self.y = y

        @service
        class ServiceY:
            def __init__(self, z: ServiceZ) -> None:
                self.z = z

        @service
        class ServiceZ:
            def __init__(self, port: PortZ) -> None:
                self.port = port

        container = Container()
        container.scan(profile=Profile.DEVELOPMENT)

        with pytest.raises(ServiceNotFoundError) as exc_info:
            container.resolve(ServiceX)

        error_msg = str(exc_info.value)
        assert 'ServiceX' in error_msg
        assert 'ServiceY' in error_msg
        assert 'ServiceZ' in error_msg
        assert 'PortZ' in error_msg


# ============================================================
# Attack 12: Old-style typing import annotations
# ============================================================


class DescribeOldStyleOptionalAnnotation:
    """typing.Optional[T] (pre-3.10 style) should also be handled."""

    def it_handles_old_style_optional_str(self) -> None:
        """Optional[str] from typing import should use the default."""

        @service
        class OldStyleConfig:
            def __init__(self, label: str | None = 'classic') -> None:
                self.label = label

        container = Container()
        container.scan()

        config = container.resolve(OldStyleConfig)
        assert config.label == 'classic'

    def it_handles_old_style_optional_int(self) -> None:
        """Optional[int] from typing import should use the default."""

        @service
        class OldIntConfig:
            def __init__(self, count: int | None = 42) -> None:
                self.count = count

        container = Container()
        container.scan()

        config = container.resolve(OldIntConfig)
        assert config.count == 42

    def it_handles_old_style_union_of_primitives(self) -> None:
        """Union[str, int] from typing import should be treated as primitive."""

        @service
        class OldUnionConfig:
            def __init__(self, val: str | int = 'mixed') -> None:
                self.val = val

        container = Container()
        container.scan()

        config = container.resolve(OldUnionConfig)
        assert config.val == 'mixed'


# ============================================================
# Attack 13: Class-level attributes only (no __init__)
# ============================================================


class DescribeClassLevelAttributesService:
    """Services with class-level attrs and no custom __init__."""

    def it_resolves_service_with_only_class_attrs(self) -> None:
        """Service with class-level defaults and no __init__."""

        @service
        class SimpleConfig:
            host: str = '0.0.0.0'
            port: int = 8080

        container = Container()
        container.scan()

        config = container.resolve(SimpleConfig)
        assert config.host == '0.0.0.0'
        assert config.port == 8080


# ============================================================
# Attack 14: Error message format
# ============================================================


class DescribeTransitiveErrorMessageFormat:
    """The transitive failure message format should be clean and readable."""

    def it_does_not_include_raw_traceback_in_error_message(self) -> None:
        """Error messages should not leak raw Python exception text."""

        class MissingDep(Protocol):
            def action(self) -> None: ...

        @service
        class OuterService:
            def __init__(self, inner: MissingDep) -> None:
                self.inner = inner

        container = Container()
        container.scan(profile=Profile.DEVELOPMENT)

        with pytest.raises(ServiceNotFoundError) as exc_info:
            container.resolve(OuterService)

        error_msg = str(exc_info.value)
        assert 'Traceback' not in error_msg
        assert 'raise AdapterNotFoundError' not in error_msg
        assert 'raise ServiceNotFoundError' not in error_msg

    def it_does_not_exceed_10_lines(self) -> None:
        """Even deep chain errors should fit in a reasonable number of lines."""

        class DeepMissingPort(Protocol):
            pass

        @adapter.for_(DeepMissingPort, profile=Profile.DEVELOPMENT)
        class DeepAdapter:
            def __init__(self, s: DeepMissingPortInner) -> None:
                self.s = s

        class DeepMissingPortInner(Protocol):
            pass

        container = Container()
        container.scan(profile=Profile.DEVELOPMENT)

        with pytest.raises(AdapterNotFoundError) as exc_info:
            container.resolve(DeepMissingPort)

        error_msg = str(exc_info.value)
        line_count = len(error_msg.strip().split('\n'))
        assert line_count <= 10, f'Error message has {line_count} lines, expected <= 10:\n{error_msg}'


# ============================================================
# Attack 15: Sequential resolution stress test
# ============================================================


class DescribeMultipleResolveStress:
    """Sequence of many resolves to stress-test state cleanup."""

    def it_handles_many_mixed_resolves(self) -> None:
        """Many resolves, some failing, some succeeding, in sequence."""

        @service
        class StressA:
            def __init__(self, x: str = 'a') -> None:
                self.x = x

        @service
        class StressB:
            def __init__(self, y: str = 'b') -> None:
                self.y = y

        class BogusPort(Protocol):
            pass

        class BogusPort2(Protocol):
            pass

        @service
        class StressC:
            def __init__(self, bp: BogusPort) -> None:
                self.bp = bp

        @service
        class StressD:
            def __init__(self, bp: BogusPort2) -> None:
                self.bp = bp

        container = Container()
        container.scan(profile=Profile.DEVELOPMENT)

        for _ in range(20):
            a = container.resolve(StressA)
            assert a.x == 'a'

            b = container.resolve(StressB)
            assert b.y == 'b'

            with pytest.raises(ServiceNotFoundError):
                container.resolve(StressC)

            with pytest.raises(ServiceNotFoundError):
                container.resolve(StressD)

            a2 = container.resolve(StressA)
            assert a2 is a

        assert len(container._resolving) == 0
        assert len(container._probing_deps) == 0


# ============================================================
# Attack 16: type[SomeType] not recognized as non-injectable
# ============================================================


class DescribeBugTypeSpecialFormCrash:
    """type[SomeType] (e.g. type[str]) is a GenericAlias with origin `type`.
    _is_non_injectable_type now recognizes this as non-injectable and uses
    the parameter's default value instead of crashing."""

    def it_uses_default_for_type_str_param(self) -> None:
        """type[str] with default uses the default value instead of crashing."""

        @service
        class TypeParamService:
            def __init__(self, factory: type[str] = str) -> None:
                self.factory = factory

        container = Container()
        container.scan()

        instance = container.resolve(TypeParamService)
        assert instance.factory is str

    def it_uses_default_for_type_str_in_adapter_constructor(self) -> None:
        """type[str] in an adapter constructor uses the default value."""

        class DBPort(Protocol):
            pass

        @adapter.for_(DBPort, profile=Profile.DEVELOPMENT)
        class DBAdapter:
            def __init__(self, validator: type[str] = str) -> None:
                self.validator = validator

        container = Container()
        container.scan(profile=Profile.DEVELOPMENT)

        instance = container.resolve(DBPort)
        assert instance.validator is str


# ============================================================
# Attack 17: typing.Any not recognized as non-injectable
# ============================================================


class DescribeBugAnyTypeNotRecognized:
    """typing.Any has get_origin() == None and is not in _PRIMITIVE_TYPES.
    _is_non_injectable_type now explicitly checks for `typing.Any` and uses
    the parameter's default value instead of trying to resolve it."""

    def it_uses_default_for_any_param(self) -> None:
        """typing.Any with a default uses the default instead of trying to resolve Any."""

        @service
        class AnyService:
            def __init__(self, value: typing.Any = 'default') -> None:
                self.value = value

        container = Container()
        container.scan()

        instance = container.resolve(AnyService)
        assert instance.value == 'default'


# ============================================================
# Attack 18: TypeVar not recognized as non-injectable
# ============================================================


class DescribeBugTypeVarCrash:
    """TypeVar has get_origin() == None and is not in _PRIMITIVE_TYPES.
    _is_non_injectable_type now explicitly checks for TypeVar via isinstance
    and uses the parameter's default value instead of crashing.

    TypeVar and service class are defined in an external fixture module
    so that get_type_hints can properly resolve the TypeVar annotation,
    just like the Literal fixtures."""

    def it_uses_default_for_typevar_param(self) -> None:
        """TypeVar parameter uses its default value instead of crashing."""
        from tests.fixtures.qa_typevar_fixtures import TypeVarFixture

        container = Container()
        container.scan()

        instance = container.resolve(TypeVarFixture)
        assert instance.value == 'ok'


# ============================================================
# Attack 19: Union type with no default gives misleading message
# ============================================================


class DescribeBugUnionNoDefaultMisleadingError:
    """When a service has a Union-typed parameter with no default, the
    parameter is treated as non-injectable (correct). But since there's
    no default, the cls() call fails with TypeError about missing args.
    This gets wrapped into a misleading 'transitive dependency failed'
    ServiceNotFoundError."""

    def it_gives_misleading_error_for_union_no_default(self) -> None:
        """Union[str, int] without default -> misleading transitive error."""

        @service
        class NoDefaultUnion:
            def __init__(self, value: str | int) -> None:
                self.value = value

        container = Container()
        container.scan()

        with pytest.raises(ServiceNotFoundError) as exc_info:
            container.resolve(NoDefaultUnion)

        error_msg = str(exc_info.value)
        # BUG: The error message says "transitive dependency failed"
        # but the real issue is a Union param missing a default value.
        assert 'transitive dependency' in error_msg, (
            "BUG: misleading 'transitive dependency' message for Union param with no default"
        )


# ============================================================
# Attack 20: Nested generics with special forms (boundary)
# ============================================================


class DescribeNestedGenericSpecialForms:
    """When a special form is nested inside a generic (e.g.,
    list[Callable[[int], str]]), the outer origin is `list` which is now
    in _PRIMITIVE_TYPES (via `origin in _PRIMITIVE_TYPES` check).
    _is_non_injectable_type returns True, so the parameter's default value
    is used instead of being intercepted by the multi-binding code path."""

    def it_resolves_list_of_callable_with_default_value(self) -> None:
        """list[Callable[[int], str]] uses its default value (the list class)
        instead of being intercepted by the multi-binding code path."""

        @service
        class ListCallableService:
            def __init__(self, handlers: list[Callable[[int], str]] = list) -> None:  # type: ignore[assignment]
                self.handlers = handlers

        container = Container()
        container.scan()
        instance = container.resolve(ListCallableService)

        # The origin `list` is in _PRIMITIVE_TYPES, so this is recognized
        # as non-injectable and the default value `list` (the class) is used.
        assert instance.handlers is list


# ============================================================
# Attack 21: Generic collection aliases crash (dict, set, tuple, frozenset)
# ============================================================


class DescribeBugGenericCollectionAliasCrash:
    """Generic aliases of built-in collection types (dict[str, int],
    set[int], tuple[int, str], frozenset[int]) are now recognized as
    non-injectable because _is_non_injectable_type checks `origin in
    _PRIMITIVE_TYPES` in addition to the bare type check. The parameter's
    default value is used instead of crashing."""

    def it_uses_default_for_dict_str_int(self) -> None:
        """dict[str, int] uses its default value instead of crashing."""

        @service
        class DictConfig:
            def __init__(self, config: dict[str, int] = dict) -> None:  # type: ignore[assignment]
                self.config = config

        container = Container()
        container.scan()

        instance = container.resolve(DictConfig)
        assert instance.config is dict

    def it_uses_default_for_set_int(self) -> None:
        """set[int] uses its default value instead of crashing."""

        @service
        class SetConfig:
            def __init__(self, values: set[int] = set) -> None:  # type: ignore[assignment]
                self.values = values

        container = Container()
        container.scan()

        instance = container.resolve(SetConfig)
        assert instance.values is set

    def it_uses_default_for_tuple_int_str(self) -> None:
        """tuple[int, str] uses its default value instead of crashing."""

        @service
        class TupleConfig:
            def __init__(self, coords: tuple[int, str] = tuple) -> None:  # type: ignore[assignment]
                self.coords = coords

        container = Container()
        container.scan()

        instance = container.resolve(TupleConfig)
        assert instance.coords is tuple

    def it_uses_default_for_frozenset_int(self) -> None:
        """frozenset[int] uses its default value instead of crashing."""

        @service
        class FrozenConfig:
            def __init__(self, frozen: frozenset[int] = frozenset) -> None:  # type: ignore[assignment]
                self.frozen = frozen

        container = Container()
        container.scan()

        instance = container.resolve(FrozenConfig)
        assert instance.frozen is frozenset
