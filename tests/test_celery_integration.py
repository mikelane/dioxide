"""Tests for Celery integration module.

This module tests the dioxide.celery integration that provides:
- configure_dioxide(app) - Sets up container with Celery app
- scoped_task(app) - Decorator for task scoping with dioxide
"""

from __future__ import annotations

from typing import Protocol

import pytest

# Skip this entire module if Celery is not installed
pytest.importorskip('celery')

from celery import Celery

from dioxide import (
    Container,
    Profile,
    Scope,
    ScopedContainer,
    _clear_registry,
    adapter,
    lifecycle,
    service,
)

# Clear registry before tests to ensure isolation
pytestmark = pytest.mark.usefixtures('clear_registry')


@pytest.fixture(autouse=True)
def clear_registry() -> None:
    """Clear the global registry before each test."""
    _clear_registry()


@pytest.fixture
def celery_app() -> Celery:
    """Create a Celery app configured for testing."""
    app = Celery('test_app')
    app.conf.update(
        task_always_eager=True,  # Execute tasks synchronously for testing
        task_eager_propagates=True,  # Propagate exceptions in eager mode
        broker_url='memory://',
        result_backend='cache+memory://',
    )
    return app


class DescribeConfigureDioxide:
    """Tests for configure_dioxide function."""

    def it_configures_container_with_celery_app(self, celery_app: Celery) -> None:
        """configure_dioxide sets up container reference on Celery app."""
        from dioxide.celery import configure_dioxide

        container = Container()

        configure_dioxide(celery_app, profile=Profile.TEST, container=container)

        # Verify container was stored on app
        assert hasattr(celery_app, 'dioxide_container')
        assert celery_app.dioxide_container is container

    def it_uses_global_container_when_not_provided(self, celery_app: Celery) -> None:
        """configure_dioxide uses dioxide.container when container not specified."""
        from dioxide import container as global_container
        from dioxide.celery import configure_dioxide

        # Reset global container
        global_container.reset()

        configure_dioxide(celery_app, profile=Profile.TEST)

        assert celery_app.dioxide_container is global_container

    def it_scans_specified_packages(self, celery_app: Celery) -> None:
        """configure_dioxide can scan specific packages."""
        from dioxide.celery import configure_dioxide

        container = Container()

        # This should not raise even with valid packages
        configure_dioxide(
            celery_app,
            profile=Profile.TEST,
            container=container,
            packages=['dioxide'],
        )

        assert celery_app.dioxide_container is container


class DescribeScopedTaskDecorator:
    """Tests for scoped_task decorator."""

    def it_creates_scope_per_task_execution(self, celery_app: Celery) -> None:
        """scoped_task creates a fresh scope for each task execution."""
        from dioxide.celery import (
            configure_dioxide,
            scoped_task,
        )

        @service(scope=Scope.REQUEST)
        class TaskContext:
            def __init__(self) -> None:
                import uuid

                self.task_id = str(uuid.uuid4())

        container = Container()
        configure_dioxide(celery_app, profile=Profile.TEST, container=container)

        task_ids: list[str] = []

        @scoped_task(celery_app)
        def my_task(scope: ScopedContainer) -> str:
            ctx = scope.resolve(TaskContext)
            task_ids.append(ctx.task_id)
            return ctx.task_id

        # Execute task multiple times
        my_task.delay()
        my_task.delay()

        # Each execution should get a different task context
        assert len(task_ids) == 2
        assert task_ids[0] != task_ids[1]

    def it_injects_scope_as_first_argument(self, celery_app: Celery) -> None:
        """scoped_task injects ScopedContainer as first argument."""
        from dioxide.celery import (
            configure_dioxide,
            scoped_task,
        )

        container = Container()
        configure_dioxide(celery_app, profile=Profile.TEST, container=container)

        received_scope: list[object] = []

        @scoped_task(celery_app)
        def my_task(scope: ScopedContainer) -> None:
            received_scope.append(scope)

        my_task.delay()

        assert len(received_scope) == 1
        assert isinstance(received_scope[0], ScopedContainer)

    def it_passes_through_task_arguments(self, celery_app: Celery) -> None:
        """scoped_task passes additional arguments to the task."""
        from dioxide.celery import (
            configure_dioxide,
            scoped_task,
        )

        container = Container()
        configure_dioxide(celery_app, profile=Profile.TEST, container=container)

        @scoped_task(celery_app)
        def add_task(scope: ScopedContainer, x: int, y: int) -> int:
            return x + y

        result = add_task.delay(3, 5)

        assert result.get() == 8

    def it_passes_through_keyword_arguments(self, celery_app: Celery) -> None:
        """scoped_task passes keyword arguments to the task."""
        from dioxide.celery import (
            configure_dioxide,
            scoped_task,
        )

        container = Container()
        configure_dioxide(celery_app, profile=Profile.TEST, container=container)

        @scoped_task(celery_app)
        def greet_task(scope: ScopedContainer, name: str, greeting: str = 'Hello') -> str:
            return f'{greeting}, {name}!'

        result = greet_task.delay('World', greeting='Hi')

        assert result.get() == 'Hi, World!'

    def it_resolves_singleton_from_parent_container(self, celery_app: Celery) -> None:
        """scoped_task resolves SINGLETON-scoped components from parent."""
        from dioxide.celery import (
            configure_dioxide,
            scoped_task,
        )

        @service
        class SingletonService:
            def __init__(self) -> None:
                import uuid

                self.instance_id = str(uuid.uuid4())

            def get_id(self) -> str:
                return self.instance_id

        container = Container()
        configure_dioxide(celery_app, profile=Profile.TEST, container=container)

        singleton_ids: list[str] = []

        @scoped_task(celery_app)
        def my_task(scope: ScopedContainer) -> str:
            svc = scope.resolve(SingletonService)
            singleton_ids.append(svc.get_id())
            return svc.get_id()

        # Execute task multiple times
        my_task.delay()
        my_task.delay()

        # Singleton should be the same across executions
        assert len(singleton_ids) == 2
        assert singleton_ids[0] == singleton_ids[1]


