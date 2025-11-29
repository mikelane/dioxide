# Testing Patterns

Recipes for testing dioxide applications with fakes instead of mocks.

---

## Recipe: Container Fixture

### Problem

You want complete test isolation with a fresh container for each test.

### Solution

Create a pytest fixture that provides a fresh container instance per test.

### Code

```python
"""Fresh container per test - the recommended pattern."""
import pytest
from dioxide import Container, Profile


@pytest.fixture
async def container():
    """Fresh container with complete test isolation.

    Each test gets:
    - Clean singleton cache (no state from previous tests)
    - Fresh adapter instances
    - Automatic lifecycle management
    """
    async with Container(profile=Profile.TEST) as c:
        yield c
    # Cleanup happens automatically


@pytest.fixture
def sync_container():
    """Synchronous version for non-async tests."""
    return Container(profile=Profile.TEST)


# Usage in tests
async def test_user_registration(container):
    """Each test gets isolated container."""
    service = container.resolve(UserService)
    result = await service.register("alice@example.com")
    assert result is not None
```

### Explanation

1. **Fresh per test**: Each test gets a new `Container()` instance
2. **Complete isolation**: No singleton state bleeds between tests
3. **Lifecycle managed**: `async with c` handles initialization and cleanup
4. **Async fixture**: Use `async def` for fixtures that need lifecycle

---

## Recipe: Typed Fake Access

### Problem

You want IDE autocomplete and type checking when accessing fake adapters in tests.

### Solution

Create typed fixtures that cast the resolved adapter to the fake type.

### Code

```python
"""Typed fixtures for IDE-friendly fake access."""
from typing import TYPE_CHECKING

import pytest
from dioxide import Container, Profile

from app.domain.ports import EmailPort, UserRepository

if TYPE_CHECKING:
    from app.adapters.fakes import FakeEmailAdapter, FakeUserRepository


@pytest.fixture
async def container():
    """Fresh container per test."""
    async with Container(profile=Profile.TEST) as c:
        yield c


@pytest.fixture
def fake_email(container) -> "FakeEmailAdapter":
    """Typed access to fake email adapter.

    Provides autocomplete for:
    - fake_email.sent_emails
    - fake_email.clear()
    - fake_email.was_welcome_email_sent_to(email)
    """
    return container.resolve(EmailPort)  # type: ignore[return-value]


@pytest.fixture
def fake_users(container) -> "FakeUserRepository":
    """Typed access to fake user repository.

    Provides autocomplete for:
    - fake_users.users
    - fake_users.seed(user1, user2)
    """
    return container.resolve(UserRepository)  # type: ignore[return-value]


# Usage with full IDE support
async def test_welcome_email_sent(container, fake_email, fake_users):
    """IDE knows fake_email has .sent_emails attribute."""
    # Seed test data
    fake_users.seed({"id": 1, "name": "Alice", "email": "alice@example.com"})

    # Run service
    service = container.resolve(NotificationService)
    await service.send_welcome(1)

    # Verify with autocomplete
    assert len(fake_email.sent_emails) == 1
    assert fake_email.was_welcome_email_sent_to("alice@example.com")
```

### Explanation

1. **TYPE_CHECKING import**: Only import fake types during type checking, not runtime
2. **String annotation**: Use quotes for forward reference to avoid import issues
3. **Type ignore**: Tell type checker the cast is intentional
4. **IDE support**: Now you get autocomplete for fake-specific methods

---

## Recipe: Async Test Setup

### Problem

You need to test async services with pytest.

### Solution

Use pytest-asyncio with async fixtures and test functions.

### Code

