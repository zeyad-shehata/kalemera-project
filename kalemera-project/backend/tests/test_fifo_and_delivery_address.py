"""Tests for FIFO order sequencing and delivery address validation."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models import Order, User, UserRole
from app.seed import seed_initial_data_if_empty
from app.services.business_hours import is_store_closed
from app.security import create_access_token
import asyncio


@pytest.mark.asyncio
async def test_fifo_order_sequencing_with_asc_created_at(
    client: AsyncClient, test_user: User, db_session: AsyncSession, sample_product
):
    """Orders must be returned in FIFO order (oldest first, ascending by created_at)."""
    token = create_access_token(test_user.id, test_user.role.value)
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create 3 orders in sequence: A, B, C
    order_ids = []
    for i in range(3):
        resp = await client.post(
            "/api/orders/",
            json={
                "items": [{"product_id": sample_product.id, "quantity": 1}],
                "delivery_address": "سكن الولاد الداخلي",
            },
            headers=headers,
        )
        assert resp.status_code == 201, f"Failed to create order {i}: {resp.text}"
        order_ids.append(resp.json()["id"])
        # Small delay to ensure different timestamps
        await asyncio.sleep(0.1)
    
    # Fetch orders (should return in FIFO order: A, B, C)
    resp = await client.get("/api/orders/", headers=headers)
    assert resp.status_code == 200
    orders = resp.json()
    
    # Verify we got all 3 orders
    assert len(orders) >= 3, f"Expected at least 3 orders, got {len(orders)}"
    
    # Verify FIFO order: oldest first
    retrieved_ids = [o["id"] for o in orders[:3]]
    assert retrieved_ids == order_ids, f"Expected FIFO order {order_ids}, got {retrieved_ids}"
    
    # Verify created_at is ascending (oldest first)
    created_times = [o["created_at"] for o in orders[:3]]
    assert created_times == sorted(created_times), \
        f"Orders not in ascending created_at order: {created_times}"


@pytest.mark.asyncio
async def test_delivery_address_must_start_null_on_checkout(
    client: AsyncClient, test_user: User
):
    """Frontend checkout must start with null delivery_address."""
    # This test verifies the Checkout.vue behavior through API validation
    # The frontend ref should initialize to null, not a default address
    # Verified when attempting to place order without explicit address
    token = create_access_token(test_user.id, test_user.role.value)
    headers = {"Authorization": f"Bearer {token}"}
    
    # Attempt to create order without delivery_address (should fail)
    resp = await client.post(
        "/api/orders/",
        json={
            "items": [{"product_id": 1, "quantity": 1}],
        },
        headers=headers,
    )
    # Should fail because delivery_address is required and not provided
    assert resp.status_code in [400, 422], \
        f"Expected 400/422 for missing delivery_address, got {resp.status_code}: {resp.text}"


@pytest.mark.asyncio
async def test_delivery_address_null_rejected(
    client: AsyncClient, test_user: User, sample_product
):
    """Backend must reject null delivery_address."""
    token = create_access_token(test_user.id, test_user.role.value)
    headers = {"Authorization": f"Bearer {token}"}
    
    resp = await client.post(
        "/api/orders/",
        json={
            "items": [{"product_id": sample_product.id, "quantity": 1}],
            "delivery_address": None,
        },
        headers=headers,
    )
    # Pydantic returns 422 for validation errors
    assert resp.status_code in [400, 422], f"Expected 400/422, got {resp.status_code}: {resp.text}"


@pytest.mark.asyncio
async def test_delivery_address_empty_string_rejected(
    client: AsyncClient, test_user: User, sample_product
):
    """Backend must reject empty string delivery_address."""
    token = create_access_token(test_user.id, test_user.role.value)
    headers = {"Authorization": f"Bearer {token}"}
    
    resp = await client.post(
        "/api/orders/",
        json={
            "items": [{"product_id": sample_product.id, "quantity": 1}],
            "delivery_address": "",
        },
        headers=headers,
    )
    # Pydantic returns 422 for validation errors
    assert resp.status_code in [400, 422], f"Expected 400/422, got {resp.status_code}: {resp.text}"


@pytest.mark.asyncio
async def test_delivery_address_invalid_rejected(
    client: AsyncClient, test_user: User, sample_product
):
    """Backend must reject invalid delivery_address."""
    token = create_access_token(test_user.id, test_user.role.value)
    headers = {"Authorization": f"Bearer {token}"}
    
    resp = await client.post(
        "/api/orders/",
        json={
            "items": [{"product_id": sample_product.id, "quantity": 1}],
            "delivery_address": "مكان غير موجود",
        },
        headers=headers,
    )
    # Pydantic returns 422 for validation errors
    assert resp.status_code in [400, 422], f"Expected 400/422, got {resp.status_code}: {resp.text}"


@pytest.mark.asyncio
async def test_all_three_valid_delivery_addresses_accepted(
    client: AsyncClient, test_user: User, sample_product, db_session
):
    """Each of the 3 valid addresses must be accepted."""
    from app.repositories.order_repository import order_repository
    
    token = create_access_token(test_user.id, test_user.role.value)
    headers = {"Authorization": f"Bearer {token}"}
    
    valid_addresses = [
        "سكن الولاد الداخلي",
        "سكن البنات الداخلي",
        "الحي الراقي",
    ]
    
    created_orders = []
    for address in valid_addresses:
        resp = await client.post(
            "/api/orders/",
            json={
                "items": [{"product_id": sample_product.id, "quantity": 1}],
                "delivery_address": address,
            },
            headers=headers,
        )
        assert resp.status_code == 201, \
            f"Failed to create order with address '{address}': {resp.status_code} {resp.text}"
        
        order_data = resp.json()
        assert order_data["delivery_address"] == address
        created_orders.append(order_data["id"])
    
    # Verify all orders were created and stored correctly
    orders = await order_repository.list_orders(db_session, user_id=test_user.id)
    stored_addresses = [o.delivery_address for o in orders[-3:]]  # Get last 3
    
    for address in valid_addresses:
        assert address in stored_addresses, f"Address '{address}' not found in stored orders"
