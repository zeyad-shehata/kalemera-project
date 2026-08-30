from datetime import datetime, timedelta, time, timezone
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, and_
from app.models import Order, OrderItem, Product, Category, OrderStatus

class ReportRepository:
    async def get_dashboard_summary(self, db: AsyncSession) -> Dict[str, Any]:
        sales_query = select(func.sum(Order.total_price)).where(
            Order.status != OrderStatus.CANCELLED
        )
        sales_result = await db.execute(sales_query)
        total_sales = float(sales_result.scalar() or 0.0)

        now = datetime.now(timezone.utc)
        today_start = datetime.combine(now.date(), time.min)
        today_end = datetime.combine(now.date(), time.max)
        orders_today_query = select(func.count(Order.id)).where(
            and_(Order.created_at >= today_start, Order.created_at <= today_end)
        )
        orders_today_result = await db.execute(orders_today_query)
        orders_today = orders_today_result.scalar() or 0

        top_products_query = (
            select(Product.name, func.sum(OrderItem.quantity).label("sold_qty"))
            .join(OrderItem, Product.id == OrderItem.product_id)
            .join(Order, Order.id == OrderItem.order_id)
            .where(Order.status != OrderStatus.CANCELLED)
            .group_by(Product.name)
            .order_by(func.sum(OrderItem.quantity).desc())
            .limit(5)
        )
        top_products_result = await db.execute(top_products_query)
        top_products = [
            {"name": row[0], "quantity": int(row[1])} for row in top_products_result.all()
        ]

        return {
            "totalSales": total_sales,
            "ordersToday": orders_today,
            "topProducts": top_products,
        }

    async def get_sales_by_date(
        self, db: AsyncSession, start_dt: datetime, end_dt: datetime
    ) -> List[Dict[str, Any]]:
        sales_by_date_query = (
            select(
                func.date(Order.created_at).label("date"),
                func.sum(Order.total_price).label("sales"),
            )
            .where(
                and_(
                    Order.created_at >= start_dt,
                    Order.created_at <= end_dt,
                    Order.status != OrderStatus.CANCELLED,
                )
            )
            .group_by(func.date(Order.created_at))
            .order_by(func.date(Order.created_at))
        )
        sales_result = await db.execute(sales_by_date_query)
        return [
            {"date": str(row[0]), "sales": float(row[1] or 0.0)}
            for row in sales_result.all()
        ]

    async def get_accounting_data(
        self, db: AsyncSession, start_time: datetime
    ) -> Dict[str, Any]:
        orders_query = select(Order).where(
            and_(
                Order.created_at >= start_time,
                Order.status != OrderStatus.CANCELLED
            )
        )
        orders = (await db.execute(orders_query)).scalars().all()

        total_orders = len(orders)
        total_sales = sum(o.total_price for o in orders)
        avg_order_value = total_sales / total_orders if total_orders > 0 else 0.0

        items_query = (
            select(func.sum(OrderItem.quantity))
            .join(Order, Order.id == OrderItem.order_id)
            .where(
                and_(
                    Order.created_at >= start_time,
                    Order.status != OrderStatus.CANCELLED
                )
            )
        )
        items_result = await db.execute(items_query)
        total_items_sold = int(items_result.scalar() or 0)

        best_sellers_query = (
            select(
                OrderItem.product_name_snapshot,
                OrderItem.product_name_en_snapshot,
                func.sum(OrderItem.quantity).label("sold_qty")
            )
            .join(Order, Order.id == OrderItem.order_id)
            .where(
                and_(
                    Order.created_at >= start_time,
                    Order.status != OrderStatus.CANCELLED
                )
            )
            .group_by(OrderItem.product_name_snapshot, OrderItem.product_name_en_snapshot)
            .order_by(func.sum(OrderItem.quantity).desc())
            .limit(5)
        )
        best_sellers_result = await db.execute(best_sellers_query)
        best_sellers = [
            {
                "name": row[0],
                "name_en": row[1] or row[0],
                "quantity": int(row[2])
            }
            for row in best_sellers_result.all()
        ]

        sales_by_cat_query = (
            select(
                Category.name,
                func.sum(OrderItem.subtotal).label("sales_amount"),
                func.sum(OrderItem.quantity).label("sales_qty")
            )
            .join(Product, Product.id == OrderItem.product_id)
            .join(Category, Category.id == Product.category_id)
            .join(Order, Order.id == OrderItem.order_id)
            .where(
                and_(
                    Order.created_at >= start_time,
                    Order.status != OrderStatus.CANCELLED
                )
            )
            .group_by(Category.name)
        )
        sales_by_cat_result = await db.execute(sales_by_cat_query)
        sales_by_category = [
            {
                "category": row[0],
                "sales": float(row[1] or 0.0),
                "quantity": int(row[2] or 0)
            }
            for row in sales_by_cat_result.all()
        ]

        return {
            "totalOrders": total_orders,
            "totalSales": total_sales,
            "averageOrderValue": avg_order_value,
            "totalItemsSold": total_items_sold,
            "bestSellers": best_sellers,
            "salesByCategory": sales_by_category
        }

report_repository = ReportRepository()
