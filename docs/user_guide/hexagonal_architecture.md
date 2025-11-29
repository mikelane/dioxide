# Hexagonal Architecture with dioxide

## What is Hexagonal Architecture?

**Hexagonal Architecture** (also known as **Ports and Adapters**) is an architectural pattern that promotes loose coupling between business logic and external systems. The core idea is to define **ports** (interfaces) that represent the boundaries of your application, and implement **adapters** (concrete implementations) that connect to external systems like databases, email services, or payment gateways.

The architecture gets its name from its visual representation: the core business logic sits in the center (the hexagon), surrounded by ports (edges), with adapters (outside the hexagon) plugging into those ports.

**Key benefits:**

- **Testability**: Business logic can be tested without touching real databases or external APIs
- **Maintainability**: Changing implementations (e.g., swapping SendGrid for AWS SES) requires changing only adapters
- **Flexibility**: Multiple implementations of the same port enable different configurations for different environments
- **Clarity**: Explicit boundaries between business logic and infrastructure

## Why Hexagonal Architecture?

Traditional applications often suffer from tight coupling between business logic and infrastructure:

```python
# Traditional approach - tight coupling
class UserService:
    def register_user(self, email: str, name: str):
        # Business logic mixed with infrastructure
        user = {"email": email, "name": name}

        # Direct PostgreSQL coupling
        conn = psycopg2.connect("dbname=production_db")
        conn.execute("INSERT INTO users ...")

        # Direct SendGrid coupling
        sendgrid.send(to=email, subject="Welcome!")
```

**Problems:**

- Tests require mocking PostgreSQL and SendGrid
- Cannot test business logic without database setup
- Swapping database or email provider requires editing business logic
- Hard to use different implementations for dev/test/prod

**Hexagonal Architecture fixes this:**

```python
# Hexagonal approach - loose coupling
@service
class UserService:
    def __init__(self, db: UserRepository, email: EmailPort):
        self.db = db
        self.email = email

    def register_user(self, email_addr: str, name: str):
        # Pure business logic
        user = {"email": email_addr, "name": name}
        self.db.save(user)
        self.email.send(to=email_addr, subject="Welcome!")
```

**Benefits:**

- Tests use fast in-memory fakes (no mocking!)
- Business logic depends on interfaces, not implementations
- Swapping implementations requires no changes to business logic
- Different adapters for different environments (prod, test, dev)

## Core Concepts

### 1. Ports (Protocols)

**Ports** are interfaces that define the contract between your business logic and the outside world. In Python, we use `Protocol` classes from the `typing` module.

```python
from typing import Protocol

class EmailPort(Protocol):
    """Port for sending emails - defines the seam."""
    async def send(self, to: str, subject: str, body: str) -> None: ...

class UserRepository(Protocol):
    """Port for user data access."""
    async def save_user(self, user: dict) -> None: ...
    async def find_by_email(self, email: str) -> dict | None: ...
```

**Key characteristics:**

- **No decorator** - Ports are just Protocols, no `@adapter` or `@service`
- **Interface only** - No implementation, just method signatures
- **Type hints required** - Full type annotations for mypy validation
- **Documentation** - Docstrings explain the contract

**Why Protocol?** Python's `Protocol` provides structural subtyping (duck typing with type safety). Classes that implement the required methods automatically satisfy the protocol, no explicit inheritance needed.

### 2. Adapters (Implementations)

**Adapters** are concrete implementations of ports. They connect your business logic to real external systems (databases, APIs, file systems, etc.). dioxide uses the `@adapter.for_()` decorator to register adapters for specific ports and profiles.

