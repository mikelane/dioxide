# Migration from Mocks to Fakes

**Version:** 1.0.0
**Last Updated:** 2025-01-01
**Status:** Practical migration guide for experienced developers

---

## Table of Contents

1. [Introduction](#introduction)
2. [The Problem with Mocks](#the-problem-with-mocks)
3. [Key Differences](#key-differences)
4. [What Tests Know vs What Tests Observe](#what-tests-know-vs-what-tests-observe)
5. [Step-by-Step Migration](#step-by-step-migration)
6. [Common Migration Patterns](#common-migration-patterns)
7. [When to Still Use Mocks](#when-to-still-use-mocks)
8. [FAQ](#faq)
9. [See Also](#see-also)

---

## Introduction

### The Pain You Know Too Well

If you've been writing Python tests for any length of time, you've probably experienced at least one of these moments:

**"Tests pass, production breaks."** You deployed with confidence - your test suite was green. Then came the 2 AM page. The real payment API returns a `Response` object, not the `True` your mock was configured to return. Your tests verified that your mocks work, not that your code works.

**"I touched one file and 47 tests broke."** You moved `send_email` from `myapp.services.email` to `myapp.notifications.email`. A simple refactor. But every test with `@patch('myapp.services.email.send_email')` turned red. You spent the afternoon updating patch paths instead of writing features.

**"I spent an hour debugging my mock setup, not my code."** The test kept failing with "expected call not made." Was it the argument matcher? The call order? The return value chain? Eventually you discovered you forgot `.return_value` in `mock_db.session.query.return_value.filter.return_value.first.return_value`. The mock configuration became harder to understand than the code being tested.

**"New team members can't understand our tests."** They stare at the tower of `@patch` decorators, the intricate `side_effect` lambdas, the nested `Mock()` configurations. They know what the test does, but not what it's actually testing. The tests have become a maintenance burden, not living documentation.

**"This test is flaky. Again."** It passes locally, fails in CI. Passes on retry. Something about timing or order or state leakage between tests. But the mock setup is so complex that nobody wants to debug it. So you add a retry decorator and move on.

### The Root Cause

Here's the uncomfortable truth: **when you use mocks, you're testing that your mock configuration is correct, not that your code behaves correctly.**

Every `assert_called_once_with()` verifies that you called a method on a mock object. It says nothing about whether the real implementation would have worked. Every `.return_value` trains the mock to behave like you *think* the real thing behaves - but if your assumption is wrong, your test passes and production fails.

Mocks create tests that are tightly coupled to *how* code works internally, rather than *what* it accomplishes. This is why refactoring breaks tests - you changed how without changing what, but your tests only know about how.

### This Guide Is For You If

You're an experienced Python developer who:
- Uses `@patch`, `Mock()`, or `MagicMock` regularly in tests
- Has experienced the pain points above firsthand
- Wants tests that verify behavior, not mock configuration
- Is ready to invest in tests that survive refactoring
- Is adopting dioxide for dependency injection

### The Core Shift

Instead of patching internal calls with mocks, you'll:
1. Define **ports** (Protocol interfaces) at architectural boundaries
2. Create **fakes** (simple, real implementations) for testing
3. Use dioxide's **profile system** to swap production adapters for fakes

**Result**: Tests that verify real behavior, survive refactoring, and are easier to understand.

The investment is real - you'll create ports and fakes upfront. But the payoff is tests that tell you when your code is broken, not when your mocks are misconfigured.

---

## The Problem with Mocks

### Before: Mock-Based Testing

Here's a typical test using `@patch`:

```python
# test_user_service.py
from unittest.mock import Mock, patch

@patch('myapp.services.email.send_email')
@patch('myapp.services.db.save_user')
def test_user_registration(mock_save, mock_email):
    # Configure mocks
    mock_save.return_value = {"id": "123", "email": "alice@example.com"}
    mock_email.return_value = True

    # Call the code
    service = UserService()
    result = service.register("Alice", "alice@example.com")

    # Verify mock interactions
    mock_save.assert_called_once_with("Alice", "alice@example.com")
    mock_email.assert_called_once()
    assert result["id"] == "123"
```

### Problems with This Approach

**1. Tests Implementation, Not Behavior**

The test verifies that specific methods were called with specific arguments. It doesn't verify that the user was actually registered correctly.

**2. Patch Path Fragility**

If you refactor and move `send_email` to a different module:

```python
# Refactor: move from myapp.services.email to myapp.notifications.email
@patch('myapp.notifications.email.send_email')  # Must update every test!
```

Every test with the old patch path breaks, even though behavior hasn't changed.

**3. Mock Configuration Complexity**

```python
# This mock setup is harder to understand than the code being tested
mock_db = Mock()
mock_db.users.create.return_value = Mock(id="123")
mock_db.users.create.return_value.to_dict.return_value = {"id": "123", "email": "..."}
mock_db.session.commit.side_effect = [
    None,  # First call succeeds
    IntegrityError(),  # Second call fails
    None,  # Retry succeeds
]
```

**4. Mocks Can Lie**

```python
# This test passes...
mock_email.send.return_value = True

# But real code fails because the actual API returns a Response object!
# response = api.send(...)  # Returns Response, not bool
# if response:  # Always truthy, even on error
```

**5. Tight Coupling to Internals**

Tests know too much about how the code works internally:
- Which methods are called
- In what order
- With what exact arguments
- How many times

Any internal refactoring breaks tests.

### After: Fakes with dioxide

```python
# test_user_service.py
from dioxide import Container, Profile

async def test_user_registration(container):
    # Arrange: Get real service with fake adapters (injected via profile)
    service = container.resolve(UserService)
    fake_email = container.resolve(EmailPort)

    # Act: Call REAL code
    result = await service.register("Alice", "alice@example.com")

    # Assert: Check OBSERVABLE outcomes
    assert result["email"] == "alice@example.com"
    assert len(fake_email.sent_emails) == 1
    assert fake_email.sent_emails[0]["to"] == "alice@example.com"
```

**What changed:**
- No patch decorators or path strings
- Real service code runs
- Assertions check outcomes, not method calls
- Refactoring internals won't break the test

---

## Key Differences

| Aspect | Mocks | Fakes |
|--------|-------|-------|
| **What you test** | Mock configuration | Real behavior |
| **Coupling** | Tight (knows method names, call order) | Loose (only observable outcomes) |
| **Refactoring** | Breaks tests | Tests survive |
| **Reusability** | One-off per test | Shared across tests |
| **Speed** | Fast | Fast (both in-memory) |
| **Confidence** | Tests that mocks work | Tests that code works |
| **Failure messages** | "Expected call not made" | "Email not in sent_emails" |
| **Maintenance** | Update patches when code moves | Update fakes when interface changes |

### Mental Model Shift

**With Mocks**: "Did the code call the right methods?"

**With Fakes**: "Did the code produce the right outcomes?"

---

## What Tests Know vs What Tests Observe

This distinction is the key to understanding why fakes lead to better tests than mocks.

### The Knowledge Problem

When a test "knows" something, it's coupled to that implementation detail. When implementation changes, the test breaks - even if behavior is preserved.

| Aspect | Mock-Based Test | Fake-Based Test |
|--------|-----------------|-----------------|
| **Knows** | Which methods are called, in what order, with what arguments | Only the public interface (ports) |
| **Observes** | That mocks were invoked correctly | That observable outcomes occurred |
| **Breaks when** | Any internal refactoring changes method calls | Actual behavior changes |
| **Confidence** | "My mock configuration matches my assumptions" | "My code produces correct results" |

### Testing HOW vs Testing WHAT

Here's the same behavior tested both ways:

**Mock-based test (testing HOW):**

```python
@patch('myapp.services.email.send_email')
@patch('myapp.services.db.save_user')
def test_user_registration(mock_save, mock_email):
    mock_save.return_value = {"id": "123", "email": "alice@example.com"}

    service = UserService()
    service.register("Alice", "alice@example.com")

    # Test KNOWS: save_user is called before send_email
    # Test KNOWS: exact argument format passed to save_user
    # Test KNOWS: send_email exists at myapp.services.email
    mock_save.assert_called_once_with("Alice", "alice@example.com")
    mock_email.assert_called_once()
```

This test knows:
- The exact module path where `send_email` lives
- That `save_user` is called with positional arguments in a specific order
- The internal call sequence of the service

**Fake-based test (testing WHAT):**

```python
async def test_user_registration(container):
    service = container.resolve(UserService)
    fake_email = container.resolve(EmailPort)
    fake_users = container.resolve(UserRepository)

    await service.register("Alice", "alice@example.com")

    # Test OBSERVES: a user exists with the right data
    # Test OBSERVES: an email was sent to the right address
    assert "alice@example.com" in [u["email"] for u in fake_users.users.values()]
    assert any(e["to"] == "alice@example.com" for e in fake_email.sent_emails)
```

This test observes:
- A user with the correct email exists in storage
- An email was sent to the correct address

It does not know (or care about):
- Where the email module lives in the codebase
- Whether `save_user` takes positional or keyword arguments
- What order the internal operations happen in

### Why This Matters for Refactoring

Imagine you refactor `UserService` to batch email sending for performance:

```python
# Before: sends email immediately
async def register(self, name: str, email: str) -> dict:
    user = await self.users.save(name, email)
    await self.email.send(to=email, subject="Welcome!", body=f"Hello {name}")
    return user

# After: queues email for batch sending
async def register(self, name: str, email: str) -> dict:
    user = await self.users.save(name, email)
    await self.email_queue.enqueue(to=email, subject="Welcome!", body=f"Hello {name}")
    return user
```

**Mock-based test result:** FAILS. The mock was configured for `send_email`, but now `enqueue` is called. You must update the test.

**Fake-based test result:** If your `FakeEmailQueue` adds to the same `sent_emails` list (or you check the queue), the test still passes. The observable outcome (email scheduled to be sent) is the same.

The fake-based test survives the refactor because it tests *what* the code accomplishes, not *how* it accomplishes it.

---

## Step-by-Step Migration

### Step 1: Identify Boundaries

Look at your `@patch` decorators. Each patch point is a boundary:

```python
@patch('myapp.services.email.send_email')
@patch('myapp.services.db.save_user')
@patch('myapp.clients.stripe.charge_card')
def test_checkout(mock_stripe, mock_db, mock_email):
    ...
```

These patches reveal three boundaries:
- Email sending
- User persistence
- Payment processing

### Step 2: Create Ports (Interfaces)

For each boundary, define a Protocol:

```python
# ports.py
from typing import Protocol

class EmailPort(Protocol):
    async def send(self, to: str, subject: str, body: str) -> None:
        """Send an email to the specified address."""
        ...

class UserRepository(Protocol):
    async def save(self, name: str, email: str) -> dict:
        """Save a user and return the user data."""
        ...

class PaymentGateway(Protocol):
    async def charge(self, amount: float, card_token: str) -> dict:
        """Charge the card and return the transaction result."""
        ...
```

### Step 3: Create Fakes

For each port, create a simple fake implementation:

```python
# adapters/fakes.py
from dioxide import adapter, Profile

@adapter.for_(EmailPort, profile=Profile.TEST)
class FakeEmailAdapter:
    """In-memory email for testing."""

    def __init__(self):
        self.sent_emails = []

    async def send(self, to: str, subject: str, body: str) -> None:
        self.sent_emails.append({
            "to": to,
            "subject": subject,
            "body": body,
        })

    # Test-only helper (not in Protocol)
    def clear(self) -> None:
        self.sent_emails = []


@adapter.for_(UserRepository, profile=Profile.TEST)
class FakeUserRepository:
    """In-memory user storage for testing."""

    def __init__(self):
        self.users = {}
        self._next_id = 1

    async def save(self, name: str, email: str) -> dict:
        user = {
            "id": str(self._next_id),
            "name": name,
            "email": email,
        }
        self.users[user["id"]] = user
        self._next_id += 1
        return user

    # Test-only helper
    def seed(self, *users: dict) -> None:
        for user in users:
            self.users[user["id"]] = user


@adapter.for_(PaymentGateway, profile=Profile.TEST)
class FakePaymentGateway:
    """Fake payment gateway for testing."""

    def __init__(self):
        self.charges = []
        self.should_fail = False
        self.failure_reason = "Card declined"

    async def charge(self, amount: float, card_token: str) -> dict:
        if self.should_fail:
            raise PaymentError(self.failure_reason)

        charge = {
            "id": f"ch_{len(self.charges) + 1}",
            "amount": amount,
            "status": "succeeded",
        }
        self.charges.append(charge)
        return charge

    # Test-only helpers
    def fail_next_charge(self, reason: str = "Card declined") -> None:
        self.should_fail = True
        self.failure_reason = reason

    def reset(self) -> None:
        self.charges = []
        self.should_fail = False
```

### Step 4: Update Your Service

Make your service depend on ports via constructor injection:

```python
# Before: Direct imports (hard to test)
from myapp.services.email import send_email
from myapp.services.db import save_user

class UserService:
    def register(self, name: str, email: str) -> dict:
        user = save_user(name, email)
        send_email(email, "Welcome!", f"Hello {name}")
        return user
```

```python
# After: Constructor injection with ports
from dioxide import service

@service
class UserService:
    def __init__(
        self,
        users: UserRepository,
        email: EmailPort,
    ):
        self.users = users
        self.email = email

    async def register(self, name: str, email: str) -> dict:
        user = await self.users.save(name, email)
        await self.email.send(
            to=email,
            subject="Welcome!",
            body=f"Hello {name}",
        )
        return user
```

### Step 5: Update Tests

Replace mock-based tests with fake-based tests:

```python
# Before: Mock-based
@patch('myapp.services.email.send_email')
@patch('myapp.services.db.save_user')
def test_user_registration(mock_save, mock_email):
    mock_save.return_value = {"id": "123", "email": "alice@example.com"}
    mock_email.return_value = True

    service = UserService()
    result = service.register("Alice", "alice@example.com")

    mock_save.assert_called_once_with("Alice", "alice@example.com")
    mock_email.assert_called_once()
    assert result["id"] == "123"
```

```python
# After: Fake-based
import pytest
from dioxide import Container, Profile

@pytest.fixture
def container():
    c = Container()
    c.scan(profile=Profile.TEST)
    return c

async def test_user_registration(container):
    # Arrange
    service = container.resolve(UserService)
    fake_email = container.resolve(EmailPort)

    # Act
    result = await service.register("Alice", "alice@example.com")

    # Assert: Check observable outcomes
    assert result["email"] == "alice@example.com"
    assert len(fake_email.sent_emails) == 1
    assert fake_email.sent_emails[0]["to"] == "alice@example.com"
    assert fake_email.sent_emails[0]["subject"] == "Welcome!"
```

---

## Common Migration Patterns

### Pattern: Database Operations

**Before (Mock):**

```python
@patch('myapp.db.session')
def test_creates_order(mock_session):
    mock_session.add = Mock()
    mock_session.commit = Mock()
    mock_session.query.return_value.filter.return_value.first.return_value = None

    service = OrderService()
    order = service.create_order(user_id=1, items=[...])

    mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once()
```

**After (Fake):**

```python
# adapters/fakes.py
@adapter.for_(OrderRepository, profile=Profile.TEST)
class FakeOrderRepository:
    def __init__(self):
        self.orders = {}

    async def create(self, user_id: int, items: list) -> dict:
        order = {
            "id": len(self.orders) + 1,
            "user_id": user_id,
            "items": items,
            "status": "pending",
        }
        self.orders[order["id"]] = order
        return order

    async def find_by_id(self, order_id: int) -> dict | None:
        return self.orders.get(order_id)

# test_order_service.py
async def test_creates_order(container):
    service = container.resolve(OrderService)
    fake_orders = container.resolve(OrderRepository)

    order = await service.create_order(user_id=1, items=["item1", "item2"])

    # Check the order exists in the fake repository
    assert order["id"] in fake_orders.orders
    assert fake_orders.orders[order["id"]]["status"] == "pending"
```

### Pattern: External APIs

**Before (Mock):**

```python
@patch('requests.post')
def test_sends_notification(mock_post):
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {"success": True}

    service = NotificationService()
    result = service.send_push("user123", "Hello!")

    mock_post.assert_called_once()
    assert "user123" in str(mock_post.call_args)
```

**After (Fake):**

```python
# ports.py
class PushNotificationPort(Protocol):
    async def send(self, user_id: str, message: str) -> bool: ...

# adapters/fakes.py
@adapter.for_(PushNotificationPort, profile=Profile.TEST)
class FakePushNotification:
    def __init__(self):
        self.notifications = []
        self.should_fail = False

    async def send(self, user_id: str, message: str) -> bool:
        if self.should_fail:
            return False
        self.notifications.append({"user_id": user_id, "message": message})
        return True

# test_notification_service.py
async def test_sends_notification(container):
    service = container.resolve(NotificationService)
    fake_push = container.resolve(PushNotificationPort)

    result = await service.send_push("user123", "Hello!")

    assert result is True
    assert len(fake_push.notifications) == 1
    assert fake_push.notifications[0]["user_id"] == "user123"
    assert fake_push.notifications[0]["message"] == "Hello!"
```

### Pattern: Time-Dependent Logic

**Before (Mock):**

```python
from unittest.mock import patch
from datetime import datetime

@patch('myapp.services.datetime')
def test_subscription_expired(mock_datetime):
    mock_datetime.now.return_value = datetime(2024, 6, 1)
    mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)

    service = SubscriptionService()
    user = {"subscription_end": datetime(2024, 5, 15)}

    assert service.is_expired(user) is True
```

**After (Fake):**

```python
# ports.py
class Clock(Protocol):
    def now(self) -> datetime: ...

# adapters/fakes.py
from datetime import datetime, timedelta, UTC

@adapter.for_(Clock, profile=Profile.TEST)
class FakeClock:
    def __init__(self):
        self._now = datetime(2024, 1, 1, tzinfo=UTC)

    def now(self) -> datetime:
        return self._now

    # Test-only control methods
    def set_time(self, dt: datetime) -> None:
        self._now = dt

    def advance(self, **kwargs) -> None:
        self._now += timedelta(**kwargs)

# test_subscription_service.py
async def test_subscription_expired(container):
    fake_clock = container.resolve(Clock)
    service = container.resolve(SubscriptionService)

    # Set up: subscription ended May 15
    fake_clock.set_time(datetime(2024, 6, 1, tzinfo=UTC))
    user = {"subscription_end": datetime(2024, 5, 15, tzinfo=UTC)}

    assert await service.is_expired(user) is True

async def test_subscription_active(container):
    fake_clock = container.resolve(Clock)
    service = container.resolve(SubscriptionService)

    # Set up: subscription ends June 30
    fake_clock.set_time(datetime(2024, 6, 1, tzinfo=UTC))
    user = {"subscription_end": datetime(2024, 6, 30, tzinfo=UTC)}

    assert await service.is_expired(user) is False
```

### Pattern: Error Handling

**Before (Mock):**

```python
@patch('myapp.clients.payment.charge')
def test_handles_payment_failure(mock_charge):
    mock_charge.side_effect = PaymentError("Card declined")

    service = CheckoutService()

    with pytest.raises(CheckoutError) as exc_info:
        service.checkout(cart_id=1, card_token="tok_123")

    assert "payment failed" in str(exc_info.value).lower()
```

**After (Fake):**

```python
async def test_handles_payment_failure(container):
    fake_gateway = container.resolve(PaymentGateway)
    service = container.resolve(CheckoutService)

    # Configure fake to fail
    fake_gateway.fail_next_charge(reason="Card declined")

    with pytest.raises(CheckoutError) as exc_info:
        await service.checkout(cart_id=1, card_token="tok_123")

    assert "payment failed" in str(exc_info.value).lower()
```

---

## When to Still Use Mocks

Fakes are usually better, but mocks still have their place:

### 1. Third-Party Libraries Without Ports

When you're testing interaction with a library you don't control and can't easily wrap:

```python
# Acceptable: Mocking a third-party library directly
@patch('boto3.client')
def test_uploads_to_s3(mock_client):
    mock_s3 = Mock()
    mock_client.return_value = mock_s3

    uploader = S3Uploader()
    uploader.upload("bucket", "key", b"data")

    mock_s3.put_object.assert_called_once()
```

**Better alternative**: Create a port and fake for file storage, then use the real S3 client in a production adapter.

### 2. Verifying Specific Call Counts (Rare)

When the number of calls is the behavior being tested:

```python
# Rare case: Testing rate limiting
async def test_rate_limiter_allows_three_calls(container):
    service = container.resolve(RateLimitedService)

    # These should succeed
    await service.call_api()
    await service.call_api()
    await service.call_api()

    # This should fail due to rate limit
    with pytest.raises(RateLimitError):
        await service.call_api()
```

With fakes, you'd check the fake's state. But if you genuinely need call counting, a mock might be simpler.

### 3. Legacy Code Migration (Temporary)

When migrating legacy code incrementally, you might use mocks temporarily:

```python
# Step 1: Mock while you figure out the interface
@patch('legacy.module.some_function')
def test_legacy_code(mock_fn):
    ...

# Step 2: Extract a port
# Step 3: Create a fake
# Step 4: Remove the mock
```

**Important**: This should be temporary. Convert to fakes as you refactor.

---

## FAQ

### "But I need to verify the method was called"

Check observable outcomes instead.

**Mock approach (what you're used to):**
```python
mock_email.send.assert_called_once_with("alice@example.com", "Welcome!")
```

**Fake approach (what to do instead):**
```python
assert len(fake_email.sent_emails) == 1
assert fake_email.sent_emails[0]["to"] == "alice@example.com"
assert fake_email.sent_emails[0]["subject"] == "Welcome!"
```

Both verify that an email was sent. The fake approach also lets you check the email content without brittle argument matching.

### "My tests will be slower"

No. Fakes are in-memory, just like mocks. There's no performance difference.

Both approaches avoid real I/O (databases, APIs, file systems). The execution time is nearly identical.

### "I have hundreds of mocked tests"

We hear you. The thought of rewriting hundreds of tests is overwhelming. Here's the good news: **you don't have to do it all at once, and you probably shouldn't.**

A wholesale rewrite is risky - you might introduce bugs, lose coverage, and demoralize your team. Instead, migrate incrementally using this prioritization:

**Priority 1: New code gets fakes from day one**

Every new feature, every new service, every new boundary - write it with ports and fakes. This stops the bleeding. Your mock debt stops growing.

**Priority 2: Touched code gets migrated**

When you modify a file with mocked tests, that's your opportunity. You're already in the code, already understanding the context. Convert the mocks to fakes as part of the change.

**Priority 3: Brittle tests get prioritized**

Keep a mental (or literal) list of tests that break frequently, are hard to understand, or that nobody wants to touch. These are your highest-ROI conversions. Every time one of these tests breaks, consider whether this is the moment to convert it.

**Priority 4: Leave working tests alone**

A mocked test that hasn't broken in two years and still accurately tests behavior? Leave it. Don't fix what isn't broken. You'll get to it eventually through Priority 2, or maybe you won't - and that's okay.

**Realistic timeline expectations:**

- **3 months**: New code uses fakes, team is comfortable with the pattern
- **6 months**: High-churn areas are mostly converted, brittle tests eliminated
- **12 months**: Most active code paths use fakes, mocks remain in stable legacy areas
- **Ongoing**: Opportunistic conversion as code gets touched

The goal isn't "zero mocks by Friday." The goal is a test suite that increasingly tells you when your code is broken, not when your mocks are misconfigured. Every fake you add moves you in that direction.

### "Creating fakes seems like more work"

Initially, yes. But fakes are reusable:

- Same fake works for all tests
- Same fake works for development environment
- Same fake works for demos and documentation
- Mocks are recreated for each test

Over time, fakes reduce total effort.

### "What if my fake has bugs?"

Keep fakes simple. A good fake is:
- Simpler than the real implementation
- An in-memory data structure (dict, list)
- Free of business logic

If your fake is complex enough to have bugs, it's too complex. Simplify it.

### "How do I test that a method was NOT called?"

Check that the observable outcome didn't happen:

```python
# Mock approach
mock_email.send.assert_not_called()

# Fake approach
assert len(fake_email.sent_emails) == 0
```

### "What about @patch.object?"

Same migration pattern. `@patch.object` is still patching, just with a different syntax:

```python
# Before
@patch.object(EmailService, 'send')
def test_foo(mock_send):
    ...

# After: Use ports and fakes instead
```

### "Can I mix mocks and fakes?"

Technically yes, but don't. Pick one approach per test suite for consistency.

Mixing creates confusion about which testing style to use where.

---

## See Also

- [Testing Guide](TESTING_GUIDE.md) - Complete testing philosophy and patterns
- [MLP Vision](MLP_VISION.md) - Design principles behind dioxide
- [Migration from dependency-injector](migration-from-dependency-injector.rst) - Migrating from another DI framework

---

## Summary

**The core shift:**

| From | To |
|------|-----|
| `@patch('module.function')` | Define a `Port` (Protocol) |
| `Mock()` with `return_value` | Create a simple `Fake` adapter |
| `mock.assert_called_once()` | Check `fake.state` |
| Patch paths in decorators | Profile-based injection |

**The benefits:**

- Tests verify behavior, not implementation
- Refactoring doesn't break tests
- Test failures are clearer ("email not sent" vs "expected call not made")
- Fakes are reusable across tests, dev, and demos

**Start small:**

1. Pick one heavily-mocked test file
2. Identify the boundaries (what's being patched)
3. Create ports and fakes for those boundaries
4. Migrate the tests
5. Repeat

---

**This guide represents the practical path from mock-based testing to dioxide's fakes-at-the-seams approach. The investment in creating ports and fakes pays off through clearer, more maintainable tests.**