```python
"""Async testing with pytest-asyncio."""
import pytest
from dioxide import Container, Profile

# In pyproject.toml:
# [tool.pytest.ini_options]
# asyncio_mode = "auto"


@pytest.fixture
async def container():
    """Async fixture with lifecycle management."""
    c = Container()
    c.scan(profile=Profile.TEST)

    async with c:
        yield c


@pytest.fixture
async def service(container):
    """Resolve async service."""
    return container.resolve(UserService)


# Test functions can be async
async def test_async_operation(service, fake_email):
    """Test async service method."""
    await service.register_user("Alice", "alice@example.com")

    assert len(fake_email.sent_emails) == 1


# Class-based async tests
class DescribeUserService:
    """Tests for UserService."""

    async def it_registers_new_user(self, service, fake_users):
        """Creates user in repository."""
        result = await service.register_user("Bob", "bob@example.com")

        assert result["name"] == "Bob"
        assert len(fake_users.users) == 1

    async def it_sends_welcome_email(self, service, fake_email):
        """Sends welcome email on registration."""
        await service.register_user("Carol", "carol@example.com")

        assert fake_email.was_welcome_email_sent_to("carol@example.com")
```

### Explanation

1. **asyncio_mode = "auto"**: Automatically handles async tests
2. **Async fixtures**: Use `async def` for fixtures that need await
3. **Mixed sync/async**: Sync fixtures work with async tests
4. **Class methods**: Async methods in test classes work too

---

## Recipe: Error Injection

### Problem

You want to test error handling when adapters fail.

### Solution

Create fakes with configurable error behavior.

### Code

```python
"""Fakes with configurable error injection."""
from typing import Protocol

from dioxide import Profile, adapter


class PaymentPort(Protocol):
    async def charge(self, amount: float) -> dict: ...


class PaymentError(Exception):
    """Payment processing error."""
    pass


@adapter.for_(PaymentPort, profile=Profile.TEST)
class FakePaymentAdapter:
    """Fake payment with error injection."""

    def __init__(self):
        self.charges: list[dict] = []
        self.should_fail = False
        self.failure_reason = "Card declined"

    async def charge(self, amount: float) -> dict:
        if self.should_fail:
            raise PaymentError(self.failure_reason)

        charge = {"id": f"ch_{len(self.charges) + 1}", "amount": amount}
        self.charges.append(charge)
        return charge

    # Test helpers
    def fail_next(self, reason: str = "Card declined") -> None:
        """Make next charge fail."""
        self.should_fail = True
        self.failure_reason = reason

    def reset(self) -> None:
        """Reset to success mode."""
        self.should_fail = False
        self.charges.clear()


# Test error handling
import pytest


@pytest.fixture
def fake_payment(container) -> FakePaymentAdapter:
    adapter = container.resolve(PaymentPort)
    yield adapter
    adapter.reset()  # Clean up after test


class DescribeCheckoutService:
    """Tests for CheckoutService error handling."""

    async def it_raises_on_payment_failure(self, container, fake_payment):
        """Propagates payment errors."""
        fake_payment.fail_next("Insufficient funds")
        service = container.resolve(CheckoutService)

        with pytest.raises(PaymentError) as exc_info:
            await service.checkout(amount=100.0)

        assert "Insufficient funds" in str(exc_info.value)
        assert len(fake_payment.charges) == 0

    async def it_retries_on_transient_failure(self, container, fake_payment):
        """Retries once on network error."""
        # First call fails, second succeeds
        call_count = 0
        original_charge = fake_payment.charge

        async def charge_with_retry(amount: float) -> dict:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise PaymentError("Network timeout")
            return await original_charge(amount)

        fake_payment.charge = charge_with_retry
        service = container.resolve(CheckoutService)

        result = await service.checkout(amount=50.0)

        assert result is not None
        assert call_count == 2
```

### Explanation

1. **Configurable failure**: `should_fail` flag controls behavior
2. **Failure reason**: Customizable error message for different scenarios
3. **Reset after test**: Fixture cleanup prevents state leakage
4. **Test isolation**: Each test controls its own failure conditions

---

## Recipe: Controllable Time

### Problem

You need to test time-dependent logic (throttling, expiration, etc.) deterministically.

### Solution

Create a fake clock that you can control in tests.

### Code