```python
from dioxide import adapter, Profile

# Production adapter - real SendGrid
@adapter.for_(EmailPort, profile=Profile.PRODUCTION)
class SendGridAdapter:
    def __init__(self, config: AppConfig):
        self.api_key = config.sendgrid_api_key

    async def send(self, to: str, subject: str, body: str) -> None:
        # Real SendGrid API calls
        async with httpx.AsyncClient() as client:
            await client.post(
                "https://api.sendgrid.com/v3/mail/send",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={"to": to, "subject": subject, "body": body}
            )

# Test adapter - fast fake
@adapter.for_(EmailPort, profile=Profile.TEST)
class FakeEmailAdapter:
    def __init__(self):
        self.sent_emails = []

    async def send(self, to: str, subject: str, body: str) -> None:
        # No I/O, just capture in memory
        self.sent_emails.append({"to": to, "subject": subject, "body": body})

# Development adapter - console logging
@adapter.for_(EmailPort, profile=Profile.DEVELOPMENT)
class ConsoleEmailAdapter:
    async def send(self, to: str, subject: str, body: str) -> None:
        # Simple console output for debugging
        print(f"EMAIL TO: {to}\nSUBJECT: {subject}\nBODY: {body}\n")
```

**Key characteristics:**

- **`@adapter.for_(Port, profile=...)`** - Registers adapter for a specific port and profile
- **Implements port methods** - Must provide all methods from the Protocol
- **Profile-specific** - Different adapters for different environments
- **Singleton by default** - One instance per container (can be changed)
- **Dependencies injected** - Constructor parameters auto-injected by dioxide

### 3. Services (Business Logic)

**Services** contain your core business logic and domain rules. They depend on ports (interfaces), not concrete adapters. dioxide uses the `@service` decorator to register services.

```python
from dioxide import service

@service
class UserService:
    def __init__(self, db: UserRepository, email: EmailPort):
        # Depends on PORTS, not concrete adapters
        self.db = db
        self.email = email

    async def register_user(self, email_addr: str, name: str):
        # Pure business logic - no infrastructure details

        # Validation (business rule)
        if not email_addr or "@" not in email_addr:
            raise ValueError("Invalid email address")

        # Check if already exists (business rule)
        existing = await self.db.find_by_email(email_addr)
        if existing:
            raise ValueError("User already exists")

        # Create user
        user = {"email": email_addr, "name": name}
        await self.db.save_user(user)

        # Send welcome email
        await self.email.send(
            to=email_addr,
            subject="Welcome!",
            body=f"Hello {name}, welcome to our service!"
        )

        return user
```

**Key characteristics:**

- **`@service` decorator** - Registers as singleton service
- **Profile-agnostic** - Same service in all environments
- **Depends on ports** - Constructor takes Protocol types
- **Pure business logic** - No database, API, or file system code
- **Type-safe** - Full mypy validation of dependencies

### 4. Profiles (Environment Configuration)

**Profiles** determine which adapters are active for a given environment. dioxide provides a `Profile` enum with standard profiles, but you can also use custom string profiles.

```python
from dioxide import Profile

# Standard profiles
Profile.PRODUCTION   # 'production' - Real external systems
Profile.TEST         # 'test' - Fast fakes for testing
Profile.DEVELOPMENT  # 'development' - Local alternatives (SQLite, console output)
Profile.STAGING      # 'staging' - Production-like but isolated
Profile.CI           # 'ci' - Continuous integration environment
Profile.ALL          # '*' - Available in all profiles
```

**Activating a profile:**

```python
from dioxide import container, Profile

# Production environment
container.scan("app", profile=Profile.PRODUCTION)
# Activates all @adapter.for_(Port, profile=Profile.PRODUCTION) adapters

# Test environment
container.scan("app", profile=Profile.TEST)
# Activates all @adapter.for_(Port, profile=Profile.TEST) adapters
```

**Multiple profiles for one adapter:**

```python
# Adapter available in both TEST and DEVELOPMENT
@adapter.for_(EmailPort, profile=[Profile.TEST, Profile.DEVELOPMENT])
class SimpleEmailAdapter:
    async def send(self, to: str, subject: str, body: str) -> None:
        print(f"Simple email to {to}")
```

## Architecture Layers

dioxide makes hexagonal architecture explicit through distinct decorator roles:

