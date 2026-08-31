"""Tests for the order deletion mechanism and the additive schema migration.

Covers:
  * order creation persists delivery_address (Problem 1 sanity check)
  * the idempotent additive schema migration adds/keeps divergent columns
  * admin-only hard-delete of orders (restores stock, removes items)
  * deletion affects the dashboard sales total (Problem 2)
"""
from unittest.mock import patch

import pytest
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models import Order, User, Product
from app.security import create_access_token
from app.services.schema_migration import migrate_schema, _table_exists


def _customer_headers(user: User) -> dict:
    return {"Authorization": f"Bearer {create_access_token(user.id, user.role.value)}"}


def _admin_token(admin: User) -> str:
    return create_access_token(admin.id, admin.role.value)


async def _create_order(client, user, product, address="سكن الولاد الداخلي", quantity=1):
    headers = {"Authorization": f"Bearer {create_access_token(user.id, user.role.value)}"}
    with patch(
        "app.services.order_service.is_store_closed",
        return_value=False,
    ):
        resp = await client.post(
            "/api/orders/",
            json={
                "items": [{"product_id": product.id, "quantity": quantity}],
                "delivery_address": address,
            },
            headers=headers,
        )
    assert resp.status_code in (200, 201), resp.text
    return resp


@pytest.mark.asyncio
async def test_order_creation_persists_delivery_address(
    client: AsyncClient, test_user: User, sample_product: Product
):
    """Checkout persists the delivery_address (the column used in Problem 1)."""
    resp = await _create_order(client, test_user, sample_product)
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["delivery_address"] == "سكن الولاد الداخلي"
    assert data["id"] is not None


@pytest.mark.asyncio
async def test_schema_migration_is_idempotent_and_adds_missing_columns(db_session: AsyncSession):
    """migrate_schema simulates the production gap: an existing table missing the
    newly-added delivery_address column is altered in place, and re-running is safe.
    """
    if not await _table_exists(db_session, "orders"):
        pytest.skip("orders table not present")

    # Simulate the production schema drift: drop the column that a legacy table
    # would not have (this is exactly the Problem 1 scenario).
    await db_session.execute(text("ALTER TABLE orders DROP COLUMN delivery_address"))
    await db_session.commit()

    # First run: must add delivery_address back (like the production repair).
    first = await migrate_schema(db_session)
    assert "orders" in first
    assert "delivery_address" in first["orders"]

    # Column now physically present.
    res = await db_session.execute(text("PRAGMA table_info(orders)"))
    cols = {row[1] for row in res.fetchall()}
    assert "delivery_address" in cols

    # Second run: idempotent, nothing more to add, no error.
    second = await migrate_schema(db_session)
    assert "orders" not in second

    # order_items must have its snapshot columns.
    res = await db_session.execute(text("PRAGMA table_info(order_items)"))
    cols = {row[1] for row in res.fetchall()}
    for col in (
        "product_name_snapshot",
        "product_name_en_snapshot",
        "variant_id",
        "variant_name_snapshot",
        "price_snapshot",
        "subtotal",
    ):
        assert col in cols, f"order_items missing {col}"


@pytest.mark.asyncio
async def test_admin_only_delete_removes_order(
    client: AsyncClient, admin_user: User, test_user: User, sample_product: Product, db_session: AsyncSession
):
    """ADMIN can hard-delete an order; items are removed and stock restored."""
    create_resp = await _create_order(client, test_user, sample_product, quantity=2)
    order_id = create_resp.json()["id"]

    # stock was deducted on order creation
    result = await db_session.execute(select(Product).where(Product.id == sample_product.id))
    product_after_order = result.scalars().first()
    assert product_after_order.stock == 13

    resp = await client.delete(f"/api/orders/{order_id}", headers=_customer_headers(admin_user))
    assert resp.status_code == 204

    # order gone
    result = await db_session.execute(select(Order).where(Order.id == order_id))
    assert result.scalars().first() is None

    # stock restored
    result = await db_session.execute(select(Product).where(Product.id == sample_product.id))
    product_restored = result.scalars().first()
    assert product_restored.stock == 15


@pytest.mark.asyncio
async def test_customer_cannot_delete_order(
    client: AsyncClient, test_user: User, sample_product: Product, db_session: AsyncSession
):
    """Normal customers are blocked from hard-deleting orders."""
    order_user = test_user
    create_resp = await _create_order(client, order_user, sample_product)
    order_id = create_resp.json()["id"]

    resp = await client.delete(f"/api/orders/{order_id}", headers=_customer_headers(order_user))
    assert resp.status_code == 403

    # still exists
    result = await db_session.execute(select(Order).where(Order.id == order_id))
    assert result.scalars().first() is not None


@pytest.mark.asyncio
async def test_delete_order_affects_dashboard_total(
    client: AsyncClient, admin_user: User, test_user: User, sample_product: Product, db_session: AsyncSession
):
    """Deleting an order removes it from the dashboard sales total (Problem 2)."""
    create_resp = await _create_order(client, test_user, sample_product, quantity=1)
    order_id = create_resp.json()["id"]

    headers = _customer_headers(admin_user)
    before = await client.get("/api/reports/dashboard", headers=headers)
    assert before.status_code == 200
    sum_before = before.json().get("totalSales") or before.json().get("total_sales")

    await client.delete(f"/api/orders/{order_id}", headers=headers)

    after = await client.get("/api/reports/dashboard", headers=headers)
    assert after.status_code == 200
    sum_after = after.json().get("totalSales") or after.json().get("total_sales")
    assert sum_after < sum_before


@pytest.mark.asyncio
async def test_deleting_missing_order_returns_404(
    client: AsyncClient, admin_user: User
):
    resp = await client.delete("/api/orders/999999", headers=_customer_headers(admin_user))
    assert resp.status_code == 404