```python
"""Fake clock for time-dependent tests."""
from datetime import datetime, timedelta, UTC
from typing import Protocol

from dioxide import Profile, adapter


class Clock(Protocol):
    def now(self) -> datetime: ...


@adapter.for_(Clock, profile=Profile.PRODUCTION)
class SystemClock:
    """Real system clock for production."""

    def now(self) -> datetime:
        return datetime.now(UTC)


@adapter.for_(Clock, profile=Profile.TEST)
class FakeClock:
    """Controllable fake clock for testing."""

    def __init__(self):
        self._now = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)

    def now(self) -> datetime:
        return self._now

    # Test control methods
    def set_time(self, dt: datetime) -> None:
        """Set current time."""
        self._now = dt

    def advance(self, **kwargs) -> None:
        """Advance time by timedelta kwargs (days, hours, minutes, etc.)."""
        self._now += timedelta(**kwargs)

    def rewind(self, **kwargs) -> None:
        """Rewind time by timedelta kwargs."""
        self._now -= timedelta(**kwargs)


# Test time-dependent logic
import pytest


@pytest.fixture
def fake_clock(container) -> FakeClock:
    return container.resolve(Clock)


class DescribeThrottling:
    """Tests for rate limiting logic."""

    async def it_allows_first_request(self, container, fake_clock):
        """First request within window succeeds."""
        fake_clock.set_time(datetime(2024, 1, 1, tzinfo=UTC))
        service = container.resolve(RateLimitedService)

        result = await service.send_notification(user_id=1)

        assert result is True

    async def it_blocks_request_within_cooldown(self, container, fake_clock):
        """Request within 1-hour cooldown is blocked."""
        fake_clock.set_time(datetime(2024, 1, 1, 12, 0, tzinfo=UTC))
        service = container.resolve(RateLimitedService)

        await service.send_notification(user_id=1)

        # Only 30 minutes later
        fake_clock.advance(minutes=30)

        result = await service.send_notification(user_id=1)
        assert result is False

    async def it_allows_request_after_cooldown(self, container, fake_clock):
        """Request after cooldown period succeeds."""
        fake_clock.set_time(datetime(2024, 1, 1, 12, 0, tzinfo=UTC))
        service = container.resolve(RateLimitedService)

        await service.send_notification(user_id=1)

        # 2 hours later (past 1-hour cooldown)
        fake_clock.advance(hours=2)

        result = await service.send_notification(user_id=1)
        assert result is True
```

### Explanation

1. **Inject Clock as port**: Services depend on `Clock` protocol, not `datetime.now()`
2. **FakeClock is controllable**: `set_time()` and `advance()` for precise control
3. **Deterministic tests**: Same time values every run, no flaky failures
4. **Natural test flow**: Test reads like a story with time progression

---

## Recipe: Seeding Test Data

### Problem

You want to set up test data in fake repositories before running tests.

### Solution

Add `seed()` methods to fake adapters for convenient test setup.

### Code

```python
"""Test data seeding patterns."""
from typing import Protocol

from dioxide import Profile, adapter


class UserRepository(Protocol):
    async def find(self, user_id: int) -> dict | None: ...
    async def save(self, user: dict) -> dict: ...


@adapter.for_(UserRepository, profile=Profile.TEST)
class FakeUserRepository:
    """Fake repository with seeding helpers."""

    def __init__(self):
        self.users: dict[int, dict] = {}
        self._next_id = 1

    async def find(self, user_id: int) -> dict | None:
        return self.users.get(user_id)

    async def save(self, user: dict) -> dict:
        if "id" not in user:
            user["id"] = self._next_id
            self._next_id += 1
        self.users[user["id"]] = user
        return user

    # Test helpers
    def seed(self, *users: dict) -> None:
        """Seed multiple users at once."""
        for user in users:
            if "id" not in user:
                user["id"] = self._next_id
                self._next_id += 1
            self.users[user["id"]] = user

    def clear(self) -> None:
        """Clear all users."""
        self.users.clear()
        self._next_id = 1


# Convenient fixtures for common test scenarios
import pytest


@pytest.fixture
def fake_users(container) -> FakeUserRepository:
    repo = container.resolve(UserRepository)
    yield repo
    repo.clear()


@pytest.fixture
def alice(fake_users) -> dict:
    """Standard test user: Alice."""
    user = {"id": 1, "name": "Alice", "email": "alice@example.com"}
    fake_users.seed(user)
    return user


@pytest.fixture
def bob(fake_users) -> dict:
    """Standard test user: Bob."""
    user = {"id": 2, "name": "Bob", "email": "bob@example.com"}
    fake_users.seed(user)
    return user


@pytest.fixture
def many_users(fake_users) -> list[dict]:
    """10 test users for pagination tests."""
    users = [
        {"name": f"User{i}", "email": f"user{i}@example.com"}
        for i in range(1, 11)
    ]
    fake_users.seed(*users)
    return list(fake_users.users.values())


# Usage
async def test_find_user(container, alice):
    """Find seeded user."""
    service = container.resolve(UserService)

    result = await service.get_user(alice["id"])

    assert result["name"] == "Alice"


async def test_pagination(container, many_users):
    """Test with multiple users."""
    service = container.resolve(UserService)

    page = await service.list_users(limit=5, offset=0)

    assert len(page) == 5
```