```{mermaid}
flowchart TB
    subgraph services["@service (Core Domain Logic)"]
        direction LR
        US[UserService]
        OS[OrderService]
        NS[NotificationService]
    end

    subgraph ports["Ports (Protocols/ABCs)"]
        direction LR
        EP[EmailPort]
        UR[UserRepository]
        PG[PaymentGateway]
    end

    subgraph adapters["@adapter.for_(Port, profile=...)"]
        direction LR
        SG["SendGridAdapter<br/>(PRODUCTION)"]
        FE["FakeEmailAdapter<br/>(TEST)"]
        CE["ConsoleEmailAdapter<br/>(DEVELOPMENT)"]
    end

    services -->|"depends on<br/>(constructor injection)"| ports
    ports -->|"implemented by"| adapters
```

**Layer descriptions:**

| Layer | Description |
|-------|-------------|
| **@service** | Business rules, profile-agnostic, depends on ports |
| **Ports** | Interfaces only, no decorators, just type definitions |
| **@adapter** | Boundary implementations, profile-specific, swappable |

**Data flow:**

1. **Service** defines business logic, depends on **Ports**
2. **Ports** define interfaces, no implementation
3. **Adapters** implement Ports for specific **Profiles**
4. **Container** scans code, activates adapters matching active profile
5. **Container** injects adapters into services based on type hints

## Complete Example: Email System

Let's build a complete email notification system using hexagonal architecture.

### Step 1: Define the Port

First, define the interface (the seam):

```python
# ports.py
from typing import Protocol

class EmailPort(Protocol):
    """Port for sending emails.

    This interface defines the seam between business logic
    and email infrastructure. Different adapters can implement
    this for different email providers.
    """
    async def send(self, to: str, subject: str, body: str) -> None:
        """Send an email.

        Args:
            to: Recipient email address
            subject: Email subject line
            body: Email body (plain text)

        Raises:
            ValueError: If to address is invalid
        """
        ...
```

### Step 2: Create Adapters for Different Profiles

Now implement adapters for different environments:

```python
# adapters/email.py
from dioxide import adapter, Profile
from ..ports import EmailPort
import httpx

# Production adapter - real SendGrid
@adapter.for_(EmailPort, profile=Profile.PRODUCTION)
class SendGridAdapter:
    """Production email adapter using SendGrid API."""

    def __init__(self, config: AppConfig):
        self.api_key = config.sendgrid_api_key
        if not self.api_key:
            raise ValueError("SendGrid API key not configured")

    async def send(self, to: str, subject: str, body: str) -> None:
        """Send email via SendGrid API."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.sendgrid.com/v3/mail/send",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "personalizations": [{"to": [{"email": to}]}],
                    "from": {"email": "noreply@myapp.com"},
                    "subject": subject,
                    "content": [{"type": "text/plain", "value": body}]
                }
            )
            response.raise_for_status()

# Test adapter - fast fake
@adapter.for_(EmailPort, profile=Profile.TEST)
class FakeEmailAdapter:
    """Test email adapter that captures emails in memory."""

    def __init__(self):
        self.sent_emails: list[dict] = []
        self.should_fail = False

    async def send(self, to: str, subject: str, body: str) -> None:
        """Capture email in memory instead of sending."""
        if self.should_fail:
            raise RuntimeError("Fake email failure for testing")

        self.sent_emails.append({
            "to": to,
            "subject": subject,
            "body": body
        })

    def clear(self) -> None:
        """Clear sent emails (useful between tests)."""
        self.sent_emails.clear()

# Development adapter - console logging
@adapter.for_(EmailPort, profile=Profile.DEVELOPMENT)
class ConsoleEmailAdapter:
    """Development email adapter that prints to console."""

    async def send(self, to: str, subject: str, body: str) -> None:
        """Print email to console for debugging."""
        print("=" * 60)
        print(f"EMAIL TO: {to}")
        print(f"SUBJECT: {subject}")
        print(f"BODY:\n{body}")
        print("=" * 60)
```

### Step 3: Create a Service

Now create a service that uses the port:

