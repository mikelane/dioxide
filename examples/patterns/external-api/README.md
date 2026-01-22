# External API Integration Example

This example demonstrates how to integrate with external APIs (like payment
gateways) using dioxide, with special focus on testing error scenarios.

## What This Example Demonstrates

1. **External API integration**: Wrapping third-party APIs with ports
2. **Error injection for testing**: Fake adapters that can simulate failures
3. **Retry and circuit breaker patterns**: Handling transient failures
4. **Testing failure scenarios**: Verify your code handles errors gracefully

## Architecture Overview

```
Production:
    PaymentService
        -> PaymentGatewayPort
            -> StripeAdapter (real Stripe API)

Test:
    PaymentService
        -> PaymentGatewayPort
            -> FakePaymentGateway (controllable, error injection)
```

## Key Concepts

### 1. Wrapping External APIs with Ports

External APIs should be wrapped in ports for testability:

```python
class PaymentGatewayPort(Protocol):
    """Port for payment processing."""

    async def charge(
        self,
        amount: Decimal,
        currency: str,
        card_token: str,
    ) -> PaymentResult:
        """Process a payment."""
        ...

    async def refund(
        self,
        payment_id: str,
        amount: Decimal | None = None,
    ) -> RefundResult:
        """Process a refund."""
        ...
```

### 2. Error Injection in Fakes

The fake adapter can be configured to fail in specific ways:

```python
@adapter.for_(PaymentGatewayPort, profile=Profile.TEST)
class FakePaymentGateway:
    def __init__(self):
        self.should_fail = False
        self.fail_with: Exception | None = None
        self.fail_after_n_calls: int | None = None
        self.call_count = 0

    async def charge(self, amount, currency, card_token):
        self.call_count += 1

        if self.should_fail:
            raise self.fail_with or PaymentError("Simulated failure")

        if self.fail_after_n_calls and self.call_count > self.fail_after_n_calls:
            raise PaymentError("Rate limit exceeded")

        # Success case
        return PaymentResult(id="pay_fake", status="succeeded")
```

### 3. Testing Error Scenarios

```python
async def test_handles_card_declined(container, fake_gateway):
    fake_gateway.should_fail = True
    fake_gateway.fail_with = CardDeclinedError("Card declined")

    service = container.resolve(PaymentService)

    result = await service.process_order(order)

    assert result.status == "payment_failed"
    assert "declined" in result.error_message.lower()

async def test_retries_on_transient_failure(container, fake_gateway):
    fake_gateway.fail_after_n_calls = 1  # Fail first, succeed after
    fake_gateway.fail_with = TransientError("Network timeout")

    service = container.resolve(PaymentService)

    result = await service.process_order_with_retry(order)

    assert result.status == "succeeded"
    assert fake_gateway.call_count == 2  # Retried once
```

## Running the Example

```bash
# From the dioxide repository root
cd examples/patterns/external-api

# Run the example
python -m app.main

# Run tests
pytest tests/ -v
```

## Error Types to Test

### 1. Network Errors

```python
fake_gateway.fail_with = NetworkError("Connection refused")
```

### 2. Authentication Errors

```python
fake_gateway.fail_with = AuthenticationError("Invalid API key")
```

### 3. Validation Errors

```python
fake_gateway.fail_with = ValidationError("Invalid card number")
```

### 4. Card Declined

```python
fake_gateway.fail_with = CardDeclinedError("Insufficient funds")
```

### 5. Rate Limiting

```python
fake_gateway.fail_after_n_calls = 5
fake_gateway.fail_with = RateLimitError("Too many requests")
```

### 6. Timeout

```python
fake_gateway.delay_seconds = 30  # Exceed timeout
```

## Patterns for Resilience

### Retry Pattern

```python
@service
class PaymentService:
    async def charge_with_retry(
        self,
        amount: Decimal,
        card_token: str,
        max_retries: int = 3,
    ) -> PaymentResult:
        for attempt in range(max_retries):
            try:
                return await self.gateway.charge(amount, "USD", card_token)
            except TransientError:
                if attempt == max_retries - 1:
                    raise
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
```

### Circuit Breaker Pattern

```python
@service
class PaymentService:
    def __init__(self, gateway: PaymentGatewayPort):
        self.gateway = gateway
        self._failure_count = 0
        self._circuit_open = False

    async def charge(self, amount: Decimal, card_token: str) -> PaymentResult:
        if self._circuit_open:
            raise CircuitOpenError("Payment service unavailable")

        try:
            result = await self.gateway.charge(amount, "USD", card_token)
            self._failure_count = 0
            return result
        except TransientError:
            self._failure_count += 1
            if self._failure_count >= 5:
                self._circuit_open = True
            raise
```

## Files Structure

```
external-api/
├── README.md
├── pyproject.toml
├── requirements.txt
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── domain/
│   │   ├── __init__.py
│   │   ├── models.py          # PaymentResult, Order, etc.
│   │   ├── ports.py           # PaymentGatewayPort
│   │   ├── errors.py          # Custom exceptions
│   │   └── services.py        # PaymentService
│   └── adapters/
│       ├── __init__.py
│       ├── stripe.py          # Production Stripe adapter
│       └── fakes.py           # FakePaymentGateway with error injection
└── tests/
    ├── __init__.py
    ├── conftest.py
    └── test_payment_service.py
```

## Learn More

- [dioxide Documentation](https://github.com/mikelane/dioxide)
- [Stripe API Documentation](https://stripe.com/docs/api)
- [Circuit Breaker Pattern](https://martinfowler.com/bliki/CircuitBreaker.html)
- [Retry Pattern](https://docs.microsoft.com/en-us/azure/architecture/patterns/retry)
