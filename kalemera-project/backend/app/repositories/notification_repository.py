from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models import Notification

class NotificationRepository:
    async def list_unread(self, db: AsyncSession, user_id: int) -> List[Notification]:
        result = await db.execute(
            select(Notification)
            .where(Notification.user_id == user_id, Notification.is_read == False)
            .order_by(Notification.created_at.desc())
        )
        return result.scalars().all()

    async def get_by_id(self, db: AsyncSession, notification_id: int) -> Optional[Notification]:
        result = await db.execute(select(Notification).where(Notification.id == notification_id))
        return result.scalars().first()

    async def create(self, db: AsyncSession, user_id: int, message: str) -> Notification:
        notification = Notification(user_id=user_id, message=message, is_read=False)
        db.add(notification)
        await db.commit()
        await db.refresh(notification)
        return notification

    async def mark_as_read(self, db: AsyncSession, notification: Notification) -> Notification:
        notification.is_read = True
        await db.commit()
        await db.refresh(notification)
        return notification

notification_repository = NotificationRepository()