```python
# services/notification.py
from dioxide import service
from ..ports import EmailPort

@service
class NotificationService:
    """Service for sending notifications to users."""

    def __init__(self, email: EmailPort):
        # Depends on EmailPort interface, not concrete adapter
        self.email = email

    async def send_welcome_email(self, user_email: str, user_name: str) -> None:
        """Send welcome email to new user.

        Args:
            user_email: User's email address
            user_name: User's name

        Raises:
            ValueError: If email address is invalid
        """
        # Validate (business rule)
        if not user_email or "@" not in user_email:
            raise ValueError("Invalid email address")

        # Send email (through port, adapter handles details)
        await self.email.send(
            to=user_email,
            subject="Welcome to Our Service!",
            body=f"Hello {user_name},\n\nWelcome to our amazing service!"
        )

    async def send_password_reset(self, user_email: str, reset_token: str) -> None:
        """Send password reset email.

        Args:
            user_email: User's email address
            reset_token: Reset token for password reset link
        """
        reset_url = f"https://myapp.com/reset?token={reset_token}"

        await self.email.send(
            to=user_email,
            subject="Password Reset Request",
            body=f"Click here to reset your password:\n\n{reset_url}"
        )
```

### Step 4: Use in Production

```python
# main.py
from dioxide import container, Profile

async def main():
    # Scan for components with production profile
    container.scan("app", profile=Profile.PRODUCTION)

    # Resolve service (EmailPort auto-injected with SendGridAdapter)
    notification_service = container.resolve(NotificationService)

    # Use service
    await notification_service.send_welcome_email(
        user_email="alice@example.com",
        user_name="Alice"
    )
    # Email sent via SendGrid!
```

### Step 5: Test with Fakes

```python
# tests/test_notification.py
import pytest
from dioxide import container, Profile
from app.services.notification import NotificationService
from app.ports import EmailPort

@pytest.fixture
def test_container():
    """Create test container with TEST profile."""
    container.scan("app", profile=Profile.TEST)
    return container

@pytest.fixture
def notification_service(test_container):
    """Get notification service with fakes injected."""
    return test_container.resolve(NotificationService)

@pytest.fixture
def fake_email(test_container):
    """Get fake email adapter for assertions."""
    return test_container.resolve(EmailPort)

async def test_sends_welcome_email(notification_service, fake_email):
    """Sends welcome email with correct content."""
    # Act
    await notification_service.send_welcome_email(
        user_email="alice@example.com",
        user_name="Alice"
    )

    # Assert - check fake's captured emails
    assert len(fake_email.sent_emails) == 1
    email = fake_email.sent_emails[0]
    assert email["to"] == "alice@example.com"
    assert email["subject"] == "Welcome to Our Service!"
    assert "Alice" in email["body"]

async def test_rejects_invalid_email(notification_service, fake_email):
    """Rejects invalid email address."""
    # Act & Assert
    with pytest.raises(ValueError, match="Invalid email address"):
        await notification_service.send_welcome_email(
            user_email="not-an-email",
            user_name="Bob"
        )

    # No emails sent
    assert len(fake_email.sent_emails) == 0
```

**Key points:**

- Tests run fast (no actual SendGrid API calls)
- No mocking frameworks needed
- Tests verify real business logic
- Can test error cases easily by inspecting fake's state

## Real-World Example: Payment System

Here's a more complex example with multiple ports and adapters:

### Ports

```python
# ports.py
from typing import Protocol
from decimal import Decimal

class PaymentGateway(Protocol):
    """Port for processing payments."""
    async def charge(self, amount: Decimal, currency: str, card_token: str) -> str:
        """Charge a payment method.

        Returns:
            Transaction ID from payment gateway
        """
        ...

    async def refund(self, transaction_id: str, amount: Decimal) -> None:
        """Refund a transaction."""
        ...

class OrderRepository(Protocol):
    """Port for order data access."""
    async def save_order(self, order: dict) -> None: ...
    async def find_by_id(self, order_id: str) -> dict | None: ...
    async def update_status(self, order_id: str, status: str) -> None: ...
```

### Adapters