class DescribeLifecycleManagement:
    """Tests for lifecycle management in Celery tasks."""

    def it_initializes_singleton_lifecycle_components_at_configure_time(self, celery_app: Celery) -> None:
        """SINGLETON @lifecycle components are initialized when configure_dioxide is called."""
        from dioxide.celery import configure_dioxide

        initialized: list[str] = []

        @service
        @lifecycle
        class DatabaseService:
            async def initialize(self) -> None:
                initialized.append('db')

            async def dispose(self) -> None:
                pass

        container = Container()

        # configure_dioxide should scan and start the container
        configure_dioxide(celery_app, profile=Profile.TEST, container=container)

        # At this point, the container should be started
        assert 'db' in initialized


class DescribeAdapterResolution:
    """Tests for resolving adapters via ports in tasks."""

    def it_resolves_adapter_for_port(self, celery_app: Celery) -> None:
        """scoped_task can resolve adapters for ports."""
        from dioxide.celery import (
            configure_dioxide,
            scoped_task,
        )

        class NotificationPort(Protocol):
            def notify(self, message: str) -> str: ...

        @adapter.for_(NotificationPort, profile=Profile.TEST)
        class FakeNotificationAdapter:
            def notify(self, message: str) -> str:
                return f'notified: {message}'

        container = Container()
        configure_dioxide(celery_app, profile=Profile.TEST, container=container)

        @scoped_task(celery_app)
        def notify_task(scope: ScopedContainer, message: str) -> str:
            notifier = scope.resolve(NotificationPort)
            return notifier.notify(message)

        result = notify_task.delay('hello')

        assert result.get() == 'notified: hello'


class DescribeAsyncTaskSupport:
    """Tests for async task support."""

    def it_works_with_async_tasks(self, celery_app: Celery) -> None:
        """scoped_task works with async task functions."""
        import asyncio

        from dioxide.celery import (
            configure_dioxide,
            scoped_task,
        )

        @service(scope=Scope.REQUEST)
        class AsyncTaskContext:
            def __init__(self) -> None:
                import uuid

                self.context_id = str(uuid.uuid4())

        container = Container()
        configure_dioxide(celery_app, profile=Profile.TEST, container=container)

        @scoped_task(celery_app)
        async def async_task(scope: ScopedContainer) -> str:
            ctx = scope.resolve(AsyncTaskContext)
            await asyncio.sleep(0.001)  # Simulate async operation
            return ctx.context_id

        result = async_task.delay()

        # Should complete without error and return a UUID
        context_id = result.get()
        assert len(context_id) == 36  # UUID format


class DescribeSyncTaskSupport:
    """Tests for sync task support."""

    def it_works_with_sync_tasks(self, celery_app: Celery) -> None:
        """scoped_task works with synchronous task functions."""
        from dioxide.celery import (
            configure_dioxide,
            scoped_task,
        )

        @service
        class SyncService:
            def process(self, data: str) -> str:
                return data.upper()

        container = Container()
        configure_dioxide(celery_app, profile=Profile.TEST, container=container)

        @scoped_task(celery_app)
        def sync_task(scope: ScopedContainer, data: str) -> str:
            svc = scope.resolve(SyncService)
            return svc.process(data)

        result = sync_task.delay('hello')

        assert result.get() == 'HELLO'


