"""Tests for the Reviews/Ratings feature: creation, authorization, and privacy.

Enforces: only the order owner may review, only DELIVERED orders can be
reviewed, exactly one review per order, and the public schema never leaks
phone/address/order notes.
"""
import uuid

import pytest
from fastapi import HTTPException

from app.models import Category, Product, OrderStatus
from app.schemas import OrderCreate, OrderItemCreate, ReviewCreate, ReviewResponse
from app.services.order_service import order_service
from app.services.review_service import review_service


async def _make_delivered_order(db_session, user):
    cat = Category(name=f"Review Test {uuid.uuid4().hex[:6]}")
    db_session.add(cat)
    await db_session.flush()

    product = Product(
        name=f"Reviewable Item {uuid.uuid4().hex[:6]}", price=30.0, stock=5, category_id=cat.id
    )
    db_session.add(product)
    await db_session.flush()

    order_in = OrderCreate(
        items=[OrderItemCreate(product_id=product.id, quantity=1)],
        delivery_address="سكن الولاد الداخلي",
    )
    order = await order_service.create_order(db_session, user, order_in)
    order.status = OrderStatus.DELIVERED
    await db_session.commit()
    await db_session.refresh(order)
    return order


@pytest.mark.asyncio
async def test_owner_can_review_delivered_order(db_session, test_user):
    order = await _make_delivered_order(db_session, test_user)

    review = await review_service.create_review(
        db_session, test_user, order.id, ReviewCreate(rating=5, comment="Great!")
    )
    assert review.rating == 5
    assert review.comment == "Great!"
    assert review.order_id == order.id


@pytest.mark.asyncio
async def test_cannot_review_non_delivered_order(db_session, test_user, sample_product):
    order_in = OrderCreate(
        items=[OrderItemCreate(product_id=sample_product.id, quantity=1)],
        delivery_address="سكن الولاد الداخلي",
    )
    order = await order_service.create_order(db_session, test_user, order_in)
    assert order.status == OrderStatus.PENDING

    with pytest.raises(HTTPException) as exc_info:
        await review_service.create_review(
            db_session, test_user, order.id, ReviewCreate(rating=4)
        )
    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_cannot_review_someone_elses_order(db_session, test_user, admin_user):
    order = await _make_delivered_order(db_session, test_user)

    with pytest.raises(HTTPException) as exc_info:
        await review_service.create_review(
            db_session, admin_user, order.id, ReviewCreate(rating=3)
        )
    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_cannot_review_same_order_twice(db_session, test_user):
    order = await _make_delivered_order(db_session, test_user)

    await review_service.create_review(
        db_session, test_user, order.id, ReviewCreate(rating=5)
    )
    with pytest.raises(HTTPException) as exc_info:
        await review_service.create_review(
            db_session, test_user, order.id, ReviewCreate(rating=1)
        )
    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_public_review_schema_excludes_private_fields(db_session, test_user):
    order = await _make_delivered_order(db_session, test_user)
    review = await review_service.create_review(
        db_session, test_user, order.id, ReviewCreate(rating=5, comment="Nice")
    )

    public = ReviewResponse.model_validate(review)
    dumped = public.model_dump()
    assert set(dumped.keys()) == {"id", "order_id", "rating", "comment", "created_at"}
    for leaked_field in ("phone", "delivery_address", "notes", "full_name"):
        assert leaked_field not in dumped
