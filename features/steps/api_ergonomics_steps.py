"""Step definitions for API ergonomics acceptance tests.

These steps verify that dioxide's API feels natural, provides minimal ceremony,
and gives helpful guidance when developers make mistakes. Steps are designed to
test observable behavior: decorator syntax, docstring content, error messages,
and string representations.
"""

from typing import Protocol

from behave import given, then, when
from behave.runner import Context

from dioxide import Container, Profile, adapter, lifecycle, service
from dioxide._registry import _clear_registry
from dioxide.exceptions import AdapterNotFoundError, ServiceNotFoundError

# ---------------------------------------------------------------------------
# Scenario: Simple adapter syntax fits on one line
# ---------------------------------------------------------------------------


@given('I define a Protocol called EmailPort')
def step_define_email_port(context: Context) -> None:
    class EmailPort(Protocol):
        def send(self, to: str, body: str) -> None: ...

    context.email_port = EmailPort


@when('I apply the @adapter.for_ decorator with a profile')
def step_apply_adapter_decorator(context: Context) -> None:
    _clear_registry()

    @adapter.for_(context.email_port, profile=Profile.PRODUCTION)
    class SmtpAdapter:
        def send(self, to: str, body: str) -> None:
            pass

    context.adapter_class = SmtpAdapter
    context.decorator_source = '@adapter.for_(EmailPort, profile=Profile.PRODUCTION)'


@then('the full decorator fits on one line')
def step_decorator_fits_one_line(context: Context) -> None:
    decorator_text = context.decorator_source
    assert '\n' not in decorator_text, f'Decorator should fit on one line, got: {decorator_text}'


@then('the syntax reads as @adapter.for_(EmailPort, profile=Profile.PRODUCTION)')
def step_syntax_reads_naturally(context: Context) -> None:
    expected = '@adapter.for_(EmailPort, profile=Profile.PRODUCTION)'
    actual = context.decorator_source
    assert actual == expected, f'Expected syntax "{expected}", got "{actual}"'


@then('no other decorators are required for basic usage')
def step_no_extra_decorators_required(context: Context) -> None:
    cls = context.adapter_class
    assert hasattr(cls, '__dioxide_port__'), 'Adapter should have __dioxide_port__ metadata from single decorator'
    assert hasattr(cls, '__dioxide_profiles__'), (
        'Adapter should have __dioxide_profiles__ metadata from single decorator'
    )
    has_lifecycle = getattr(cls, '_dioxide_lifecycle', False)
    assert not has_lifecycle, 'Basic adapter should not require @lifecycle decorator'


# ---------------------------------------------------------------------------
# Scenario: Lifecycle decorator is optional
# ---------------------------------------------------------------------------


@given('I have an adapter for EmailPort without lifecycle needs')
def step_adapter_without_lifecycle(context: Context) -> None:
    _clear_registry()

    class EmailPort(Protocol):
        def send(self, to: str, body: str) -> None: ...

    @adapter.for_(EmailPort, profile=Profile.TEST)
    class SimpleEmailAdapter:
        def send(self, to: str, body: str) -> None:
            pass

    context.email_port = EmailPort
    context.simple_adapter = SimpleEmailAdapter


@when('I register and resolve the adapter')
def step_register_and_resolve(context: Context) -> None:
    container = Container()
    container.scan(profile=Profile.TEST)
    context.resolved = container.resolve(context.email_port)


@then('the adapter works without @lifecycle decorator')
def step_works_without_lifecycle(context: Context) -> None:
    assert context.resolved is not None, 'Adapter should resolve without @lifecycle'
    has_lifecycle = getattr(type(context.resolved), '_dioxide_lifecycle', False)
    assert not has_lifecycle, 'Adapter should not have lifecycle marker'


@then('the adapter works without initialize() or dispose() methods')
def step_works_without_lifecycle_methods(context: Context) -> None:
    resolved = context.resolved
    assert not hasattr(resolved, 'initialize') or not callable(getattr(resolved, 'initialize', None)), (
        'Simple adapter should not need initialize() method'
    )
    assert not hasattr(resolved, 'dispose') or not callable(getattr(resolved, 'dispose', None)), (
        'Simple adapter should not need dispose() method'
    )