```python
# adapters/payment.py
from dioxide import adapter, Profile
from decimal import Decimal

# Production - real Stripe
@adapter.for_(PaymentGateway, profile=Profile.PRODUCTION)
class StripeAdapter:
    def __init__(self, config: AppConfig):
        self.api_key = config.stripe_api_key

    async def charge(self, amount: Decimal, currency: str, card_token: str) -> str:
        # Real Stripe API call
        import stripe
        stripe.api_key = self.api_key

        charge = stripe.Charge.create(
            amount=int(amount * 100),  # Stripe uses cents
            currency=currency,
            source=card_token
        )
        return charge.id

    async def refund(self, transaction_id: str, amount: Decimal) -> None:
        import stripe
        stripe.api_key = self.api_key
        stripe.Refund.create(charge=transaction_id)

# Test - fake with controllable behavior
@adapter.for_(PaymentGateway, profile=Profile.TEST)
class FakePaymentAdapter:
    def __init__(self):
        self.charges: list[dict] = []
        self.refunds: list[dict] = []
        self.should_fail = False
        self.failure_reason = "Card declined"

    async def charge(self, amount: Decimal, currency: str, card_token: str) -> str:
        if self.should_fail:
            raise RuntimeError(self.failure_reason)

        transaction_id = f"fake_txn_{len(self.charges) + 1}"
        self.charges.append({
            "transaction_id": transaction_id,
            "amount": amount,
            "currency": currency,
            "card_token": card_token
        })
        return transaction_id

    async def refund(self, transaction_id: str, amount: Decimal) -> None:
        if self.should_fail:
            raise RuntimeError("Refund failed")

        self.refunds.append({
            "transaction_id": transaction_id,
            "amount": amount
        })

# adapters/database.py
@adapter.for_(OrderRepository, profile=Profile.PRODUCTION)
class PostgresOrderRepository:
    def __init__(self, db: Database):
        self.db = db

    async def save_order(self, order: dict) -> None:
        async with self.db.engine.begin() as conn:
            await conn.execute(
                "INSERT INTO orders (id, customer_email, amount, status) VALUES (?, ?, ?, ?)",
                order["id"], order["customer_email"], order["amount"], order["status"]
            )

    # ... other methods

@adapter.for_(OrderRepository, profile=Profile.TEST)
class InMemoryOrderRepository:
    def __init__(self):
        self.orders: dict[str, dict] = {}

    async def save_order(self, order: dict) -> None:
        self.orders[order["id"]] = order.copy()

    async def find_by_id(self, order_id: str) -> dict | None:
        return self.orders.get(order_id)

    async def update_status(self, order_id: str, status: str) -> None:
        if order_id in self.orders:
            self.orders[order_id]["status"] = status
```

### Service

```python
# services/checkout.py
from dioxide import service
from decimal import Decimal
import uuid

@service
class CheckoutService:
    """Service for processing checkout and payments."""

    def __init__(self, payment: PaymentGateway, orders: OrderRepository):
        self.payment = payment
        self.orders = orders

    async def process_order(self, customer_email: str, amount: Decimal, card_token: str) -> dict:
        """Process a customer order.

        Returns:
            Order details with transaction_id and order_id

        Raises:
            RuntimeError: If payment fails
        """
        # Validation (business rule)
        if amount <= 0:
            raise ValueError("Amount must be positive")

        # Generate order ID
        order_id = str(uuid.uuid4())

        # Create order (pending)
        order = {
            "id": order_id,
            "customer_email": customer_email,
            "amount": amount,
            "status": "pending"
        }
        await self.orders.save_order(order)

        try:
            # Charge payment
            transaction_id = await self.payment.charge(amount, "usd", card_token)

            # Update order status
            order["transaction_id"] = transaction_id
            order["status"] = "completed"
            await self.orders.update_status(order_id, "completed")

            return order

        except Exception as e:
            # Mark order as failed
            await self.orders.update_status(order_id, "failed")
            raise RuntimeError(f"Payment failed: {e}")

    async def refund_order(self, order_id: str) -> None:
        """Refund a completed order."""
        # Find order
        order = await self.orders.find_by_id(order_id)
        if not order:
            raise ValueError("Order not found")

        if order["status"] != "completed":
            raise ValueError("Can only refund completed orders")

        # Refund payment
        await self.payment.refund(order["transaction_id"], order["amount"])

        # Update order status
        await self.orders.update_status(order_id, "refunded")
```

