import pytest
from httpx import AsyncClient
from app.models import UserRole, FulfillmentType, OrderStatus
from app.security import create_access_token

@pytest.mark.asyncio
async def test_pickup_order_flow(client: AsyncClient, test_user, sample_product):
    """Test that customer can create a pickup order without delivery address and with 0 delivery fee."""
    token = create_access_token(user_id=test_user.id, role=test_user.role)
    
    # Place a PICKUP order
    payload = {
        "items": [
            {
                "product_id": sample_product.id,
                "quantity": 2,
                "variant_id": None
            }
        ],
        "fulfillment_type": "PICKUP"
    }

    order_res = await client.post(
        "/api/orders/",
        json=payload,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert order_res.status_code == 201
    order_data = order_res.json()
    
    # Verify pickup properties
    assert order_data["fulfillment_type"] == "PICKUP"
    assert order_data["delivery_fee"] == 0.0
    assert order_data["delivery_address"] == "استلام من الصالة"
    
    # Total price must exactly match subtotal
    expected_subtotal = sum(item["subtotal"] for item in order_data["items"])
    assert order_data["total_price"] == expected_subtotal


@pytest.mark.asyncio
async def test_delivery_order_address_validation(client: AsyncClient, test_user, sample_product):
    """Test that DELIVERY order strictly requires valid delivery address and calculates fee."""
    token = create_access_token(user_id=test_user.id, role=test_user.role)

    # 1. Delivery order with valid address 'سكن البنات الداخلي' (fee 15.0)
    valid_payload = {
        "items": [{"product_id": sample_product.id, "quantity": 1}],
        "fulfillment_type": "DELIVERY",
        "delivery_address": "سكن البنات الداخلي"
    }
    res = await client.post(
        "/api/orders/",
        json=valid_payload,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 201
    data = res.json()
    assert data["fulfillment_type"] == "DELIVERY"
    assert data["delivery_fee"] == 15.0
    assert data["delivery_address"] == "سكن البنات الداخلي"
    assert data["total_price"] == float(sample_product.price) + 15.0

    # 2. Delivery order without delivery address should be rejected
    invalid_payload = {
        "items": [{"product_id": sample_product.id, "quantity": 1}],
        "fulfillment_type": "DELIVERY",
        "delivery_address": None
    }
    err_res = await client.post(
        "/api/orders/",
        json=invalid_payload,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert err_res.status_code in [400, 422]


@pytest.mark.asyncio
async def test_admin_workflow_exposes_fulfillment(client: AsyncClient, admin_user, test_user, sample_product):
    """Test that admin workflow endpoint correctly returns fulfillment_type for all orders."""
    token = create_access_token(user_id=admin_user.id, role=admin_user.role)
    res = await client.get(
        "/api/orders/workflow",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 200
    workflow = res.json()
    assert "new" in workflow
    assert "preparing" in workflow
    assert "ready" in workflow
    assert "delivered" in workflow