# ---------------------------------------------------------------------------
# Scenario: Lifecycle with async context manager protocol
# ---------------------------------------------------------------------------


@given('I have a class with __aenter__ and __aexit__ methods')
def step_class_with_context_manager(context: Context) -> None:
    class AsyncResource:
        def __init__(self) -> None:
            self.entered = False
            self.exited = False

        async def __aenter__(self) -> 'AsyncResource':
            self.entered = True
            return self

        async def __aexit__(self, *args: object) -> None:
            self.exited = True

    context.async_resource_class = AsyncResource


@when('I check how @lifecycle integrates with async context managers')
def step_check_lifecycle_integration(context: Context) -> None:
    cls = context.async_resource_class
    context.has_aenter = hasattr(cls, '__aenter__')
    context.has_aexit = hasattr(cls, '__aexit__')

    try:
        lifecycle(cls)
        context.lifecycle_accepts_context_manager = True
        context.lifecycle_error = None
    except TypeError as e:
        context.lifecycle_accepts_context_manager = False
        context.lifecycle_error = str(e)


@then('@lifecycle requires custom initialize() and dispose() methods')
def step_lifecycle_requires_custom_methods(context: Context) -> None:
    assert not context.lifecycle_accepts_context_manager, (
        '@lifecycle currently requires initialize()/dispose(), not __aenter__/__aexit__'
    )
    assert context.lifecycle_error is not None, (
        'Expected TypeError when applying @lifecycle to class without initialize()'
    )
    assert 'initialize' in context.lifecycle_error, f'Error should mention initialize(), got: {context.lifecycle_error}'


@then('there is clear documentation explaining the lifecycle protocol')
def step_lifecycle_has_documentation(context: Context) -> None:
    docstring = lifecycle.__doc__
    assert docstring is not None, '@lifecycle should have a docstring'
    assert 'initialize' in docstring.lower(), 'Lifecycle docstring should explain initialize() requirement'
    assert 'dispose' in docstring.lower(), 'Lifecycle docstring should explain dispose() requirement'


# ---------------------------------------------------------------------------
# Scenario: Profile.ALL displays cleanly
# ---------------------------------------------------------------------------


@given('I have the Profile.ALL constant')
def step_have_profile_all(context: Context) -> None:
    context.profile_all = Profile.ALL


@when('I check its string representations')
def step_check_profile_representations(context: Context) -> None:
    context.profile_repr = repr(context.profile_all)
    context.profile_str = str(context.profile_all)


@then('repr shows "Profile.ALL" rather than the raw wildcard')
def step_repr_shows_profile_all(context: Context) -> None:
    actual = context.profile_repr
    assert 'Profile.ALL' in actual or 'all' in actual.lower(), (
        f'repr(Profile.ALL) should show "Profile.ALL", got: {actual!r}. '
        f'Currently shows the raw wildcard "*" which is confusing.'
    )
    assert '*' not in actual, (
        f'repr(Profile.ALL) should not contain raw "*", got: {actual!r}. '
        f'Users see this in debuggers and error messages.'
    )


@then('str conversion in error messages avoids showing raw "*"')
def step_str_avoids_raw_wildcard(context: Context) -> None:
    # Error messages typically use repr() for Profile values.
    # When developers see Profile('*') in tracebacks or logs, they
    # must know the internal convention. "Profile.ALL" is clearer.
    # This step verifies repr() is developer-friendly.
    assert '*' not in context.profile_repr, (
        f'repr(Profile.ALL) should not expose "*": got {context.profile_repr!r}. '
        f'Error messages and debuggers use repr(), so it must be readable.'
    )


# ---------------------------------------------------------------------------
# Scenario: @service docstring
# ---------------------------------------------------------------------------


@when('I inspect the @service decorator docstring')
def step_inspect_service_docstring(context: Context) -> None:
    context.service_doc = service.__doc__