### Testing

```python
# tests/test_checkout.py
import pytest
from decimal import Decimal
from dioxide import container, Profile

@pytest.fixture
def test_container():
    container.scan("app", profile=Profile.TEST)
    return container

@pytest.fixture
def checkout_service(test_container):
    return test_container.resolve(CheckoutService)

@pytest.fixture
def fake_payment(test_container):
    return test_container.resolve(PaymentGateway)

@pytest.fixture
def fake_orders(test_container):
    return test_container.resolve(OrderRepository)

async def test_successful_order_processing(checkout_service, fake_payment, fake_orders):
    """Processes order successfully and creates transaction."""
    # Act
    order = await checkout_service.process_order(
        customer_email="alice@example.com",
        amount=Decimal("99.99"),
        card_token="tok_visa"
    )

    # Assert - check returned order
    assert order["status"] == "completed"
    assert order["customer_email"] == "alice@example.com"
    assert order["amount"] == Decimal("99.99")
    assert "transaction_id" in order

    # Assert - check payment was charged
    assert len(fake_payment.charges) == 1
    charge = fake_payment.charges[0]
    assert charge["amount"] == Decimal("99.99")
    assert charge["card_token"] == "tok_visa"

    # Assert - check order saved in database
    saved_order = await fake_orders.find_by_id(order["id"])
    assert saved_order is not None
    assert saved_order["status"] == "completed"

async def test_payment_failure_marks_order_failed(checkout_service, fake_payment, fake_orders):
    """Marks order as failed when payment fails."""
    # Arrange - make payment fail
    fake_payment.should_fail = True
    fake_payment.failure_reason = "Insufficient funds"

    # Act & Assert
    with pytest.raises(RuntimeError, match="Payment failed: Insufficient funds"):
        await checkout_service.process_order(
            customer_email="bob@example.com",
            amount=Decimal("50.00"),
            card_token="tok_declined"
        )

    # Assert - no successful charges
    assert len(fake_payment.charges) == 0

    # Assert - order marked as failed
    # (Check orders created with status="pending", then updated to "failed")
    orders = list(fake_orders.orders.values())
    assert len(orders) == 1
    assert orders[0]["status"] == "failed"

async def test_refund_completed_order(checkout_service, fake_payment, fake_orders):
    """Refunds a completed order."""
    # Arrange - create completed order
    order = await checkout_service.process_order(
        customer_email="carol@example.com",
        amount=Decimal("75.00"),
        card_token="tok_visa"
    )
    order_id = order["id"]

    # Act
    await checkout_service.refund_order(order_id)

    # Assert - refund recorded
    assert len(fake_payment.refunds) == 1
    refund = fake_payment.refunds[0]
    assert refund["transaction_id"] == order["transaction_id"]
    assert refund["amount"] == Decimal("75.00")

    # Assert - order status updated
    refunded_order = await fake_orders.find_by_id(order_id)
    assert refunded_order["status"] == "refunded"
```

**Testing benefits:**

- No real Stripe API calls (tests run in milliseconds)
- Can test failure scenarios easily (`fake_payment.should_fail = True`)
- Can inspect captured data (`fake_payment.charges`, `fake_orders.orders`)
- No flaky tests from network timeouts or rate limits

## Best Practices

### 1. Keep Ports Small and Focused

**Good** - Single responsibility:

```python
class EmailPort(Protocol):
    async def send(self, to: str, subject: str, body: str) -> None: ...

class SMSPort(Protocol):
    async def send(self, to: str, message: str) -> None: ...
```

**Bad** - Too many responsibilities:

