from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.models import Order, OrderItem, Product, OrderStatus

class OrderRepository:
    async def create(
        self, db: AsyncSession, user_id: int, total_price: float, items: List[OrderItem], delivery_address: Optional[str] = None
    ) -> Order:
        order = Order(
            user_id=user_id,
            status=OrderStatus.PENDING,
            total_price=total_price,
            delivery_address=delivery_address,
            items=items,
        )
        db.add(order)
        await db.flush()
        return order

    async def list_orders(
        self, db: AsyncSession, user_id: Optional[int] = None, is_admin: bool = False
    ) -> List[Order]:
        query = select(Order).options(selectinload(Order.items), selectinload(Order.user))
        if not is_admin and user_id is not None:
            query = query.where(Order.user_id == user_id)
        query = query.order_by(Order.created_at.desc())

        result = await db.execute(query)
        return result.scalars().all()

    async def get_by_id(self, db: AsyncSession, order_id: int) -> Optional[Order]:
        result = await db.execute(
            select(Order)
            .where(Order.id == order_id)
            .options(selectinload(Order.items), selectinload(Order.user))
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
