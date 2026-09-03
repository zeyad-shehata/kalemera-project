from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import func

from app.models import Order, OrderItem, Product, OrderStatus, FulfillmentType

class OrderRepository:
    async def create(
        self,
        db: AsyncSession,
        user_id: int,
        total_price: float,
        items: List[OrderItem],
        delivery_address: Optional[str] = None,
        delivery_fee: float = 0.0,
        fulfillment_type: FulfillmentType = FulfillmentType.DELIVERY,
        notes: Optional[str] = None,
        idempotency_key: Optional[str] = None,
    ) -> Order:
        order = Order(
            user_id=user_id,
            status=OrderStatus.PENDING,
            fulfillment_type=fulfillment_type,
            total_price=total_price,
            delivery_address=delivery_address,
            delivery_fee=delivery_fee,
            notes=notes,
            idempotency_key=idempotency_key,
            items=items,
        )
        db.add(order)
        await db.flush()
        return order

    async def list_orders(
        self, db: AsyncSession, user_id: Optional[int] = None, is_admin: bool = False
    ) -> List[Order]:
        query = select(Order).options(selectinload(Order.items), selectinload(Order.user), selectinload(Order.review))
        if not is_admin and user_id is not None:
            query = query.where(Order.user_id == user_id)
        # FIFO ordering: oldest orders first (created_at ASC), secondary sort by id ASC
        query = query.order_by(Order.created_at.asc(), Order.id.asc())

        result = await db.execute(query)
        return result.scalars().all()

    async def list_orders_by_status(
        self, db: AsyncSession, status: OrderStatus, limit: Optional[int] = None, offset: int = 0
    ) -> List[Order]:
        """Efficient server-side filtering of orders by status (FIFO within each status)."""
        query = (
            select(Order)
            .options(selectinload(Order.items), selectinload(Order.user), selectinload(Order.review))
            .where(Order.status == status)
            .order_by(Order.created_at.asc(), Order.id.asc())
        )
        if offset > 0:
            query = query.offset(offset)
        if limit is not None:
            query = query.limit(limit)
        result = await db.execute(query)
        return result.scalars().all()

    async def count_orders_by_status(self, db: AsyncSession, status: OrderStatus) -> int:
        """Efficient COUNT(*) for an order status (used for delivered history pagination)."""
        result = await db.execute(
            select(func.count()).select_from(Order).where(Order.status == status)
        )
        return int(result.scalar() or 0)

    async def list_admin_orders_workflow(
        self, db: AsyncSession, delivered_limit: int = 50, delivered_offset: int = 0
    ) -> dict:
        """Return orders grouped by workflow bucket for the Admin Orders UI.

        Active states (NEW/PREPARING/READY) are returned fully, oldest-first
        (FIFO). The delivered history is paginated to avoid loading all
        historical rows — this is important on Neon to keep IO low.
        """
        # Active buckets are normally small (a handful of in-flight orders), but
        # bound them defensively so a stuck/runaway status bucket can't force an
        # unbounded table scan/result set.
        ACTIVE_BUCKET_LIMIT = 500
        new_orders = await self.list_orders_by_status(db, OrderStatus.PENDING, limit=ACTIVE_BUCKET_LIMIT)
        preparing_orders = await self.list_orders_by_status(db, OrderStatus.PROCESSING, limit=ACTIVE_BUCKET_LIMIT)
        ready_orders = await self.list_orders_by_status(db, OrderStatus.SHIPPED, limit=ACTIVE_BUCKET_LIMIT)
        delivered_orders = await self.list_orders_by_status(
            db, OrderStatus.DELIVERED, limit=delivered_limit, offset=delivered_offset
        )
        delivered_total = await self.count_orders_by_status(db, OrderStatus.DELIVERED)
        cancelled_orders = await self.list_orders_by_status(db, OrderStatus.CANCELLED, limit=ACTIVE_BUCKET_LIMIT)
        return {
            "new": new_orders,
            "preparing": preparing_orders,
            "ready": ready_orders,
            "delivered": delivered_orders,
            "cancelled": cancelled_orders,
            "delivered_total": delivered_total,
        }

    async def get_by_id(self, db: AsyncSession, order_id: int) -> Optional[Order]:
        result = await db.execute(
            select(Order)
            .where(Order.id == order_id)
            .options(selectinload(Order.items), selectinload(Order.user), selectinload(Order.review))
        )
        return result.scalars().first()

    async def get_by_user_and_idempotency_key(
        self, db: AsyncSession, user_id: int, idempotency_key: str
    ) -> Optional[Order]:
        result = await db.execute(
            select(Order)
            .where(Order.user_id == user_id, Order.idempotency_key == idempotency_key)
            .options(selectinload(Order.items), selectinload(Order.user), selectinload(Order.review))
        )
        return result.scalars().first()

    async def update_status(self, db: AsyncSession, order: Order, new_status: OrderStatus) -> Order:
        order.status = new_status
        await db.commit()
        await db.refresh(order)
        return await self.get_by_id(db, order.id)

    async def restore_stock_for_order(self, db: AsyncSession, order: Order) -> None:
        for item in order.items:
            res = await db.execute(select(Product).where(Product.id == item.product_id))
            product = res.scalars().first()
            if product:
                product.stock += item.quantity

    async def delete(self, db: AsyncSession, order: Order) -> None:
        """Hard-delete an order and its order_items.

        order_items are removed via the ORM relationship cascade
        (cascade="all, delete-orphan"). Only the order and its own items are
        removed; users, products, and categories are left untouched.
        """
        await db.delete(order)
        await db.commit()

order_repository = OrderRepository()
