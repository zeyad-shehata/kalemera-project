from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import User
from app.schemas import ReviewCreate, ReviewResponse, ReviewAdminResponse
from app.security import get_current_user, admin_required
from app.services.review_service import review_service

router = APIRouter(prefix="/api/reviews", tags=["reviews"])


@router.post("/orders/{order_id}", response_model=ReviewResponse, status_code=201)
async def create_review(
    order_id: int,
    review_in: ReviewCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await review_service.create_review(db, current_user, order_id, review_in)


@router.get("/", response_model=List[ReviewResponse])
async def list_public_reviews(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """Public-safe listing: only rating/comment/created_at are ever exposed here."""
    return await review_service.list_public_reviews(db, limit=limit, offset=offset)


@router.get("/admin", response_model=List[ReviewAdminResponse])
async def list_admin_reviews(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    admin_user: User = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    """Admin view: rating, comment, date, and reviewer name only — never phone,
    address, or private order notes."""
    reviews = await review_service.list_admin_reviews(db, limit=limit, offset=offset)
    return [
        ReviewAdminResponse(
            id=r.id,
            order_id=r.order_id,
            rating=r.rating,
            comment=r.comment,
            created_at=r.created_at,
            reviewer_name=r.user.full_name if r.user else None,
        )
        for r in reviews
    ]
