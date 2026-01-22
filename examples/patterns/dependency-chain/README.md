# Multi-Service Dependency Chain Example

This example demonstrates a realistic multi-service dependency chain typical of
production applications. It shows how dioxide handles complex dependency graphs
where services depend on multiple other services and adapters.

## What This Example Demonstrates

1. **Deep dependency chains**: Controller -> UseCase -> Repository + Cache + Events
2. **Multiple dependencies per service**: Services can depend on many ports
3. **Layered architecture**: Clear separation between HTTP, Application, and Domain layers
4. **Automatic dependency resolution**: dioxide resolves the entire graph automatically
5. **Testing with fakes**: Each adapter has a test fake for isolated testing

## Architecture Overview

```
HTTP Layer (Controllers)
    |
    v
Application Layer (Use Cases / Services)
    |
    +---> Domain Repositories
    |         |
    |         +---> Database Adapter (production)
    |         +---> In-Memory Adapter (test)
    |
    +---> Cache Port
    |         |
    |         +---> Redis Adapter (production)
    |         +---> In-Memory Adapter (test)
    |
    +---> Event Publisher Port
              |
              +---> Kafka Adapter (production)
              +---> In-Memory Adapter (test)
```

## The Dependency Graph

```python
OrderController
    |
    +---> OrderService (Use Case)
              |
              +---> OrderRepository (Port)
              |         -> PostgresOrderRepository (production)
              |         -> FakeOrderRepository (test)
              |
              +---> ProductRepository (Port)
              |         -> PostgresProductRepository (production)
              |         -> FakeProductRepository (test)
              |
              +---> CachePort
              |         -> RedisCache (production)
              |         -> FakeCache (test)
              |
              +---> EventPublisher (Port)
                        -> KafkaEventPublisher (production)
                        -> FakeEventPublisher (test)
```

## Running the Example

```bash
# From the dioxide repository root
cd examples/patterns/dependency-chain

# Install dependencies (if running standalone)
pip install -r requirements.txt

# Run the example
python -m app.main

# Run tests
pytest tests/ -v
```

## Key Concepts

### 1. Multiple Dependencies

Services can depend on multiple ports without complexity:

```python
@service
class OrderService:
    def __init__(
        self,
        orders: OrderRepositoryPort,
        products: ProductRepositoryPort,
        cache: CachePort,
        events: EventPublisherPort,
    ):
        # All dependencies injected automatically
        self.orders = orders
        self.products = products
        self.cache = cache
        self.events = events
```

### 2. Dependency Chain Resolution

dioxide resolves the entire dependency graph automatically:

```python
# Container resolves:
# 1. CachePort -> RedisCache (or FakeCache)
# 2. EventPublisherPort -> KafkaEventPublisher (or FakeEventPublisher)
# 3. OrderRepositoryPort -> PostgresOrderRepository (or FakeOrderRepository)
# 4. ProductRepositoryPort -> PostgresProductRepository (or FakeProductRepository)
# 5. OrderService with all dependencies injected
# 6. OrderController with OrderService injected

controller = container.resolve(OrderController)
```

### 3. Testing the Full Chain

In tests, the entire chain uses fakes:

```python
async def test_create_order(container):
    # Get fakes for verification
    fake_orders = container.resolve(OrderRepositoryPort)
    fake_events = container.resolve(EventPublisherPort)

    # Seed test data
    fake_products = container.resolve(ProductRepositoryPort)
    fake_products.seed(Product(id="p1", name="Widget", price=10.00))

    # Execute through full chain
    controller = container.resolve(OrderController)
    result = await controller.create_order(
        customer_id="c1",
        items=[{"product_id": "p1", "quantity": 2}]
    )

    # Verify side effects
    assert len(fake_orders.orders) == 1
    assert len(fake_events.published) == 1
```

## Why This Pattern Matters

### Testability

- Each layer can be tested in isolation
- Fakes replace real infrastructure with zero configuration
- Tests run in milliseconds, not seconds

### Flexibility

- Swap any adapter without changing business logic
- Add caching, logging, or events without modifying services
- Support multiple environments (prod, test, dev) with profiles

### Maintainability

- Clear dependency relationships
- Easy to understand what each service needs
- Changes are localized to specific adapters

## Files Structure

```
dependency-chain/
├── README.md
├── pyproject.toml
├── requirements.txt
├── app/
│   ├── __init__.py
│   ├── main.py              # Entry point and container setup
│   ├── domain/
│   │   ├── __init__.py
│   │   ├── models.py        # Domain entities
│   │   ├── ports.py         # Port definitions (Protocols)
│   │   └── services.py      # Use cases / business logic
│   └── adapters/
│       ├── __init__.py
│       ├── postgres.py      # Production database adapters
│       ├── redis.py         # Production cache adapter
│       ├── kafka.py         # Production event publisher
│       └── fakes.py         # Test fakes
└── tests/
    ├── __init__.py
    ├── conftest.py          # Test fixtures
    └── test_order_service.py
```

## Learn More

- [dioxide Documentation](https://github.com/mikelane/dioxide)
- [Hexagonal Architecture](https://alistair.cockburn.us/hexagonal-architecture/)
- [Clean Architecture by Robert Martin](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
