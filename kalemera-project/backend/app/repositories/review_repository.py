from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from app.models import Review


class ReviewRepository:
    async def get_by_order_id(self, db: AsyncSession, order_id: int) -> Optional[Review]:
        result = await db.execute(select(Review).where(Review.order_id == order_id))
        return result.scalars().first()

    async def get_by_id(self, db: AsyncSession, review_id: int) -> Optional[Review]:
        result = await db.execute(select(Review).where(Review.id == review_id))
        return result.scalars().first()

    async def create(
        self, db: AsyncSession, order_id: int, user_id: int, rating: int, comment: Optional[str]
    ) -> Review:
        review = Review(order_id=order_id, user_id=user_id, rating=rating, comment=comment)
        db.add(review)
        await db.commit()
        await db.refresh(review)
        return review

    async def list_all(
        self, db: AsyncSession, limit: int = 50, offset: int = 0
    ) -> List[Review]:
        """Admin listing, newest first, bounded/paginated."""
        result = await db.execute(
            select(Review)
            .options(selectinload(Review.user))
            .order_by(Review.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return result.scalars().all()

    async def list_public(
        self, db: AsyncSession, limit: int = 50, offset: int = 0
    ) -> List[Review]:
        """Public listing — caller must serialize with the public-safe ReviewResponse schema."""
        result = await db.execute(
            select(Review)
            .order_by(Review.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return result.scalars().all()


review_repository = ReviewRepository()
