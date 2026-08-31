import datetime
from unittest.mock import patch
from zoneinfo import ZoneInfo

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models import User, UserRole, Category
from app.seed import seed_initial_data_if_empty
from app.services.business_hours import is_store_closed


@pytest.mark.asyncio
async def test_seed_creates_new_categories(db_session: AsyncSession):
    """The two new menu categories must be seeded exactly once."""
    await seed_initial_data_if_empty(db_session)
    result = await db_session.execute(
        select(Category).where(Category.name.in_(["الخضار والفاكهة", "العروض"]))
    )
    cats = result.scalars().all()
    names = {c.name for c in cats}
    assert "الخضار والفاكهة" in names
    assert "العروض" in names
    # No duplicates by unique constraint
    result2 = await db_session.execute(
        select(Category).where(Category.name == "الخضار والفاكهة")
    )
    assert len(result2.scalars().all()) == 1


@pytest.mark.asyncio
async def test_seed_creates_admin_account(db_session: AsyncSession):
    """The primary admin account (01055103802) must exist exactly once as ADMIN."""
    await seed_initial_data_if_empty(db_session)
    result = await db_session.execute(select(User).where(User.phone == "01055103802"))
    admins = result.scalars().all()
    assert len(admins) == 1
    assert admins[0].role == UserRole.ADMIN
    # Password must be hashed, never stored in plain text
    assert admins[0].hashed_password != "baraa321"
    assert admins[0].hashed_password.startswith("$2")


@pytest.mark.asyncio
async def test_admin_login(db_session: AsyncSession, client: AsyncClient):
    """The seeded admin can log in with the configured credentials."""
    await seed_initial_data_if_empty(db_session)
    resp = await client.post(
        "/api/auth/login",
        json={"phone": "01055103802", "password": "baraa321"},
    )
    assert resp.status_code == 200
    me = await client.get("/api/auth/me")
    assert me.status_code == 200
    assert me.json()["role"] == "ADMIN"


@pytest.mark.asyncio
async def test_customer_cannot_access_admin_routes(client: AsyncClient, test_user: User):
    """Normal customers are blocked from admin-only endpoints."""
    resp = await client.post(
        "/api/auth/login",
        json={"phone": test_user.phone, "password": "password123"},
    )
    assert resp.status_code == 200

    blocked = await client.get("/api/reports/dashboard")
    assert blocked.status_code == 403

    blocked2 = await client.get("/api/storage/overview")
    assert blocked2.status_code == 403


@pytest.mark.asyncio
async def test_business_hours_endpoint(client: AsyncClient):
    """GET /api/business-hours exposes server-time open/closed state."""
    resp = await client.get("/api/business-hours")
    assert resp.status_code == 200
    data = resp.json()
    assert "closed" in data
    assert data["timezone"] == "Africa/Cairo"


def test_business_hours_logic_blocks_after_23():
    """After 23:00 Africa/Cairo the store is closed."""
    cairo = ZoneInfo("Africa/Cairo")
    closed_time = datetime.datetime(2026, 8, 31, 23, 30, tzinfo=cairo)
    with patch(
        "app.services.business_hours.now_in_business_timezone",
        return_value=closed_time,
    ):
        assert is_store_closed() is True

    open_time = datetime.datetime(2026, 8, 31, 12, 0, tzinfo=cairo)
    with patch(
        "app.services.business_hours.now_in_business_timezone",
        return_value=open_time,
    ):
        assert is_store_closed() is False

    # Exactly at 23:00 it is already closed
    boundary = datetime.datetime(2026, 8, 31, 23, 0, tzinfo=cairo)
    with patch(
        "app.services.business_hours.now_in_business_timezone",
        return_value=boundary,
    ):
        assert is_store_closed() is True


@pytest.mark.asyncio
async def test_order_blocked_when_closed(client: AsyncClient, test_user: User, sample_product):
    """Order submission must be rejected with 403 + Arabic message when closed."""
    from app.security import create_access_token
    headers = {"Authorization": f"Bearer {create_access_token(test_user.id, test_user.role.value)}"}

    cairo = ZoneInfo("Africa/Cairo")
    closed_time = datetime.datetime(2026, 8, 31, 23, 45, tzinfo=cairo)
    with patch(
        "app.services.order_service.is_store_closed",
        return_value=True,
    ):
        resp = await client.post(
            "/api/orders/",
            json={
                "items": [{"product_id": sample_product.id, "quantity": 1}],
                "delivery_address": "سكن الولاد الداخلي",
            },
            headers=headers,
        )
    assert resp.status_code == 403
    assert resp.json()["detail"] == "المكان خارج ساعات العمل"
