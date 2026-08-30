from typing import List, Optional
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models import Category, Product, OrderItem

class CategoryRepository:
    async def list_with_counts(self, db: AsyncSession) -> List[Category]:
        query = (
            select(Category, func.count(Product.id).label("product_count"))
            .outerjoin(Product, Category.id == Product.category_id)
            .group_by(Category.id)
            .order_by(Category.name)
        )
        result = await db.execute(query)
        categories = []
        for row in result.all():
            category = row[0]
            category.product_count = row[1]
            categories.append(category)
        return categories

    async def get_by_id(self, db: AsyncSession, category_id: int) -> Optional[Category]:
        result = await db.execute(select(Category).where(Category.id == category_id))
        return result.scalars().first()

    async def get_by_name(self, db: AsyncSession, name: str) -> Optional[Category]:
        result = await db.execute(select(Category).where(Category.name == name))
        return result.scalars().first()

    async def create(self, db: AsyncSession, name: str) -> Category:
        category = Category(name=name)
        db.add(category)
        await db.commit()
        await db.refresh(category)
        return category

    async def update(self, db: AsyncSession, category: Category, name: str) -> Category:
        category.name = name
        await db.commit()
        await db.refresh(category)
        return category

    async def has_ordered_products(self, db: AsyncSession, category_id: int) -> bool:
        product_ids = (
            (await db.execute(select(Product.id).where(Product.category_id == category_id)))
            .scalars()
            .all()
        )
        if product_ids:
            check = await db.execute(
                select(OrderItem.id).where(OrderItem.product_id.in_(product_ids)).limit(1)
            )
            return check.scalars().first() is not None
        return False

    async def delete(self, db: AsyncSession, category: Category) -> None:
        await db.delete(category)
        await db.commit()

category_repository = CategoryRepository()
