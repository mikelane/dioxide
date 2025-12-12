"""Tests for Django REST Framework integration.

This module tests that dioxide.django's inject() function works seamlessly
with Django REST Framework (DRF) patterns:

- APIView class-based views
- ViewSet classes
- @api_view decorated function views
- DRF authentication classes
- DRF permission classes
"""

from __future__ import annotations

from typing import Protocol

import pytest

# Skip this entire module if Django or DRF is not installed
pytest.importorskip('django')
pytest.importorskip('rest_framework')

import django
from django.conf import settings

# Configure Django settings before importing Django test utilities
if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={},
        INSTALLED_APPS=[
            'django.contrib.contenttypes',
            'django.contrib.auth',
            'rest_framework',
        ],
        ROOT_URLCONF=[],
        DEFAULT_CHARSET='utf-8',
        SECRET_KEY='test-secret-key-for-dioxide-drf-testing',
    )
    django.setup()

import pytest
from django.http import HttpRequest
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.test import APIRequestFactory
from rest_framework.views import APIView

from dioxide import (
    Container,
    Profile,
    Scope,
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


class DescribeAPIViewIntegration:
    """Tests for inject() with DRF APIView class-based views."""

    def it_resolves_service_in_apiview_get_method(self) -> None:
        """inject() resolves a service inside APIView.get()."""
        from dioxide.django import (
            DioxideMiddleware,
            configure_dioxide,
            inject,
        )

        @service
        class UserService:
            def get_user(self) -> str:
                return 'test_user'

        container = Container()
        configure_dioxide(profile=Profile.TEST, container=container)

        result: list[str] = []

        class UserView(APIView):
            def get(self, request: Request) -> Response:
                user_service = inject(UserService)
                result.append(user_service.get_user())
                return Response({'user': user_service.get_user()})

        def view_wrapper(request: HttpRequest) -> Response:
            view = UserView.as_view()
            return view(request)

        middleware = DioxideMiddleware(view_wrapper)

        factory = APIRequestFactory()
        request = factory.get('/users/')
        middleware(request)

        assert result[0] == 'test_user'

    def it_resolves_adapter_for_port_in_apiview(self) -> None:
        """inject() resolves the correct adapter for a port in APIView."""
        from dioxide.django import (
            DioxideMiddleware,
            configure_dioxide,
            inject,
        )

        class EmailPort(Protocol):
            def send(self, to: str) -> str: ...

        @adapter.for_(EmailPort, profile=Profile.TEST)
        class FakeEmailAdapter:
            def send(self, to: str) -> str:
                return f'sent to {to}'

        container = Container()
        configure_dioxide(profile=Profile.TEST, container=container)

        result: list[str] = []

        class NotificationView(APIView):
            def post(self, request: Request) -> Response:
                email = inject(EmailPort)
                result.append(email.send('test@example.com'))
                return Response({'status': 'sent'})

        def view_wrapper(request: HttpRequest) -> Response:
            view = NotificationView.as_view()
            return view(request)

        middleware = DioxideMiddleware(view_wrapper)

        factory = APIRequestFactory()
        request = factory.post('/notify/')
        middleware(request)

        assert result[0] == 'sent to test@example.com'

    def it_handles_request_scoped_service_in_apiview(self) -> None:
        """inject() correctly handles REQUEST-scoped services in APIView."""
        from dioxide.django import (
            DioxideMiddleware,
            configure_dioxide,
            inject,
        )

        @service(scope=Scope.REQUEST)
        class RequestContext:
            def __init__(self) -> None:
                import uuid

                self.request_id = str(uuid.uuid4())

        container = Container()
        configure_dioxide(profile=Profile.TEST, container=container)

        request_ids: list[str] = []

        class ContextView(APIView):
            def get(self, request: Request) -> Response:
                ctx = inject(RequestContext)
                request_ids.append(ctx.request_id)
                return Response({'request_id': ctx.request_id})

        def view_wrapper(request: HttpRequest) -> Response:
            view = ContextView.as_view()
            return view(request)

        middleware = DioxideMiddleware(view_wrapper)

        factory = APIRequestFactory()
        request1 = factory.get('/ctx/')
        request2 = factory.get('/ctx/')

        middleware(request1)
        middleware(request2)

        # Each request gets a unique request context
        assert len(request_ids) == 2
        assert request_ids[0] != request_ids[1]

    def it_shares_singleton_across_apiview_requests(self) -> None:
        """inject() shares SINGLETON-scoped instances across APIView requests."""
        from dioxide.django import (
            DioxideMiddleware,
            configure_dioxide,
            inject,
        )

        @service
        class CounterService:
            def __init__(self) -> None:
                self.count = 0

            def increment(self) -> int:
                self.count += 1
                return self.count

        container = Container()
        configure_dioxide(profile=Profile.TEST, container=container)

        counts: list[int] = []

        class CounterView(APIView):
            def get(self, request: Request) -> Response:
                counter = inject(CounterService)
                counts.append(counter.increment())
                return Response({'count': counter.count})

        def view_wrapper(request: HttpRequest) -> Response:
            view = CounterView.as_view()
            return view(request)

        middleware = DioxideMiddleware(view_wrapper)

        factory = APIRequestFactory()
        for _ in range(3):
            request = factory.get('/counter/')
            middleware(request)

        # Singleton should persist across requests
        assert counts == [1, 2, 3]

    def it_works_with_multiple_dependencies_in_apiview(self) -> None:
        """inject() allows multiple dependencies in same APIView method."""
        from dioxide.django import (
            DioxideMiddleware,
            configure_dioxide,
            inject,
        )

        @service
        class ServiceA:
            def get_value(self) -> str:
                return 'A'

        @service
        class ServiceB:
            def get_value(self) -> str:
                return 'B'

        container = Container()
        configure_dioxide(profile=Profile.TEST, container=container)

        result: list[str] = []

        class MultiView(APIView):
            def get(self, request: Request) -> Response:
                service_a = inject(ServiceA)
                service_b = inject(ServiceB)
                combined = f'{service_a.get_value()}-{service_b.get_value()}'
                result.append(combined)
                return Response({'combined': combined})

        def view_wrapper(request: HttpRequest) -> Response:
            view = MultiView.as_view()
            return view(request)

        middleware = DioxideMiddleware(view_wrapper)

        factory = APIRequestFactory()
        request = factory.get('/multi/')
        middleware(request)

        assert result[0] == 'A-B'


class DescribeApiViewDecoratorIntegration:
    """Tests for inject() with @api_view decorated functions."""

    def it_works_with_api_view_decorated_function(self) -> None:
        """inject() works within @api_view decorated functions."""
        from rest_framework.decorators import api_view

        from dioxide.django import (
            DioxideMiddleware,
            configure_dioxide,
            inject,
        )

        @service
        class UserService:
            def get_user(self) -> str:
                return 'api_user'

        container = Container()
        configure_dioxide(profile=Profile.TEST, container=container)

        result: list[str] = []

        @api_view(['GET'])
        def user_list(request: Request) -> Response:
            user_service = inject(UserService)
            result.append(user_service.get_user())
            return Response({'user': user_service.get_user()})

        def view_wrapper(request: HttpRequest) -> Response:
            return user_list(request)

        middleware = DioxideMiddleware(view_wrapper)

        factory = APIRequestFactory()
        request = factory.get('/users/')
        middleware(request)

        assert result[0] == 'api_user'


class DescribeViewSetIntegration:
    """Tests for inject() with DRF ViewSet classes."""

    def it_works_in_viewset_list_action(self) -> None:
        """inject() works in ViewSet.list() action."""
        from rest_framework.viewsets import ViewSet

        from dioxide.django import (
            DioxideMiddleware,
            configure_dioxide,
            inject,
        )

        @service
        class ItemService:
            def list_items(self) -> list[str]:
                return ['item1', 'item2']

        container = Container()
        configure_dioxide(profile=Profile.TEST, container=container)

        result: list[list[str]] = []

        class ItemViewSet(ViewSet):
            def list(self, request: Request) -> Response:
                item_service = inject(ItemService)
                items = item_service.list_items()
                result.append(items)
                return Response({'items': items})

        def view_wrapper(request: HttpRequest) -> Response:
            view = ItemViewSet.as_view({'get': 'list'})
            return view(request)

        middleware = DioxideMiddleware(view_wrapper)

        factory = APIRequestFactory()
        request = factory.get('/items/')
        middleware(request)

        assert result[0] == ['item1', 'item2']

    def it_works_in_viewset_retrieve_action(self) -> None:
        """inject() works in ViewSet.retrieve() action."""
        from rest_framework.viewsets import ViewSet

        from dioxide.django import (
            DioxideMiddleware,
            configure_dioxide,
            inject,
        )

        @service
        class ItemService:
            def get_item(self, pk: str) -> dict[str, str]:
                return {'id': pk, 'name': f'Item {pk}'}

        container = Container()
        configure_dioxide(profile=Profile.TEST, container=container)

        result: list[dict[str, str]] = []

        class ItemViewSet(ViewSet):
            def retrieve(self, request: Request, pk: str | None = None) -> Response:
                item_service = inject(ItemService)
                item = item_service.get_item(pk or '0')
                result.append(item)
                return Response(item)

        def view_wrapper(request: HttpRequest) -> Response:
            view = ItemViewSet.as_view({'get': 'retrieve'})
            return view(request, pk='42')

        middleware = DioxideMiddleware(view_wrapper)

        factory = APIRequestFactory()
        request = factory.get('/items/42/')
        middleware(request)

        assert result[0] == {'id': '42', 'name': 'Item 42'}


class DescribeLifecycleIntegration:
    """Tests for lifecycle integration with DRF views."""

    def it_disposes_request_scoped_lifecycle_components(self) -> None:
        """inject() properly disposes REQUEST-scoped @lifecycle components after DRF request."""
        from dioxide.django import (
            DioxideMiddleware,
            configure_dioxide,
            inject,
        )

        disposed: list[str] = []

        @service(scope=Scope.REQUEST)
        @lifecycle
        class RequestResource:
            async def initialize(self) -> None:
                pass

            async def dispose(self) -> None:
                disposed.append('resource')

        container = Container()
        configure_dioxide(profile=Profile.TEST, container=container)

        class ResourceView(APIView):
            def get(self, request: Request) -> Response:
                inject(RequestResource)
                return Response({'status': 'ok'})

        def view_wrapper(request: HttpRequest) -> Response:
            view = ResourceView.as_view()
            return view(request)

        middleware = DioxideMiddleware(view_wrapper)

        factory = APIRequestFactory()
        request = factory.get('/resource/')
        middleware(request)

        # After request completes, scope should be disposed
        assert 'resource' in disposed
