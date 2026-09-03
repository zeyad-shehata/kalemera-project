"""Tests for order idempotency: a repeated request with the same client-generated
idempotency_key must return the original order, never create a duplicate."""
import uuid

import pytest

from app.models import Category, Product
from app.schemas import OrderCreate, OrderItemCreate
from app.services.order_service import order_service


@pytest.mark.asyncio
async def test_repeated_request_with_same_idempotency_key_returns_same_order(
    db_session, test_user
):
    cat = Category(name=f"Idempotency Test {uuid.uuid4().hex[:6]}")
    db_session.add(cat)
    await db_session.flush()

    product = Product(
        name=f"Idempotent Item {uuid.uuid4().hex[:6]}", price=40.0, stock=10, category_id=cat.id
    )
    db_session.add(product)
    await db_session.flush()

    key = uuid.uuid4().hex
    order_in = OrderCreate(
        items=[OrderItemCreate(product_id=product.id, quantity=2)],
        delivery_address="سكن الولاد الداخلي",
        idempotency_key=key,
    )

    first_order = await order_service.create_order(db_session, test_user, order_in)
    second_order = await order_service.create_order(db_session, test_user, order_in)

    assert first_order.id == second_order.id

    await db_session.refresh(product)
    # Stock must be decremented exactly once (quantity=2), not twice.
    assert product.stock == 8


@pytest.mark.asyncio
async def test_different_idempotency_keys_create_separate_orders(db_session, test_user):
    cat = Category(name=f"Idempotency Distinct {uuid.uuid4().hex[:6]}")
    db_session.add(cat)
    await db_session.flush()

    product = Product(
        name=f"Distinct Item {uuid.uuid4().hex[:6]}", price=20.0, stock=10, category_id=cat.id
    )
    db_session.add(product)
    await db_session.flush()

    order_in_1 = OrderCreate(
        items=[OrderItemCreate(product_id=product.id, quantity=1)],
        delivery_address="سكن الولاد الداخلي",
        idempotency_key=uuid.uuid4().hex,
    )
    order_in_2 = OrderCreate(
        items=[OrderItemCreate(product_id=product.id, quantity=1)],
        delivery_address="سكن الولاد الداخلي",
        idempotency_key=uuid.uuid4().hex,
    )

    first_order = await order_service.create_order(db_session, test_user, order_in_1)
    second_order = await order_service.create_order(db_session, test_user, order_in_2)

    assert first_order.id != second_order.id

    await db_session.refresh(product)
    assert product.stock == 8