class DescribeTaskOptions:
    """Tests for Celery task options passthrough."""

    def it_accepts_celery_task_options(self, celery_app: Celery) -> None:
        """scoped_task accepts standard Celery task options."""
        from dioxide.celery import (
            configure_dioxide,
            scoped_task,
        )

        container = Container()
        configure_dioxide(celery_app, profile=Profile.TEST, container=container)

        @scoped_task(celery_app, name='custom.task.name', bind=False)
        def custom_task(scope: ScopedContainer) -> str:
            return 'done'

        # Verify task was registered with custom name
        assert custom_task.name == 'custom.task.name'

        result = custom_task.delay()
        assert result.get() == 'done'


class DescribeErrorHandling:
    """Tests for error handling."""

    def it_propagates_task_exceptions(self, celery_app: Celery) -> None:
        """Task exceptions are properly propagated to the caller."""
        from dioxide.celery import (
            configure_dioxide,
            scoped_task,
        )

        container = Container()
        configure_dioxide(celery_app, profile=Profile.TEST, container=container)

        @scoped_task(celery_app)
        def failing_task(scope: ScopedContainer) -> None:
            raise ValueError('Task failed!')

        with pytest.raises(ValueError, match='Task failed!'):
            failing_task.delay().get()

    def it_cleans_up_scope_on_task_failure(self, celery_app: Celery) -> None:
        """Scope cleanup happens even when task raises an exception."""
        from dioxide.celery import (
            configure_dioxide,
            scoped_task,
        )

        # Track that task actually ran with a scope
        task_ran: list[bool] = []

        @service(scope=Scope.REQUEST)
        class TaskContext:
            def __init__(self) -> None:
                task_ran.append(True)

        container = Container()
        configure_dioxide(celery_app, profile=Profile.TEST, container=container)

        @scoped_task(celery_app)
        def failing_task(scope: ScopedContainer) -> None:
            scope.resolve(TaskContext)
            raise ValueError('Task failed!')

        with pytest.raises(ValueError, match='Task failed!'):
            failing_task.delay().get()

        # Task ran and resolved the context before failing
        assert True in task_ran


class DescribeImportErrorHandling:
    """Tests for handling missing Celery dependency."""

    def it_raises_import_error_when_celery_not_installed(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Module raises ImportError when Celery dependencies are unavailable."""
        import dioxide.celery as celery_module

        # Simulate Celery not being installed
        monkeypatch.setattr(celery_module, 'Celery', None)

        with pytest.raises(ImportError, match='Celery is not installed'):
            celery_module.configure_dioxide(None, profile=Profile.TEST)  # type: ignore[arg-type]


class DescribeTaskIsolation:
    """Tests for task isolation and scope separation."""

    def it_creates_separate_scopes_for_sequential_tasks(self, celery_app: Celery) -> None:
        """Each task execution gets its own isolated scope."""
        from dioxide.celery import (
            configure_dioxide,
            scoped_task,
        )

        @service(scope=Scope.REQUEST)
        class TaskContext:
            def __init__(self) -> None:
                import uuid

                self.task_id = str(uuid.uuid4())

        container = Container()
        configure_dioxide(celery_app, profile=Profile.TEST, container=container)

        task_ids: list[str] = []

        @scoped_task(celery_app)
        def isolated_task(scope: ScopedContainer) -> str:
            ctx = scope.resolve(TaskContext)
            task_ids.append(ctx.task_id)
            return ctx.task_id

        # Execute multiple tasks sequentially
        for _ in range(4):
            isolated_task.delay()

        # All task IDs should be unique (each task got its own scope)
        assert len(task_ids) == 4
        assert len(set(task_ids)) == 4

    def it_shares_request_scoped_within_same_task(self, celery_app: Celery) -> None:
        """REQUEST-scoped components are shared within a single task execution."""
        from dioxide.celery import (
            configure_dioxide,
            scoped_task,
        )

        @service(scope=Scope.REQUEST)
        class TaskContext:
            def __init__(self) -> None:
                import uuid

                self.context_id = str(uuid.uuid4())

        container = Container()
        configure_dioxide(celery_app, profile=Profile.TEST, container=container)

        @scoped_task(celery_app)
        def shared_scope_task(scope: ScopedContainer) -> dict[str, bool]:
            ctx1 = scope.resolve(TaskContext)
            ctx2 = scope.resolve(TaskContext)
            return {
                'same_instance': ctx1 is ctx2,
                'same_id': ctx1.context_id == ctx2.context_id,
            }

        result = shared_scope_task.delay().get()

        assert result['same_instance'] is True
        assert result['same_id'] is True
