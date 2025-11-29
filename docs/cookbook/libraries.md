# Building dioxide-Compatible Libraries

## Problem

You're a library author who wants to make your library work seamlessly with dioxide-based applications, but you don't want to:

- Add dioxide as a dependency (keeping your library lightweight)
- Force users to use any specific DI framework
- Compromise on testability for your own library

How do you build a library that works great with dioxide but doesn't require it?

## Solution

Use **optional dependency injection with sensible defaults**:

1. Define your ports (interfaces) using Python's `Protocol`
2. Provide default implementations that work out of the box
3. Accept optional dependency injection through constructor parameters
4. Let dioxide users inject their own adapters when needed

This pattern makes your library:

- **Zero-config for simple use cases** - Works immediately without any DI framework
- **dioxide-friendly** - Users can inject fakes or custom implementations
- **Framework-agnostic** - Works with any DI framework (or none at all)

## Complete Example: HTTP Client Library

Let's build a complete mini-library that fetches data from an API.

### Step 1: Define the Port (Interface)

```python
# mylib/ports.py
from typing import Protocol
from dataclasses import dataclass

@dataclass
class Response:
    """HTTP response container."""
    status_code: int
    body: str
    headers: dict[str, str]

class HttpPort(Protocol):
    """Port for HTTP operations.

    This interface defines the contract for HTTP clients.
    Libraries and applications can provide their own implementations.
    """
    def get(self, url: str, headers: dict[str, str] | None = None) -> Response:
        """Perform HTTP GET request.

        Args:
            url: The URL to fetch
            headers: Optional request headers

        Returns:
            Response object with status, body, and headers

        Raises:
            ConnectionError: If the request fails
        """
        ...

    def post(self, url: str, body: str, headers: dict[str, str] | None = None) -> Response:
        """Perform HTTP POST request.

        Args:
            url: The URL to post to
            body: Request body (typically JSON string)
            headers: Optional request headers

        Returns:
            Response object with status, body, and headers

        Raises:
            ConnectionError: If the request fails
        """
        ...
```

### Step 2: Provide a Default Implementation

```python
# mylib/adapters.py
import urllib.request
import urllib.error
from .ports import HttpPort, Response

class DefaultHttpAdapter:
    """Default HTTP adapter using urllib (no external dependencies).

    This adapter is used when no custom HTTP client is provided.
    It uses Python's built-in urllib for zero-dependency operation.
    """

    def get(self, url: str, headers: dict[str, str] | None = None) -> Response:
        """Perform HTTP GET using urllib."""
        req = urllib.request.Request(url, headers=headers or {})
        try:
            with urllib.request.urlopen(req) as response:
                return Response(
                    status_code=response.status,
                    body=response.read().decode('utf-8'),
                    headers=dict(response.headers)
                )
        except urllib.error.HTTPError as e:
            return Response(
                status_code=e.code,
                body=e.read().decode('utf-8'),
                headers=dict(e.headers)
            )

    def post(self, url: str, body: str, headers: dict[str, str] | None = None) -> Response:
        """Perform HTTP POST using urllib."""
        req_headers = {"Content-Type": "application/json", **(headers or {})}
        req = urllib.request.Request(url, data=body.encode('utf-8'), headers=req_headers)
        try:
            with urllib.request.urlopen(req) as response:
                return Response(
                    status_code=response.status,
                    body=response.read().decode('utf-8'),
                    headers=dict(response.headers)
                )
        except urllib.error.HTTPError as e:
            return Response(
                status_code=e.code,
                body=e.read().decode('utf-8'),
                headers=dict(e.headers)
            )
```

### Step 3: Build the Library Client with Optional Injection

