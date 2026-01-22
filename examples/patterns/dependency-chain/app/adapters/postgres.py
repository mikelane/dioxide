"""PostgreSQL adapters for production database operations.

In a real application, these would use asyncpg or SQLAlchemy.
This example simulates the behavior for demonstration purposes.
"""

from dioxide import Profile, adapter

from ..domain.models import Order, Product
from ..domain.ports import OrderRepositoryPort, ProductRepositoryPort


@adapter.for_(OrderRepositoryPort, profile=Profile.PRODUCTION)
class PostgresOrderRepository:
    """Production order repository using PostgreSQL.

    In a real implementation, this would:
    - Use asyncpg or SQLAlchemy for async database access
    - Have proper connection pooling
    - Use transactions for consistency
    """

    def __init__(self) -> None:
        """Initialize with simulated database state."""
        self._orders: dict[str, Order] = {}
        print("  [Postgres] Order repository initialized")

    async def save(self, order: Order) -> None:
        """Save an order to PostgreSQL."""
        self._orders[order.id] = order
        print(f"  [Postgres] Saved order {order.id}")

    async def get_by_id(self, order_id: str) -> Order | None:
        """Retrieve an order by ID from PostgreSQL."""
        order = self._orders.get(order_id)
        if order:
            print(f"  [Postgres] Found order {order_id}")
        else:
            print(f"  [Postgres] Order {order_id} not found")
        return order

    async def list_by_customer(self, customer_id: str) -> list[Order]:
        """List all orders for a customer from PostgreSQL."""
        orders = [o for o in self._orders.values() if o.customer_id == customer_id]
        print(f"  [Postgres] Found {len(orders)} orders for customer {customer_id}")
        return orders


@adapter.for_(ProductRepositoryPort, profile=Profile.PRODUCTION)
class PostgresProductRepository:
    """Production product repository using PostgreSQL.

    In a real implementation, this would query the products table.
    """

    def __init__(self) -> None:
        """Initialize with sample product data."""
        self._products: dict[str, Product] = {
            "prod-001": Product(id="prod-001", name="Widget", price=29.99, stock=100),
            "prod-002": Product(id="prod-002", name="Gadget", price=49.99, stock=50),
            "prod-003": Product(id="prod-003", name="Gizmo", price=19.99, stock=200),
        }
        print("  [Postgres] Product repository initialized with sample data")

    async def get_by_id(self, product_id: str) -> Product | None:
        """Retrieve a product by ID from PostgreSQL."""
        product = self._products.get(product_id)
        if product:
            print(f"  [Postgres] Found product {product_id}: {product.name}")
        else:
            print(f"  [Postgres] Product {product_id} not found")
        return product

    async def update_stock(self, product_id: str, quantity_delta: int) -> None:
        """Update product stock in PostgreSQL."""
        product = self._products.get(product_id)
        if product:
            product.stock += quantity_delta
            print(f"  [Postgres] Updated {product.name} stock by {quantity_delta}, new stock: {product.stock}")