### Explanation

1. **seed() method**: Convenient way to add multiple entities at once
2. **Auto-ID generation**: Fake handles ID assignment like real database
3. **Fixture composition**: Build complex test data from simple fixtures
4. **Named fixtures**: `alice`, `bob` are more readable than inline dicts

---

## Recipe: Parametrized Tests

### Problem

You want to test multiple scenarios without duplicating test code.

### Solution

Use pytest's parametrize decorator with clear test case names.

### Code

```python
"""Parametrized tests for multiple scenarios."""
import pytest
from datetime import datetime, UTC


@pytest.mark.parametrize(
    "days_since_last_sent,expected_result",
    [
        pytest.param(None, True, id="never-sent-before"),
        pytest.param(0, False, id="sent-today"),
        pytest.param(7, False, id="sent-last-week"),
        pytest.param(29, False, id="sent-29-days-ago"),
        pytest.param(30, True, id="sent-exactly-30-days-ago"),
        pytest.param(60, True, id="sent-60-days-ago"),
    ],
)
async def test_email_throttling(
    container,
    fake_users,
    fake_clock,
    days_since_last_sent,
    expected_result,
):
    """Email throttling respects 30-day cooldown."""
    # Set up user with last_sent timestamp
    now = datetime(2024, 6, 1, tzinfo=UTC)
    fake_clock.set_time(now)

    if days_since_last_sent is not None:
        last_sent = now - timedelta(days=days_since_last_sent)
    else:
        last_sent = None

    fake_users.seed({
        "id": 1,
        "email": "alice@example.com",
        "last_email_sent": last_sent,
    })

    service = container.resolve(NotificationService)

    result = await service.send_welcome(user_id=1)

    assert result == expected_result


@pytest.mark.parametrize(
    "input_email,is_valid",
    [
        pytest.param("user@example.com", True, id="valid-email"),
        pytest.param("user@sub.example.com", True, id="valid-subdomain"),
        pytest.param("user.name@example.com", True, id="valid-dot-local"),
        pytest.param("invalid", False, id="no-at-sign"),
        pytest.param("@example.com", False, id="no-local-part"),
        pytest.param("user@", False, id="no-domain"),
        pytest.param("", False, id="empty-string"),
    ],
)
def test_email_validation(input_email, is_valid):
    """Email validation catches invalid formats."""
    from app.domain.validators import is_valid_email

    assert is_valid_email(input_email) == is_valid
```

### Explanation

1. **pytest.param with id**: Named test cases for clear output
2. **Descriptive IDs**: `sent-29-days-ago` vs anonymous parameters
3. **Table-driven**: Easy to add new cases
4. **Single assertion**: Each parametrized run tests one thing

---

## See Also

- [TESTING_GUIDE.md](../TESTING_GUIDE.md) - Comprehensive testing philosophy
- [FastAPI Integration](fastapi.md) - Testing FastAPI endpoints
- [Database Patterns](database.md) - Repository fakes