```python
# mylib/client.py
from __future__ import annotations
import json
from dataclasses import dataclass
from .ports import HttpPort, Response
from .adapters import DefaultHttpAdapter

@dataclass
class WeatherData:
    """Weather information for a location."""
    city: str
    temperature: float
    conditions: str
    humidity: int

class WeatherClient:
    """Client for fetching weather data.

    Works with or without a DI framework. If no HTTP client is provided,
    uses the built-in DefaultHttpAdapter.

    Examples:
        # Simple usage (no DI framework needed)
        client = WeatherClient(api_key="your-key")
        weather = client.get_weather("Seattle")

        # With custom HTTP client
        client = WeatherClient(api_key="your-key", http=my_custom_http)

        # With dioxide (inject via container)
        http = container.resolve(HttpPort)
        client = WeatherClient(api_key="your-key", http=http)
    """

    def __init__(
        self,
        api_key: str,
        http: HttpPort | None = None,  # Optional injection point
        base_url: str = "https://api.weather.example.com"
    ):
        self.api_key = api_key
        self.base_url = base_url
        # Use provided HTTP client or fall back to default
        self.http = http or DefaultHttpAdapter()

    def get_weather(self, city: str) -> WeatherData:
        """Fetch current weather for a city.

        Args:
            city: City name to get weather for

        Returns:
            WeatherData with current conditions

        Raises:
            ValueError: If city not found
            ConnectionError: If API request fails
        """
        url = f"{self.base_url}/v1/weather?city={city}"
        headers = {"Authorization": f"Bearer {self.api_key}"}

        response = self.http.get(url, headers=headers)

        if response.status_code == 404:
            raise ValueError(f"City not found: {city}")

        if response.status_code != 200:
            raise ConnectionError(f"API error: {response.status_code}")

        data = json.loads(response.body)
        return WeatherData(
            city=data["city"],
            temperature=data["temperature"],
            conditions=data["conditions"],
            humidity=data["humidity"]
        )

    def get_forecast(self, city: str, days: int = 5) -> list[WeatherData]:
        """Fetch weather forecast for a city.

        Args:
            city: City name to get forecast for
            days: Number of days to forecast (1-14)

        Returns:
            List of WeatherData for each day
        """
        url = f"{self.base_url}/v1/forecast?city={city}&days={days}"
        headers = {"Authorization": f"Bearer {self.api_key}"}

        response = self.http.get(url, headers=headers)

        if response.status_code != 200:
            raise ConnectionError(f"API error: {response.status_code}")

        data = json.loads(response.body)
        return [
            WeatherData(
                city=city,
                temperature=day["temperature"],
                conditions=day["conditions"],
                humidity=day["humidity"]
            )
            for day in data["forecast"]
        ]
```

### Step 4: Export Public API

```python
# mylib/__init__.py
"""Weather client library - works with or without DI frameworks."""

from .client import WeatherClient, WeatherData
from .ports import HttpPort, Response
from .adapters import DefaultHttpAdapter

__all__ = [
    "WeatherClient",
    "WeatherData",
    "HttpPort",
    "Response",
    "DefaultHttpAdapter",
]
```

## Usage Without dioxide

Users who don't use dioxide can use your library immediately:

```python
from mylib import WeatherClient

# Just works - uses DefaultHttpAdapter internally
client = WeatherClient(api_key="my-api-key")
weather = client.get_weather("Seattle")

print(f"{weather.city}: {weather.temperature}F, {weather.conditions}")
# Output: Seattle: 52.3F, Partly Cloudy
```

No configuration, no DI framework, no ceremony.

## Usage With dioxide

Users who use dioxide can inject their own adapters:

### Production: Custom HTTP Client

```python
# app/adapters/http.py
from dioxide import adapter, Profile
from mylib import HttpPort, Response
import httpx

@adapter.for_(HttpPort, profile=Profile.PRODUCTION)
class HttpxAdapter:
    """Production HTTP adapter using httpx for better performance."""

    def __init__(self):
        self.client = httpx.Client(timeout=30.0)

    def get(self, url: str, headers: dict[str, str] | None = None) -> Response:
        resp = self.client.get(url, headers=headers or {})
        return Response(
            status_code=resp.status_code,
            body=resp.text,
            headers=dict(resp.headers)
        )

    def post(self, url: str, body: str, headers: dict[str, str] | None = None) -> Response:
        resp = self.client.post(url, content=body, headers=headers or {})
        return Response(
            status_code=resp.status_code,
            body=resp.text,
            headers=dict(resp.headers)
        )
```