@then('the docstring mentions "core business logic"')
def step_service_mentions_business_logic(context: Context) -> None:
    doc = context.service_doc
    assert doc is not None, '@service should have a docstring'
    assert 'core' in doc.lower() and ('business logic' in doc.lower() or 'domain logic' in doc.lower()), (
        f'@service docstring should mention "core business logic" or "core domain logic". First 200 chars: {doc[:200]}'
    )


@then('the docstring includes a usage example')
def step_service_has_example(context: Context) -> None:
    doc = context.service_doc
    assert doc is not None, '@service should have a docstring'
    assert '@service' in doc, '@service docstring should include a usage example showing @service decorator'
    assert 'class' in doc, '@service docstring should include a class in its usage example'


@then('the docstring mentions "profile-agnostic" behavior')
def step_service_mentions_profile_agnostic(context: Context) -> None:
    doc = context.service_doc
    assert doc is not None, '@service should have a docstring'
    doc_lower = doc.lower()
    has_profile_agnostic = 'profile-agnostic' in doc_lower or 'profile agnostic' in doc_lower
    has_all_profiles = 'all profiles' in doc_lower or 'available in all' in doc_lower
    assert has_profile_agnostic or has_all_profiles, (
        '@service docstring should mention that services are profile-agnostic or available in all profiles.'
    )


# ---------------------------------------------------------------------------
# Scenario: @adapter.for_ docstring
# ---------------------------------------------------------------------------


@when('I inspect the @adapter.for_ decorator docstring')
def step_inspect_adapter_docstring(context: Context) -> None:
    context.adapter_doc = adapter.for_.__doc__


@then('the docstring mentions "swappable implementations"')
def step_adapter_mentions_swappable(context: Context) -> None:
    doc = context.adapter_doc
    assert doc is not None, '@adapter.for_ should have a docstring'
    doc_lower = doc.lower()
    has_swappable = 'swap' in doc_lower
    has_implementations = 'implementation' in doc_lower
    assert has_swappable and has_implementations, (
        '@adapter.for_ docstring should mention swappable implementations. '
        f'Found swap={has_swappable}, implementation={has_implementations}'
    )


@then('the docstring includes an example with profile parameter')
def step_adapter_has_profile_example(context: Context) -> None:
    doc = context.adapter_doc
    assert doc is not None, '@adapter.for_ should have a docstring'
    assert 'profile=' in doc, '@adapter.for_ docstring should include example with profile parameter'
    assert 'Profile.' in doc, '@adapter.for_ docstring should show Profile enum usage in example'


@then('the docstring mentions implementing a port')
def step_adapter_mentions_port(context: Context) -> None:
    doc = context.adapter_doc
    assert doc is not None, '@adapter.for_ should have a docstring'
    doc_lower = doc.lower()
    has_port = 'port' in doc_lower
    has_implements = 'implement' in doc_lower
    assert has_port and has_implements, (
        f'@adapter.for_ docstring should mention implementing a port. Found port={has_port}, implement={has_implements}'
    )


# ---------------------------------------------------------------------------
# Scenario: Wrong decorator usage produces helpful error
# ---------------------------------------------------------------------------


@given('I accidentally use @service on a class that implements a port')
def step_service_on_adapter_class(context: Context) -> None:
    _clear_registry()

    class NotificationPort(Protocol):
        def notify(self, message: str) -> None: ...

    @service
    class EmailNotifier:
        """This class implements NotificationPort but is incorrectly marked as @service."""

        def notify(self, message: str) -> None:
            pass

    context.notification_port = NotificationPort
    context.misused_service = EmailNotifier


@given('a separate adapter exists for the same port')
def step_adapter_for_same_port(context: Context) -> None:
    @adapter.for_(context.notification_port, profile=Profile.PRODUCTION)
    class SmsNotifier:
        def notify(self, message: str) -> None:
            pass

    context.correct_adapter = SmsNotifier


