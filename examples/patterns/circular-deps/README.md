# Circular Dependency Detection and Resolution Example

This example demonstrates how dioxide detects circular dependencies at startup
and how to refactor your code to eliminate them.

## What This Example Demonstrates

1. **Circular dependency detection**: dioxide catches cycles at container initialization
2. **Clear error messages**: Error tells you exactly which types form the cycle
3. **Refactoring patterns**: Three strategies to break circular dependencies
4. **Architecture improvements**: Better design emerges from fixing cycles

## Why Circular Dependencies Are Bad

Circular dependencies indicate a design flaw:

```
ServiceA -> ServiceB -> ServiceA  (cycle!)
```

Problems:
- **Initialization order**: Which service gets created first?
- **Testing difficulty**: Can't test one without the other
- **Tight coupling**: Changes ripple through the cycle
- **Code smell**: Usually indicates responsibilities are mixed

## dioxide's Approach

dioxide does NOT support circular dependencies. Instead of hiding the problem
with lazy injection or Provider patterns, dioxide fails fast at startup with
a clear error message showing the cycle.

**This is intentional.** Circular dependencies are a design flaw, not something
to work around with framework tricks.

## Running the Example

```bash
# From the dioxide repository root
cd examples/patterns/circular-deps

# Run the problem demonstration (shows error)
python problem.py

# Run the solution demonstration
python solution.py
```

## The Problem

Here's a common circular dependency pattern:

```python
# The Problem: OrderService and NotificationService depend on each other

class OrderService:
    def __init__(self, notifications: NotificationService):
        self.notifications = notifications

    def create_order(self, data):
        order = Order(**data)
        self.notifications.notify_order_created(order)
        return order

class NotificationService:
    def __init__(self, orders: OrderService):
        self.orders = orders

    def notify_order_status_change(self, order_id: str):
        order = self.orders.get_order(order_id)  # Needs order details!
        self.send_email(order.customer_email, f"Order {order_id} status changed")
```

When dioxide tries to resolve `OrderService`:
1. It needs `NotificationService`
2. `NotificationService` needs `OrderService`
3. **Cycle detected!**

## dioxide's Error Message

```
CircularDependencyError: Circular dependency detected:
  OrderService -> NotificationService -> OrderService

Refactoring suggestions:
1. Extract shared logic to a new service
2. Use an event-based pattern (publisher/subscriber)
3. Pass data instead of service references
```

## Solutions

### Solution 1: Extract Shared Data Access

If `NotificationService` only needs order data (not full service):

```python
# Extract an OrderRepository for data access
class OrderRepositoryPort(Protocol):
    async def get_by_id(self, order_id: str) -> Order: ...

@service
class OrderService:
    def __init__(
        self,
        repository: OrderRepositoryPort,
        notifications: NotificationService,
    ):
        self.repository = repository
        self.notifications = notifications

@service
class NotificationService:
    def __init__(self, repository: OrderRepositoryPort):
        # Now depends on data, not service
        self.repository = repository

    async def notify_order_status_change(self, order_id: str):
        order = await self.repository.get_by_id(order_id)
        await self.send_email(order.customer_email, ...)
```

Now: `OrderService -> NotificationService -> OrderRepository` (no cycle!)

### Solution 2: Event-Based Communication

Use domain events to decouple services:

```python
class EventBusPort(Protocol):
    async def publish(self, event: DomainEvent) -> None: ...
    def subscribe(self, event_type: type, handler: Callable) -> None: ...

@service
class OrderService:
    def __init__(self, repository: OrderRepositoryPort, events: EventBusPort):
        self.repository = repository
        self.events = events

    async def create_order(self, data) -> Order:
        order = Order(**data)
        await self.repository.save(order)
        await self.events.publish(OrderCreated(order_id=order.id))
        return order

@service
class NotificationService:
    def __init__(self, events: EventBusPort, repository: OrderRepositoryPort):
        self.repository = repository
        events.subscribe(OrderCreated, self.handle_order_created)

    async def handle_order_created(self, event: OrderCreated):
        order = await self.repository.get_by_id(event.order_id)
        await self.send_welcome_email(order)
```

Now: Both services depend on `EventBusPort` (no direct dependency!)

### Solution 3: Pass Data Instead of References

Sometimes the simplest fix is passing data directly:

```python
@service
class OrderService:
    def __init__(self, repository: OrderRepositoryPort):
        self.repository = repository

    async def create_order(self, data) -> Order:
        order = Order(**data)
        await self.repository.save(order)
        return order  # Caller handles notification

# In controller/use case layer:
class CreateOrderUseCase:
    def __init__(self, orders: OrderService, notifications: NotificationService):
        self.orders = orders
        self.notifications = notifications

    async def execute(self, data) -> Order:
        order = await self.orders.create_order(data)
        await self.notifications.notify_order_created(order)  # Pass data!
        return order
```

Now: Use case orchestrates, services are independent.

## Best Practices

### Detect Cycles Early

dioxide fails at container initialization, not at resolution time. This means:
- CI catches cycles immediately
- No runtime surprises in production
- Clear error messages with cycle path

### Prefer Events for Cross-Cutting Concerns

Notifications, logging, and analytics often create cycles. Events break them:

```python
# Instead of:
OrderService -> NotificationService -> OrderService

# Use:
OrderService -> EventBus <- NotificationService
              (publish)      (subscribe)
```

### Keep Services Focused

If ServiceA needs ServiceB and ServiceB needs ServiceA, ask:
- Are responsibilities mixed?
- Should this be one service?
- Is there missing abstraction?

## Files

```
circular-deps/
├── README.md           # This file
├── problem.py          # Demonstrates the circular dependency error
└── solution.py         # Shows refactored, working solution
```

## Learn More

- [dioxide Documentation](https://github.com/mikelane/dioxide)
- [Dependency Inversion Principle](https://en.wikipedia.org/wiki/Dependency_inversion_principle)
- [Event-Driven Architecture](https://martinfowler.com/articles/201701-event-driven.html)
