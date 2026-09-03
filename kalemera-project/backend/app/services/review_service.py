from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User, UserRole, OrderStatus
from app.repositories.order_repository import order_repository
from app.repositories.review_repository import review_repository
from app.schemas import ReviewCreate


class ReviewService:
    async def create_review(
        self, db: AsyncSession, current_user: User, order_id: int, review_in: ReviewCreate
    ):
        order = await order_repository.get_by_id(db, order_id)
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Order not found."
            )

        if order.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only review your own orders.",
            )

        if order.status != OrderStatus.DELIVERED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only delivered orders can be reviewed.",
            )

        existing = await review_repository.get_by_order_id(db, order_id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This order has already been reviewed.",
            )

        return await review_repository.create(
            db,
            order_id=order_id,
            user_id=current_user.id,
            rating=review_in.rating,
            comment=review_in.comment,
        )

    async def list_admin_reviews(self, db: AsyncSession, limit: int = 50, offset: int = 0):
        return await review_repository.list_all(db, limit=limit, offset=offset)

    async def list_public_reviews(self, db: AsyncSession, limit: int = 50, offset: int = 0):
        return await review_repository.list_public(db, limit=limit, offset=offset)


review_service = ReviewService()