```python
class NotificationPort(Protocol):
    async def send_email(self, to: str, subject: str, body: str) -> None: ...
    async def send_sms(self, to: str, message: str) -> None: ...
    async def send_push(self, device_id: str, message: str) -> None: ...
```

**Why?** Small ports are easier to implement, test, and swap. Multiple small ports are better than one large port.

### 2. Use Fakes, Not Mocks

**Good** - Real fake implementation:

```python
@adapter.for_(EmailPort, profile=Profile.TEST)
class FakeEmailAdapter:
    def __init__(self):
        self.sent_emails = []

    async def send(self, to: str, subject: str, body: str) -> None:
        self.sent_emails.append({"to": to, "subject": subject, "body": body})
```

**Bad** - Mock-based testing:

```python
@patch('sendgrid.send')
async def test_notification(mock_send):
    mock_send.return_value = True
    # Testing mock behavior, not real code
```

**Why?** Fakes are:
- Reusable across tests
- Can be used in development environment
- Test real code paths, not mock configuration
- Faster than mocks (no patching overhead)

### 3. Keep Services Pure (No Infrastructure)

**Good** - Pure business logic:

```python
@service
class UserService:
    def __init__(self, db: UserRepository, email: EmailPort):
        self.db = db
        self.email = email

    async def register_user(self, email_addr: str, name: str):
        # Business logic only
        if not email_addr or "@" not in email_addr:
            raise ValueError("Invalid email")

        user = {"email": email_addr, "name": name}
        await self.db.save_user(user)
        await self.email.send(email_addr, "Welcome!", f"Hello {name}!")
```

**Bad** - Infrastructure in service:

```python
@service
class UserService:
    async def register_user(self, email_addr: str, name: str):
        # Don't do this!
        conn = psycopg2.connect("dbname=production_db")
        sendgrid.send(to=email_addr, subject="Welcome!")
```

**Why?** Pure business logic is:
- Testable without database setup
- Independent of infrastructure choices
- Reusable across different adapters

### 4. Use Multiple Adapters for Different Profiles

**Good** - Different adapters per environment:

```python
@adapter.for_(EmailPort, profile=Profile.PRODUCTION)
class SendGridAdapter: ...

@adapter.for_(EmailPort, profile=Profile.TEST)
class FakeEmailAdapter: ...

@adapter.for_(EmailPort, profile=Profile.DEVELOPMENT)
class ConsoleEmailAdapter: ...
```

**Bad** - One adapter with environment checks:

```python
@adapter.for_(EmailPort, profile=Profile.ALL)
class EmailAdapter:
    def __init__(self, config: AppConfig):
        self.env = config.environment

    async def send(self, to: str, subject: str, body: str) -> None:
        if self.env == "production":
            # Real SendGrid
            ...
        elif self.env == "test":
            # Fake behavior
            ...
```

**Why?** Separate adapters:
- Are easier to understand and maintain
- Have no environment-specific branching
- Can be tested independently

### 5. Document Port Contracts

**Good** - Clear contract:

```python
class PaymentGateway(Protocol):
    """Port for processing payments.

    Implementations must handle:
    - Idempotent charge operations (same card_token can be charged multiple times)
    - Currency validation (only 'usd', 'eur', 'gbp' supported)
    - Error handling (raise RuntimeError with descriptive message on failure)
    """
    async def charge(self, amount: Decimal, currency: str, card_token: str) -> str:
        """Charge a payment method.

        Args:
            amount: Amount to charge (must be positive)
            currency: Currency code ('usd', 'eur', 'gbp')
            card_token: Payment method token from frontend

        Returns:
            Transaction ID from payment gateway (for refunds)

        Raises:
            ValueError: If amount <= 0 or currency invalid
            RuntimeError: If charge fails (card declined, network error, etc.)
        """
        ...
```

**Bad** - No documentation:

```python
class PaymentGateway(Protocol):
    async def charge(self, amount: Decimal, currency: str, card_token: str) -> str: ...
```

**Why?** Clear contracts:
- Help adapter implementers understand requirements
- Document error handling expectations
- Prevent subtle bugs from misunderstood contracts

