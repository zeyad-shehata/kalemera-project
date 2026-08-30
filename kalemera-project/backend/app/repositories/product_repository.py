from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy import func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.models import Product, ProductVariant, OrderItem, Order, OrderStatus

class ProductRepository:
    async def list_paginated(
        self,
        db: AsyncSession,
        search: Optional[str] = None,
        category: Optional[int] = None,
        sort_by: Optional[str] = None,
        sort_order: Optional[str] = "asc",
        page: int = 1,
        size: int = 10,
    ) -> Tuple[List[Product], int]:
        if page < 1:
            page = 1
        if size < 1:
            size = 10
        offset = (page - 1) * size

        query = select(Product).options(selectinload(Product.variants))
        count_query = select(func.count(Product.id))

        if category is not None:
            query = query.where(Product.category_id == category)
            count_query = count_query.where(Product.category_id == category)

        if search:
            search_filter = or_(
                Product.name.ilike(f"%{search}%"),
                Product.name_en.ilike(f"%{search}%"),
                Product.description.ilike(f"%{search}%"),
                Product.description_en.ilike(f"%{search}%"),
            )
            query = query.where(search_filter)
            count_query = count_query.where(search_filter)

        is_desc = sort_order and sort_order.lower() == "desc"

        if sort_by == "price":
            order_col = Product.price.desc() if is_desc else Product.price.asc()
            query = query.order_by(order_col)
        elif sort_by == "newest":
            query = query.order_by(Product.created_at.desc())
        elif sort_by == "best_selling":
            query = (
                query.outerjoin(OrderItem, Product.id == OrderItem.product_id)
                .outerjoin(Order, OrderItem.order_id == Order.id)
                .where(or_(Order.status == None, Order.status != OrderStatus.CANCELLED))
                .group_by(Product.id)
                .order_by(func.coalesce(func.sum(OrderItem.quantity), 0).desc())
            )
        else:
            order_col = Product.name.desc() if is_desc else Product.name.asc()
            query = query.order_by(order_col)

        query = query.offset(offset).limit(size)

        total_res = await db.execute(count_query)
        total = total_res.scalar() or 0

        products_res = await db.execute(query)
        products = products_res.scalars().all()

        return products, total

    async def get_by_id(self, db: AsyncSession, product_id: int) -> Optional[Product]:
        result = await db.execute(
            select(Product)
            .where(Product.id == product_id)
            .options(selectinload(Product.variants))
        )
        return result.scalars().first()

    async def is_referenced_in_orders(self, db: AsyncSession, product_id: int) -> bool:
        check = await db.execute(
            select(OrderItem.id).where(OrderItem.product_id == product_id).limit(1)
        )
        return check.scalars().first() is not None

    async def create(
        self,
        db: AsyncSession,
        name: str,
        name_en: Optional[str],
        description: Optional[str],
        description_en: Optional[str],
        price: float,
        stock: int,
        category_id: int,
        image_path: Optional[str],
        price_s: Optional[float] = None,
        price_l: Optional[float] = None,
    ) -> Product:
        product = Product(
            name=name,
            name_en=name_en,
            description=description,
            description_en=description_en,
            price=price,
            stock=stock,
            category_id=category_id,
            image_path=image_path,
        )

        if price_s is not None:
            product.variants.append(ProductVariant(name="S", price=price_s))
        if price_l is not None:
            product.variants.append(ProductVariant(name="L", price=price_l))

        db.add(product)
        await db.commit()

        return await self.get_by_id(db, product.id)

    async def update(
        self,
        db: AsyncSession,
        product: Product,
        name: str,
        name_en: Optional[str],
        description: Optional[str],
        description_en: Optional[str],
        price: float,
        stock: int,
        category_id: int,
        image_path: Optional[str],
        price_s: Optional[float] = None,
        price_l: Optional[float] = None,
    ) -> Product:
        product.name = name
        product.name_en = name_en
        product.description = description
        product.description_en = description_en
        product.price = price
        product.stock = stock
        product.category_id = category_id
        product.image_path = image_path

        # Update variants
        product.variants.clear()
        if price_s is not None:
            product.variants.append(ProductVariant(name="S", price=price_s))
        if price_l is not None:
            product.variants.append(ProductVariant(name="L", price=price_l))

        await db.commit()
        return await self.get_by_id(db, product.id)

    async def delete(self, db: AsyncSession, product: Product) -> None:
        await db.delete(product)
        await db.commit()

    async def get_all_active_image_paths(self, db: AsyncSession) -> List[str]:
        result = await db.execute(select(Product.image_path).where(Product.image_path != None))
        return [row[0] for row in result.all() if row[0]]

product_repository = ProductRepository()