### Testing: Fake HTTP Client

```python
# app/adapters/fake_http.py
from dioxide import adapter, Profile
from mylib import HttpPort, Response
import json

@adapter.for_(HttpPort, profile=Profile.TEST)
class FakeHttpAdapter:
    """Fake HTTP adapter for testing - no network calls."""

    def __init__(self):
        self.requests: list[dict] = []
        self.responses: dict[str, Response] = {}
        self.default_response = Response(
            status_code=200,
            body='{"city": "Seattle", "temperature": 52.3, "conditions": "Sunny", "humidity": 65}',
            headers={}
        )

    def get(self, url: str, headers: dict[str, str] | None = None) -> Response:
        self.requests.append({"method": "GET", "url": url, "headers": headers})
        return self.responses.get(url, self.default_response)

    def post(self, url: str, body: str, headers: dict[str, str] | None = None) -> Response:
        self.requests.append({"method": "POST", "url": url, "body": body, "headers": headers})
        return self.responses.get(url, self.default_response)

    # Test helpers (not part of HttpPort)
    def stub_response(self, url: str, response: Response) -> None:
        """Configure a specific response for a URL."""
        self.responses[url] = response

    def clear(self) -> None:
        """Reset state between tests."""
        self.requests.clear()
        self.responses.clear()
```

### Wiring It Together

```python
# app/main.py
import asyncio
from dioxide import Container, Profile
from mylib import WeatherClient, HttpPort

async def main():
    # Production: Container(profile=...) auto-scans and activates HttpxAdapter
    async with Container(profile=Profile.PRODUCTION) as container:
        # Resolve HTTP adapter and inject into library
        http = container.resolve(HttpPort)
        client = WeatherClient(api_key="my-api-key", http=http)

        # Now using httpx under the hood
        weather = client.get_weather("Seattle")
        print(f"{weather.city}: {weather.temperature}F")

if __name__ == "__main__":
    asyncio.run(main())
```

### Testing the Integration

```python
# tests/test_weather_integration.py
import pytest
from dioxide import Container, Profile
from mylib import WeatherClient, HttpPort, Response

@pytest.fixture
def container():
    """Container with test fakes."""
    return Container(profile=Profile.TEST)

@pytest.fixture
def fake_http(container):
    """Get the fake HTTP adapter."""
    return container.resolve(HttpPort)

@pytest.fixture
def weather_client(container):
    """WeatherClient with fake HTTP injected."""
    http = container.resolve(HttpPort)
    return WeatherClient(api_key="test-key", http=http)

def test_fetches_weather_from_api(weather_client, fake_http):
    """Fetches weather data and parses response correctly."""
    # Arrange - stub a specific response
    fake_http.stub_response(
        "https://api.weather.example.com/v1/weather?city=Portland",
        Response(
            status_code=200,
            body='{"city": "Portland", "temperature": 48.5, "conditions": "Rainy", "humidity": 85}',
            headers={}
        )
    )

    # Act
    weather = weather_client.get_weather("Portland")

    # Assert
    assert weather.city == "Portland"
    assert weather.temperature == 48.5
    assert weather.conditions == "Rainy"
    assert weather.humidity == 85

    # Verify the request was made correctly
    assert len(fake_http.requests) == 1
    assert fake_http.requests[0]["url"] == "https://api.weather.example.com/v1/weather?city=Portland"
    assert "Authorization" in fake_http.requests[0]["headers"]

def test_raises_value_error_for_unknown_city(weather_client, fake_http):
    """Raises ValueError when city is not found."""
    # Arrange - stub a 404 response
    fake_http.stub_response(
        "https://api.weather.example.com/v1/weather?city=Atlantis",
        Response(status_code=404, body='{"error": "City not found"}', headers={})
    )

    # Act & Assert
    with pytest.raises(ValueError, match="City not found: Atlantis"):
        weather_client.get_weather("Atlantis")

def test_raises_connection_error_on_api_failure(weather_client, fake_http):
    """Raises ConnectionError when API returns server error."""
    # Arrange - stub a 500 response
    fake_http.stub_response(
        "https://api.weather.example.com/v1/weather?city=Seattle",
        Response(status_code=500, body='{"error": "Internal error"}', headers={})
    )

    # Act & Assert
    with pytest.raises(ConnectionError, match="API error: 500"):
        weather_client.get_weather("Seattle")
```

