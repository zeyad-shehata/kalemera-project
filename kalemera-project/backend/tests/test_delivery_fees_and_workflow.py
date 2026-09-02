"""Tests for delivery fees, the admin order workflow buckets, and status transitions."""

import asyncio
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.security import create_access_token


def _headers(user) -> dict:
    return {"Authorization": f"Bearer {create_access_token(user.id, user.role.value)}"}


async def _create_order(client: AsyncClient, user, product, address: str) -> dict:
    resp = await client.post(
        "/api/orders/",
        json={
            "items": [{"product_id": product.id, "quantity": 1}],
            "delivery_address": address,
        },
        headers=_headers(user),
    )
    assert resp.status_code == 201, f"Order creation failed: {resp.text}"
    return resp.json()


@pytest.mark.asyncio
async def test_delivery_fees_per_location(
    client: AsyncClient, test_user, sample_product
):
    """Each delivery location must be charged its configured fee (20/15/25 EGP)."""
    # sample_product price = 120.0, ordered quantity 1 -> subtotal 120.0
    expected = {
        "سكن الولاد الداخلي": (20.0, 140.0),  # 120 subtotal + 20
        "سكن البنات الداخلي": (15.0, 135.0),  # 120 subtotal + 15
        "الحي الراقي": (25.0, 145.0),          # 120 subtotal + 25
    }
    for address, (fee, total) in expected.items():
        order = await _create_order(client, test_user, sample_product, address)
        assert order["delivery_fee"] == fee
        assert order["total_price"] == total
        assert order["items"][0]["subtotal"] == 120.0


@pytest.mark.asyncio
async def test_client_cannot_tamper_delivery_fee(
    client: AsyncClient, test_user, sample_product
):
    """A client-supplied delivery_fee is ignored; the fee comes from the server only."""
    resp = await client.post(
        "/api/orders/",
        json={
            "items": [{"product_id": sample_product.id, "quantity": 1}],
            "delivery_address": "سكن الولاد الداخلي",
            "delivery_fee": 0.0,
            "total_price": 241.0,
        },
        headers=_headers(test_user),
    )
    assert resp.status_code == 201
    order = resp.json()
    assert order["delivery_fee"] == 20.0
    assert order["total_price"] == 140.0  # 120 subtotal + 20 fee


@pytest.mark.asyncio
async def test_workflow_endpoint_is_admin_only(
    client: AsyncClient, test_user, admin_user
):
    """Customers must not see the admin workflow; admins must."""
    customer_resp = await client.get("/api/orders/workflow", headers=_headers(test_user))
    assert customer_resp.status_code == 403

    admin_resp = await client.get("/api/orders/workflow", headers=_headers(admin_user))
    assert admin_resp.status_code == 200
    data = admin_resp.json()
    for bucket in ("new", "preparing", "ready", "delivered", "cancelled"):
        assert bucket in data
    assert data["delivered_total"] == 0


@pytest.mark.asyncio
async def test_workflow_buckets_and_transitions(
    client: AsyncClient, test_user, admin_user, sample_product
):
    """Advancing an order through NEW -> PREPARING -> READY -> DELIVERED must move
    it between the correct workflow buckets, and delivered orders stay in history."""
    order_a = await _create_order(client, test_user, sample_product, "سكن الولاد الداخلي")
    order_b = await _create_order(client, test_user, sample_product, "الحي الراقي")

        # Capture baseline before transition
    baseline = (
        await client.get("/api/orders/workflow", headers=_headers(admin_user))
    ).json()
    delivered_before = baseline["delivered_total"]
    new_ids_before = [o["id"] for o in baseline["new"]]

    # Admin advances order_b all the way to delivered
    for target in ("PROCESSING", "SHIPPED", "DELIVERED"):
        resp = await client.put(
            f"/api/orders/{order_b['id']}/status",
            json={"status": target},
            headers=_headers(admin_user),
        )
        assert resp.status_code == 200, f"Transition to {target} failed: {resp.text}"

    workflow = (
        await client.get("/api/orders/workflow", headers=_headers(admin_user))
    ).json()

    # order_a must still be in the new bucket, order_b must not
    new_ids = [o["id"] for o in workflow["new"]]
    assert order_a["id"] in new_ids
    assert order_b["id"] not in new_ids
    # Delivered history includes order_b
    delivered_ids = [o["id"] for o in workflow["delivered"]]
    assert order_b["id"] in delivered_ids
    assert workflow["delivered_total"] == delivered_before + 1

    # The delivered order still shows its server-calculated fee in history
    assert workflow["delivered"][0]["delivery_fee"] == 25.0
    assert workflow["delivered"][0]["total_price"] == 145.0  # 120 subtotal + 25 fee


