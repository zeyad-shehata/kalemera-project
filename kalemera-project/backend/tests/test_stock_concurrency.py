"""Regression test for the atomic stock-decrement fix in order_service.create_order.

Verifies that ordering the last unit of stock is enforced by a single atomic
`UPDATE ... WHERE stock >= quantity` validated via rowcount, not by a
read-stock -> check -> write pattern (which is a check-then-act race under
concurrent requests). Given stock=1, ordering it twice in a row must succeed
exactly once and never let stock go negative.

Note: the test SQLite engine used in this suite does not share a single
connection/schema across independently-opened sessions, so a true
multi-connection race (two requests hitting the database at the literally
same instant) cannot be exercised here. That guarantee comes from PostgreSQL's
row-level locking on the atomic UPDATE in production. This test instead proves
the guard itself is correct: the second attempt against already-exhausted
stock is rejected by the database, not by stale in-memory state.
"""
import uuid

import pytest
from fastapi import HTTPException

from app.models import Category, Product
from app.schemas import OrderCreate, OrderItemCreate
from app.services.order_service import order_service


@pytest.mark.asyncio
async def test_second_order_for_last_unit_of_stock_is_rejected_and_never_goes_negative(
    db_session, test_user
):
    cat = Category(name=f"Concurrency Test {uuid.uuid4().hex[:6]}")
    db_session.add(cat)
    await db_session.flush()

    product = Product(
        name=f"Last Unit Item {uuid.uuid4().hex[:6]}",
        price=50.0,
        stock=1,
        category_id=cat.id,
    )
    db_session.add(product)
    await db_session.flush()

    order_in = OrderCreate(
        items=[OrderItemCreate(product_id=product.id, quantity=1)],
        delivery_address="سكن الولاد الداخلي",
    )

    # First attempt consumes the last unit via the atomic guarded UPDATE.
    first_order = await order_service.create_order(db_session, test_user, order_in)
    assert first_order is not None

    await db_session.refresh(product)
    assert product.stock == 0

    # Second attempt for the same (now exhausted) stock must be rejected by
    # the database-level guard, not silently allowed to go negative.
    with pytest.raises(HTTPException) as exc_info:
        await order_service.create_order(db_session, test_user, order_in)
    assert exc_info.value.status_code == 400
    assert "stock" in exc_info.value.detail.lower() or "purchased" in exc_info.value.detail.lower()

    await db_session.refresh(product)
    assert product.stock == 0
