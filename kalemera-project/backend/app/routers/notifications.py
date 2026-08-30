from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Notification, User
from app.schemas import NotificationResponse, NotificationCreate
from app.security import get_current_user, admin_required
from app.repositories.notification_repository import notification_repository
from app.repositories.user_repository import user_repository

router = APIRouter(prefix="/api/notifications", tags=["notifications"])

@router.get("/", response_model=List[NotificationResponse])
async def list_unread_notifications(
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    return await notification_repository.list_unread(db, current_user.id)

@router.post(
    "/", response_model=NotificationResponse, status_code=status.HTTP_201_CREATED
)
async def push_notification(
    notification_in: NotificationCreate,
    admin_user=Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    user = await user_repository.get_by_id(db, notification_in.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Target user not found."
        )

    return await notification_repository.create(db, notification_in.user_id, notification_in.message)

@router.put("/{notification_id}/read", response_model=NotificationResponse)
async def mark_notification_as_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    notification = await notification_repository.get_by_id(db, notification_id)
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found."
        )

    if notification.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to modify this notification.",
        )

    return await notification_repository.mark_as_read(db, notification)