@pytest.mark.asyncio
async def test_workflow_fifo_within_new_bucket(
    client: AsyncClient, test_user, admin_user, sample_product
):
    """New orders must be listed FIFO (oldest first) inside the workflow bucket."""
    # Capture baseline
    baseline = (
        await client.get("/api/orders/workflow", headers=_headers(admin_user))
    ).json()
    existing_new_ids = [o["id"] for o in baseline["new"]]

    ids = []
    for _ in range(3):
        order = await _create_order(client, test_user, sample_product, "سكن البنات الداخلي")
        ids.append(order["id"])
        await asyncio.sleep(0.1)

    workflow = (
        await client.get("/api/orders/workflow", headers=_headers(admin_user))
    ).json()

    # Our 3 new orders must appear in FIFO order (by ID) within the new bucket
    all_new_ids = [o["id"] for o in workflow["new"]]
    for our_id in ids:
        assert our_id in all_new_ids
    # Check they appear in the correct relative order
    positions = [all_new_ids.index(oid) for oid in ids]
    assert positions == sorted(positions)


@pytest.mark.asyncio
async def test_workflow_delivered_pagination(
    client: AsyncClient, test_user, admin_user, sample_product
):
    """Delivered history must be paginated via delivered_limit / delivered_offset."""
    # Capture baseline
    baseline = (
        await client.get("/api/orders/workflow", headers=_headers(admin_user))
    ).json()
    delivered_before = baseline["delivered_total"]

    delivered_order_id = (await _create_order(client, test_user, sample_product, "الحي الراقي"))["id"]
    resp = await client.put(
        f"/api/orders/{delivered_order_id}/status",
        json={"status": "DELIVERED"},
        headers=_headers(admin_user),
    )
    assert resp.status_code == 200

    page1 = (
        await client.get(
            "/api/orders/workflow",
            params={"delivered_limit": 1, "delivered_offset": 0},
            headers=_headers(admin_user),
        )
    ).json()
    assert len(page1["delivered"]) == 1
    assert page1["delivered_total"] == delivered_before + 1
    # FIFO: page 1 holds the oldest delivered order
    assert page1["delivered"][0]["status"] == "DELIVERED"

    # Offset=1 skips the first delivered row, so it holds a different order (or none if only one exists)
    page2 = (
        await client.get(
            "/api/orders/workflow",
            params={"delivered_limit": 1, "delivered_offset": 1},
            headers=_headers(admin_user),
        )
    ).json()
    assert len(page2["delivered"]) <= 1
    assert page2["delivered_total"] == delivered_before + 1
    if page2["delivered"]:
        assert page2["delivered"][0]["id"] != page1["delivered"][0]["id"]


@pytest.mark.asyncio
async def test_status_transition_rules(
    client: AsyncClient, test_user, admin_user, sample_product
):
    """Forward transitions are allowed; nonsensical/backward transitions are blocked."""
    order = await _create_order(client, test_user, sample_product, "سكن الولاد الداخلي")
    oid = order["id"]

    # PENDING → PROCESSING → SHIPPED → DELIVERED (happy path)
    for target in ("PROCESSING", "SHIPPED", "DELIVERED"):
        resp = await client.put(
            f"/api/orders/{oid}/status",
            json={"status": target},
            headers=_headers(admin_user),
        )
        assert resp.status_code == 200, f"-> {target} should be allowed: {resp.text}"
        assert resp.json()["status"] == target

    # Once delivered, no further transitions are allowed
    for target in ("PENDING", "PROCESSING", "SHIPPED", "CANCELLED"):
        resp = await client.put(
            f"/api/orders/{oid}/status",
            json={"status": target},
            headers=_headers(admin_user),
        )
        assert resp.status_code == 400, f"DELIVERED -> {target} should be blocked"


@pytest.mark.asyncio
async def test_cancel_from_new_restores_stock(
    client: AsyncClient, test_user, admin_user, sample_product, db_session: AsyncSession
):
    """Cancelling an order from the NEW bucket restores product stock."""
    order = await _create_order(client, test_user, sample_product, "سكن الولاد الداخلي")

    await db_session.refresh(sample_product)
    assert sample_product.stock == 14  # 15 initial - 1 ordered

    resp = await client.put(
        f"/api/orders/{order['id']}/status",
        json={"status": "CANCELLED"},
        headers=_headers(admin_user),
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "CANCELLED"

    await db_session.refresh(sample_product)
    assert sample_product.stock == 15  # restored