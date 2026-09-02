from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Order, User, UserRole
from app.schemas import OrderCreate, OrderResponse, OrderStatusUpdate, AdminOrderWorkflow
from app.security import get_current_user, admin_required
from app.repositories.order_repository import order_repository
from app.services.order_service import order_service

router = APIRouter(prefix="/api/orders", tags=["orders"])

@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    order_in: OrderCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await order_service.create_order(db, current_user, order_in)

@router.get("/", response_model=List[OrderResponse])
async def list_orders(
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    is_admin = (current_user.role == UserRole.ADMIN)
    return await order_repository.list_orders(db, user_id=current_user.id, is_admin=is_admin)

@router.get("/workflow", response_model=AdminOrderWorkflow)
async def get_admin_workflow(
    admin_user=Depends(admin_required),
    db: AsyncSession = Depends(get_db),
    delivered_limit: int = 50,
    delivered_offset: int = 0,
):
    """Admin-only: return orders grouped into workflow buckets (new/preparing/ready/delivered/cancelled).

    The delivered history is paginated (delivered_limit / delivered_offset) so
    large delivered histories never need to be loaded fully.
    """
    delivered_limit = max(1, min(delivered_limit, 200))
    delivered_offset = max(0, delivered_offset)
    return await order_service.get_admin_workflow(
        db,
        delivered_limit=delivered_limit,
        delivered_offset=delivered_offset,
    )

@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    order = await order_repository.get_by_id(db, order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Order not found."
        )

    if current_user.role != UserRole.ADMIN and order.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this order.",
        )
    return order
@router.post("/{order_id}/cancel", response_model=OrderResponse)
async def cancel_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await order_service.cancel_order(db, current_user, order_id)

@router.put("/{order_id}/status", response_model=OrderResponse)
async def update_order_status(
    order_id: int,
    status_update: OrderStatusUpdate,
    admin_user=Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    return await order_service.update_order_status(db, order_id, status_update)


@router.delete("/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_order(
    order_id: int,
    admin_user=Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    """ADMIN-ONLY hard deletion of an order.

    Removes the order and its order_items, restores product stock, and requires
    admin authentication (admin_required). Normal customers are always rejected.
    """
    await order_service.delete_order(db, admin_user, order_id)
