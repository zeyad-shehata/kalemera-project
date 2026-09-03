import datetime
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models import Order, OrderStatus, User, UserRole
from app.security import create_access_token


@pytest.mark.asyncio
async def test_order_notes_persistence_and_admin_view(
    client: AsyncClient, test_user: User, admin_user: User, sample_product, db_session: AsyncSession
):
    """Customer can create an order with notes, and both customer and admin can view the note."""
    customer_token = create_access_token(test_user.id, test_user.role.value)
    admin_token = create_access_token(admin_user.id, admin_user.role.value)

    note_text = "البرجر من غير طماطم ومن غير مخلل"
    resp = await client.post(
        "/api/orders/",
        json={
            "items": [{"product_id": sample_product.id, "quantity": 1}],
            "fulfillment_type": "PICKUP",
            "notes": note_text,
        },
        headers={"Authorization": f"Bearer {customer_token}"},
    )
    assert resp.status_code == 201
    order_data = resp.json()
    assert order_data["notes"] == note_text
    order_id = order_data["id"]

    # Verify directly in database session
    result = await db_session.execute(select(Order).where(Order.id == order_id))
    persisted_order = result.scalar_one()
    assert persisted_order.notes == note_text

    # Verify customer my-orders response
    customer_orders_resp = await client.get(
        "/api/orders/",
        headers={"Authorization": f"Bearer {customer_token}"},
    )
    assert customer_orders_resp.status_code == 200
    my_orders = customer_orders_resp.json()
    matched = [o for o in my_orders if o["id"] == order_id]
    assert len(matched) == 1
    assert matched[0]["notes"] == note_text

    # Verify admin workflow endpoint includes notes
    admin_workflow_resp = await client.get(
        "/api/orders/workflow",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert admin_workflow_resp.status_code == 200
    workflow = admin_workflow_resp.json()
    new_orders = workflow["new"]
    admin_matched = [o for o in new_orders if o["id"] == order_id]
    assert len(admin_matched) == 1
    assert admin_matched[0]["notes"] == note_text


@pytest.mark.asyncio
async def test_10_minute_cancellation_policy(
    client: AsyncClient, test_user: User, admin_user: User, sample_product, db_session: AsyncSession
):
    """Order within 10 minutes can be cancelled by customer; order older than 10 minutes is rejected."""
    customer_token = create_access_token(test_user.id, test_user.role.value)

    # 1. Create order A (fresh, within 10 minutes)
    resp_a = await client.post(
        "/api/orders/",
        json={
            "items": [{"product_id": sample_product.id, "quantity": 1}],
            "fulfillment_type": "DELIVERY",
            "delivery_address": "سكن الولاد الداخلي",
        },
        headers={"Authorization": f"Bearer {customer_token}"},
    )
    assert resp_a.status_code == 201
    order_a_id = resp_a.json()["id"]

    # Cancel order A within 10 min window -> should succeed
    cancel_a_resp = await client.post(
        f"/api/orders/{order_a_id}/cancel",
        headers={"Authorization": f"Bearer {customer_token}"},
    )
    assert cancel_a_resp.status_code == 200
    assert cancel_a_resp.json()["status"] == OrderStatus.CANCELLED.value

    # 2. Create order B and artificially age it past 10 minutes (e.g. 11 minutes ago)
    resp_b = await client.post(
        "/api/orders/",
        json={
            "items": [{"product_id": sample_product.id, "quantity": 1}],
            "fulfillment_type": "DELIVERY",
            "delivery_address": "سكن الولاد الداخلي",
        },
        headers={"Authorization": f"Bearer {customer_token}"},
    )
    assert resp_b.status_code == 201
    order_b_id = resp_b.json()["id"]

    # Age order B by updating created_at in DB
    result_b = await db_session.execute(select(Order).where(Order.id == order_b_id))
    order_b = result_b.scalar_one()
    order_b.created_at = datetime.datetime.utcnow() - datetime.timedelta(minutes=11)
    await db_session.commit()

    # Attempt cancellation by customer -> MUST BE REJECTED with 400
    cancel_b_resp = await client.post(
        f"/api/orders/{order_b_id}/cancel",
        headers={"Authorization": f"Bearer {customer_token}"},
    )
    assert cancel_b_resp.status_code == 400
    assert "10 دقائق" in cancel_b_resp.json()["detail"]