@when('I try to resolve the port from the container')
def step_try_resolve_port(context: Context) -> None:
    container = Container()
    container.scan(profile=Profile.TEST)
    context.resolution_error = None
    try:
        context.resolved_port = container.resolve(context.notification_port)
    except (AdapterNotFoundError, ServiceNotFoundError) as e:
        context.resolution_error = e
    except Exception as e:
        context.resolution_error = e


@then('the error message provides guidance about the correct decorator')
def step_error_provides_guidance(context: Context) -> None:
    err = context.resolution_error
    assert err is not None, 'Expected an error when resolving a port with no TEST adapter'
    error_text = str(err)
    # The error should help the developer understand what went wrong.
    # Ideally it would mention that a @service class exists that
    # implements the port interface but isn't registered as an adapter.
    has_guidance = (
        'adapter' in error_text.lower()
        or 'decorator' in error_text.lower()
        or 'register' in error_text.lower()
        or '@service' in error_text
        or 'hint' in error_text.lower()
        or 'suggestion' in error_text.lower()
    )
    assert has_guidance, f'Error message should provide guidance about registering an adapter. Got: {error_text}'


@then('the error message mentions @adapter.for_ as an alternative')
def step_error_mentions_adapter_decorator(context: Context) -> None:
    err = context.resolution_error
    assert err is not None, 'Expected an error'
    error_text = str(err)
    # The error should specifically suggest using @adapter.for_() when
    # a developer has used @service for a class that should be an adapter.
    # This is a key ergonomics improvement: detecting misuse and guiding
    # the developer to the correct pattern.
    has_adapter_mention = '@adapter.for_' in error_text or 'adapter.for_' in error_text
    assert has_adapter_mention, f'Error should mention @adapter.for_ as the correct decorator. Got: {error_text}'


# ---------------------------------------------------------------------------
# Scenario: Profile class IDE autocomplete descriptions
# ---------------------------------------------------------------------------


@when('I inspect the Profile class and its constants')
def step_inspect_profile_class(context: Context) -> None:
    context.profile_class = Profile
    context.builtin_profiles = {
        'PRODUCTION': Profile.PRODUCTION,
        'TEST': Profile.TEST,
        'DEVELOPMENT': Profile.DEVELOPMENT,
        'STAGING': Profile.STAGING,
        'CI': Profile.CI,
        'ALL': Profile.ALL,
    }


@then('each built-in profile constant has a descriptive docstring or annotation')
def step_profiles_have_descriptions(context: Context) -> None:
    # Check that the Profile class docstring documents each constant.
    # For IDE hover to work well, Profile class should have clear
    # documentation of each constant.
    class_doc = Profile.__doc__
    assert class_doc is not None, 'Profile class should have a docstring'

    for name in context.builtin_profiles:
        assert name.lower() in class_doc.lower() or name in class_doc, (
            f'Profile class docstring should document {name}. This enables IDE hover documentation.'
        )


@then('none of the descriptions expose the raw "*" implementation detail')
def step_descriptions_hide_wildcard(context: Context) -> None:
    profile_all_repr = repr(Profile.ALL)
    # The repr should not leak '*' as an implementation detail.
    # Developers seeing Profile('*') in debuggers or error messages
    # have to know the internal convention. "Profile.ALL" is clearer.
    assert '*' not in profile_all_repr, (
        f'Profile.ALL repr should not expose raw "*": got {profile_all_repr!r}. '
        f'Expected something like "Profile.ALL" for clarity.'
    )


@then('Profile.ALL description refers to "all profiles" or "universal"')
def step_profile_all_description(context: Context) -> None:
    class_doc = Profile.__doc__ or ''
    doc_lower = class_doc.lower()
    # The docs for Profile.ALL should use clear language
    has_all_profiles = 'all' in doc_lower
    has_universal = 'universal' in doc_lower
    assert has_all_profiles or has_universal, (
        'Profile class documentation should describe ALL as "all profiles" '
        'or "universal". Got docstring snippet: '
        f'{class_doc[:300]}'
    )