## Anti-Patterns

### 1. Services Depending on Concrete Adapters

**Anti-pattern:**

```python
from adapters.sendgrid import SendGridAdapter

@service
class UserService:
    def __init__(self, email: SendGridAdapter):  # Depends on concrete adapter!
        self.email = email
```

**Problem:** Service now tightly coupled to SendGrid. Cannot swap implementations without changing service.

**Solution:** Depend on port (Protocol):

```python
@service
class UserService:
    def __init__(self, email: EmailPort):  # Depends on port
        self.email = email
```

### 2. Adapters with Business Logic

**Anti-pattern:**

```python
@adapter.for_(EmailPort, profile=Profile.PRODUCTION)
class SendGridAdapter:
    async def send(self, to: str, subject: str, body: str) -> None:
        # Business logic in adapter!
        if not to or "@" not in to:
            raise ValueError("Invalid email")

        # SendGrid API call
        ...
```

**Problem:** Business rules (email validation) scattered across adapters. Fakes might not implement same rules.

**Solution:** Move business logic to service:

```python
@service
class UserService:
    def register_user(self, email_addr: str, name: str):
        # Validation in service
        if not email_addr or "@" not in email_addr:
            raise ValueError("Invalid email")

        # Adapter just handles infrastructure
        await self.email.send(email_addr, "Welcome!", f"Hello {name}!")
```

### 3. Ports That Leak Implementation Details

**Anti-pattern:**

```python
class EmailPort(Protocol):
    async def send_with_sendgrid(self, api_key: str, to: str, subject: str) -> None: ...
```

**Problem:** Port exposes SendGrid-specific details. Fakes or alternative implementations forced to fake SendGrid.

**Solution:** Port should be implementation-agnostic:

```python
class EmailPort(Protocol):
    async def send(self, to: str, subject: str, body: str) -> None: ...
```

### 4. God Objects as Ports

**Anti-pattern:**

```python
class DatabasePort(Protocol):
    async def save_user(self, user: dict) -> None: ...
    async def find_user(self, user_id: str) -> dict: ...
    async def save_order(self, order: dict) -> None: ...
    async def find_order(self, order_id: str) -> dict: ...
    async def save_product(self, product: dict) -> None: ...
    # ... 50 more methods
```

**Problem:** Port too large, hard to implement, hard to test.

**Solution:** Split into focused repositories:

```python
class UserRepository(Protocol):
    async def save_user(self, user: dict) -> None: ...
    async def find_user(self, user_id: str) -> dict: ...

class OrderRepository(Protocol):
    async def save_order(self, order: dict) -> None: ...
    async def find_order(self, order_id: str) -> dict: ...
```

### 5. Using Mocks Instead of Fakes

**Anti-pattern:**

```python
@patch('adapters.sendgrid.SendGridAdapter.send')
async def test_notification(mock_send):
    mock_send.return_value = None
    # Testing mock behavior, not real code
```

**Problem:** Tests become brittle, test mock configuration rather than business logic.

**Solution:** Use real fake adapter:

```python
async def test_notification(test_container):
    fake_email = test_container.resolve(EmailPort)
    service = test_container.resolve(NotificationService)

    await service.send_welcome_email("alice@example.com", "Alice")

    assert len(fake_email.sent_emails) == 1
```

## Summary

**Hexagonal Architecture with dioxide:**

1. **Define Ports** - Protocols that define seams (interfaces)
2. **Create Adapters** - Concrete implementations for different profiles
3. **Write Services** - Pure business logic depending on ports
4. **Use Profiles** - Different adapters for prod/test/dev
5. **Test with Fakes** - Fast, real implementations instead of mocks

**Benefits:**

- Testable without I/O
- Maintainable (swap implementations easily)
- Clear architecture (explicit boundaries)
- Type-safe (mypy validates everything)

**Next steps:**

- Read [Testing with Fakes](testing_with_fakes.rst) for detailed testing patterns
- Explore the [API Reference](../api/dioxide/index.rst) for detailed API documentation
