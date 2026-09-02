from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Order, OrderItem, Product, User, UserRole, OrderStatus, Notification
from app.repositories.order_repository import order_repository
from app.repositories.product_repository import product_repository
from app.repositories.notification_repository import notification_repository
from app.schemas import (
    OrderCreate,
    OrderStatusUpdate,
    ALLOWED_ADDRESSES,
    calculate_delivery_fee,
    OrderResponse,
    AdminOrderWorkflow,
)
from app.services.business_hours import is_store_closed, closed_message

class OrderService:
    async def create_order(
        self, db: AsyncSession, current_user: User, order_in: OrderCreate
    ) -> Order:
        # Business hours enforcement (server timezone: Africa/Cairo)
        if is_store_closed():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=closed_message(),
            )

        if not order_in.items:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Order must contain at least one item.",
            )

        # Validate delivery address (backend validation - user cannot bypass with manual API call)
        if not order_in.delivery_address or order_in.delivery_address.strip() == "":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Delivery address is required.",
            )
        
        if order_in.delivery_address not in ALLOWED_ADDRESSES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid delivery address. Allowed addresses are: {', '.join(ALLOWED_ADDRESSES)}",
            )

        total_price = 0.0
        order_items_to_create = []

        for item in order_in.items:
            product = await product_repository.get_by_id(db, item.product_id)
            if not product:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Product with ID {item.product_id} not found.",
                )

            if product.stock < item.quantity:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Not enough stock for product '{product.name}'. Available: {product.stock}, Requested: {item.quantity}.",
                )

            # Deduct stock
            product.stock -= item.quantity

            # Variant and price calculation
            variant_name_snapshot = None
            variant_id = item.variant_id

            if variant_id is not None:
                variant = next((v for v in product.variants if v.id == variant_id), None)
                if not variant:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Variant with ID {variant_id} does not exist for product '{product.name}'.",
                    )
                item_price = float(variant.price)
                variant_name_snapshot = variant.name
            elif product.variants and len(product.variants) > 0:
                # Product has variants, default to first variant
                variant = product.variants[0]
                variant_id = variant.id
                item_price = float(variant.price)
                variant_name_snapshot = variant.name
            else:
                item_price = float(product.price)

            subtotal = item_price * item.quantity
            total_price += subtotal

            order_item = OrderItem(
                product_id=product.id,
                product_name_snapshot=product.name,
                product_name_en_snapshot=product.name_en or product.name,
                variant_id=variant_id,
                variant_name_snapshot=variant_name_snapshot,
                price_snapshot=item_price,
                quantity=item.quantity,
                subtotal=subtotal
            )
            order_items_to_create.append(order_item)

        # Calculate delivery fee server-side (authoritative)
        delivery_fee = calculate_delivery_fee(order_in.delivery_address)
        total_price += delivery_fee

        new_order = await order_repository.create(
            db=db,
            user_id=current_user.id,
            total_price=total_price,
            items=order_items_to_create,
            delivery_address=order_in.delivery_address,
            delivery_fee=delivery_fee,
        )

        # Notify buyer
        await notification_repository.create(
            db=db,
            user_id=current_user.id,
            message=f"Order #{new_order.id} has been placed successfully. Subtotal: {total_price - delivery_fee:.2f} EGP, Delivery: {delivery_fee:.2f} EGP, Total: {total_price:.2f} EGP."
        )
        await db.commit()

        return await order_repository.get_by_id(db, new_order.id)

    async def delete_order(
        self, db: AsyncSession, current_user: User, order_id: int
    ) -> None:
        """ADMIN-ONLY hard deletion of an order.

        Removes the order and its order_items. Stock is restored so product
        availability stays consistent (mirrors the cancellation flow). This is a
        deliberate, destructive admin action used to remove test/orphaned orders;
        it is never exposed to customers. Users, products, and categories are not
        affected.
        """
        if current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only administrators can delete orders.",
            )

        order = await order_repository.get_by_id(db, order_id)
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Order not found."
            )

        # Restore stock before deleting so product availability is preserved.
        await order_repository.restore_stock_for_order(db, order)
        await order_repository.delete(db, order)

    async def cancel_order(
        self, db: AsyncSession, current_user: User, order_id: int
    ) -> Order:
        order = await order_repository.get_by_id(db, order_id)
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Order not found."
            )

        if current_user.role != UserRole.ADMIN and order.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to cancel this order.",
            )

        if order.status != OrderStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Order cannot be cancelled. Current status: {order.status.value}.",
            )

        order.status = OrderStatus.CANCELLED
        await order_repository.restore_stock_for_order(db, order)

        await notification_repository.create(
            db=db,
            user_id=order.user_id,
            message=f"Order #{order.id} has been cancelled. Stock has been restored."
        )

        await db.commit()
        return await order_repository.get_by_id(db, order.id)

    async def update_order_status(
        self, db: AsyncSession, order_id: int, status_update: OrderStatusUpdate
    ) -> Order:
        order = await order_repository.get_by_id(db, order_id)
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Order not found."
            )

        current = order.status
        target = status_update.status

        # Enforce logical forward transitions (NEW -> PREPARING -> READY -> DELIVERED)
        # CANCELLED is allowed from PENDING (same as existing cancel logic), and admin may
        # move a non-delivered order back when explicitly requested, but we prevent
        # nonsensical forwards skips and backward jumps.
        forward_map = {
            OrderStatus.PENDING: {OrderStatus.PROCESSING, OrderStatus.CANCELLED, OrderStatus.SHIPPED, OrderStatus.DELIVERED},
            OrderStatus.PROCESSING: {OrderStatus.SHIPPED, OrderStatus.CANCELLED},
            OrderStatus.SHIPPED: {OrderStatus.DELIVERED, OrderStatus.CANCELLED},
            OrderStatus.DELIVERED: set(),
            OrderStatus.CANCELLED: set(),
        }

        allowed = forward_map.get(current, set())

        if target not in allowed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status transition from {current.value} to {target.value}.",
            )

        if (
            target == OrderStatus.CANCELLED
            and current != OrderStatus.CANCELLED
        ):
            await order_repository.restore_stock_for_order(db, order)

        order.status = target

        await notification_repository.create(
            db=db,
            user_id=order.user_id,
            message=f"Order #{order.id} status has been updated to: {target.value}."
        )

        await db.commit()
        return await order_repository.get_by_id(db, order.id)

    async def get_admin_workflow(
        self, db: AsyncSession, delivered_limit: int = 50, delivered_offset: int = 0
    ) -> AdminOrderWorkflow:
        """Return orders grouped by workflow bucket for the Admin Orders UI."""
        workflow = await order_repository.list_admin_orders_workflow(
            db,
            delivered_limit=delivered_limit,
            delivered_offset=delivered_offset,
        )
        return AdminOrderWorkflow(
            new=[OrderResponse.model_validate(o) for o in workflow["new"]],
            preparing=[OrderResponse.model_validate(o) for o in workflow["preparing"]],
            ready=[OrderResponse.model_validate(o) for o in workflow["ready"]],
            delivered=[OrderResponse.model_validate(o) for o in workflow["delivered"]],
            cancelled=[OrderResponse.model_validate(o) for o in workflow["cancelled"]],
            delivered_total=workflow["delivered_total"],
        )

order_service = OrderService()