## Testing Your Library (Without dioxide)

Your library should have its own tests that don't require dioxide:

```python
# tests/test_weather_client.py
import pytest
from mylib import WeatherClient, HttpPort, Response

class FakeHttp:
    """Test fake for HttpPort - used in library's own tests."""

    def __init__(self):
        self.canned_response = Response(
            status_code=200,
            body='{"city": "Test City", "temperature": 70.0, "conditions": "Clear", "humidity": 50}',
            headers={}
        )

    def get(self, url: str, headers: dict[str, str] | None = None) -> Response:
        return self.canned_response

    def post(self, url: str, body: str, headers: dict[str, str] | None = None) -> Response:
        return self.canned_response

def test_parses_weather_response():
    """Parses API response into WeatherData."""
    fake_http = FakeHttp()
    client = WeatherClient(api_key="test", http=fake_http)

    weather = client.get_weather("Test City")

    assert weather.city == "Test City"
    assert weather.temperature == 70.0
    assert weather.conditions == "Clear"

def test_raises_on_404():
    """Raises ValueError for 404 responses."""
    fake_http = FakeHttp()
    fake_http.canned_response = Response(status_code=404, body="{}", headers={})
    client = WeatherClient(api_key="test", http=fake_http)

    with pytest.raises(ValueError, match="City not found"):
        client.get_weather("Unknown")

def test_uses_default_adapter_when_none_provided():
    """Falls back to DefaultHttpAdapter when http is None."""
    from mylib.adapters import DefaultHttpAdapter

    client = WeatherClient(api_key="test")

    assert isinstance(client.http, DefaultHttpAdapter)
```

## Explanation

### Why This Pattern Works

1. **No dioxide dependency**: Your library uses only Python's `Protocol` from `typing` - no external dependencies for the DI pattern.

2. **Sensible defaults**: The `DefaultHttpAdapter` means users can use your library immediately without any configuration.

3. **Optional injection**: The `http: HttpPort | None = None` parameter provides an escape hatch for users who need custom behavior.

4. **dioxide compatibility**: Because you export `HttpPort`, dioxide users can register their own adapters and inject them.

5. **Testability**: Both your library and your users can easily test by providing fake implementations.

### The Pattern in One Sentence

> Depend on a Protocol, provide a default implementation, accept optional injection.

### Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| Use `Protocol` not ABC | No inheritance required, works with duck typing |
| Default to `None` | Makes injection optional, not required |
| Export the Port | Lets users create their own adapters |
| Export the default adapter | Lets users extend or wrap it |
| No dioxide imports | Library stays framework-agnostic |

## See Also

- [Hexagonal Architecture](../user_guide/hexagonal_architecture.md) - Understanding ports and adapters
- [Testing with Fakes](../user_guide/testing_with_fakes.rst) - Writing effective test fakes and using profiles

## Summary

Building dioxide-compatible libraries is about being a **good ecosystem citizen**:

1. **Define interfaces** using `Protocol` (no dependencies)
2. **Provide defaults** that work out of the box
3. **Accept injection** optionally through constructor parameters
4. **Export your ports** so users can implement them

Your users get the best of both worlds:

- **Without dioxide**: Library works immediately with zero configuration
- **With dioxide**: Full DI integration with custom adapters and fakes

This pattern respects user choice while enabling powerful testing and customization for those who want it.
