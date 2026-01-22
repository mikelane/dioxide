# Caching Adapter Pattern Example

This example demonstrates the caching adapter pattern (decorator pattern) with
dioxide, showing how to wrap a real repository with caching behavior that can
be swapped out based on profile.

## What This Example Demonstrates

1. **Caching decorator pattern**: Wrap a repository with transparent caching
2. **Profile-based switching**: Production uses caching, tests use fakes
3. **Cache invalidation strategies**: TTL and explicit invalidation
4. **Testing cache behavior**: Verify caching without real Redis

## Architecture Overview

```
Production Stack:
    UserService
        -> CachingUserRepository (caches reads)
            -> PostgresUserRepository (actual database)
            -> RedisCache (cache storage)

Test Stack:
    UserService
        -> FakeUserRepository (in-memory, no caching)
```

## The Caching Pattern

The caching adapter wraps another repository and adds caching behavior:

```python
@adapter.for_(UserRepositoryPort, profile=Profile.PRODUCTION)
class CachingUserRepository:
    def __init__(
        self,
        delegate: DatabaseUserRepository,  # The "real" repository
        cache: CachePort,                   # Cache storage
    ):
        self.delegate = delegate
        self.cache = cache

    async def get_by_id(self, user_id: str) -> User | None:
        # Check cache first
        cached = await self.cache.get(f"user:{user_id}")
        if cached:
            return User(**cached)

        # Cache miss - get from database
        user = await self.delegate.get_by_id(user_id)
        if user:
            await self.cache.set(f"user:{user_id}", user.to_dict())

        return user
```

## Key Concepts

### 1. The Delegate Pattern

The caching repository delegates to a "real" repository:

```python
class CachingUserRepository:
    def __init__(self, delegate: DatabaseUserRepository, cache: CachePort):
        self.delegate = delegate  # PostgresUserRepository
        self.cache = cache        # RedisCache
```

This allows:
- Transparent caching (callers don't know about it)
- Easy testing (swap delegate with fake)
- Clear separation of concerns

### 2. Profile-Based Configuration

```python
# Production: Uses caching wrapper
@adapter.for_(UserRepositoryPort, profile=Profile.PRODUCTION)
class CachingUserRepository:
    def __init__(self, delegate: DatabaseUserRepository, cache: CachePort):
        ...

# Test: No caching, just in-memory storage
@adapter.for_(UserRepositoryPort, profile=Profile.TEST)
class FakeUserRepository:
    def __init__(self):
        self.users = {}
```

### 3. Cache Invalidation

```python
async def save(self, user: User) -> None:
    await self.delegate.save(user)
    # Invalidate cache on write
    await self.cache.delete(f"user:{user.id}")
```

## Running the Example

```bash
# From the dioxide repository root
cd examples/patterns/caching

# Run the example
python -m app.main

# Run tests
pytest tests/ -v
```

## Testing Strategies

### Test Cache Hits and Misses

```python
async def test_caches_user_on_first_read(container, cache):
    service = container.resolve(UserService)

    # First read - cache miss
    await service.get_user("user-1")
    assert cache.miss_count == 1

    # Second read - cache hit
    await service.get_user("user-1")
    assert cache.hit_count == 1
```

### Test Cache Invalidation

```python
async def test_invalidates_cache_on_update(container, cache):
    service = container.resolve(UserService)

    # Read to populate cache
    await service.get_user("user-1")
    assert "user:user-1" in cache.data

    # Update should invalidate
    await service.update_user("user-1", name="New Name")
    assert "user:user-1" not in cache.data
```

### Test Without Cache (Profile.TEST)

```python
async def test_works_without_caching(container):
    # TEST profile uses FakeUserRepository (no caching)
    service = container.resolve(UserService)

    await service.get_user("user-1")
    # Works fine, just no caching
```

## When to Use This Pattern

**Good use cases:**
- Read-heavy data (user profiles, product catalogs)
- Data that doesn't change frequently
- Expensive database queries

**Consider alternatives when:**
- Data changes frequently (use shorter TTL or skip caching)
- Consistency is critical (banking, inventory)
- Data is user-specific (session storage might be better)

## Files Structure

```
caching/
├── README.md
├── pyproject.toml
├── requirements.txt
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── domain/
│   │   ├── __init__.py
│   │   ├── models.py
│   │   ├── ports.py
│   │   └── services.py
│   └── adapters/
│       ├── __init__.py
│       ├── postgres.py      # DatabaseUserRepository
│       ├── caching.py       # CachingUserRepository
│       ├── redis.py         # RedisCache
│       └── fakes.py         # FakeUserRepository, FakeCache
└── tests/
    ├── __init__.py
    ├── conftest.py
    └── test_caching.py
```

## Learn More

- [dioxide Documentation](https://github.com/mikelane/dioxide)
- [Cache-Aside Pattern](https://docs.microsoft.com/en-us/azure/architecture/patterns/cache-aside)
- [Decorator Pattern](https://refactoring.guru/design-patterns/decorator)
