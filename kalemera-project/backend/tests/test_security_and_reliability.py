import io
import os
import shutil
import sqlite3
import pytest
from httpx import AsyncClient
from PIL import Image

from app.main import app
from app.models import User, UserRole, Product, OrderStatus
from app.security import create_access_token
from app.services.backup_service import backup_service
from app.services.image_service import image_service

@pytest.mark.asyncio
async def test_authorization_customer_blocked_from_admin_endpoints(client: AsyncClient, test_user: User, sample_product: Product):
    """Verify customer role cannot access any admin-restricted endpoints."""
    token = create_access_token(test_user.id, test_user.role.value)
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Product creation
    resp = await client.post("/api/products/", data={"name": "Hacked", "price": 10, "stock": 5, "category_id": sample_product.category_id}, headers=headers)
    assert resp.status_code == 403, f"Expected 403 Forbidden, got {resp.status_code}"

    # 2. Product deletion
    resp = await client.delete(f"/api/products/{sample_product.id}", headers=headers)
    assert resp.status_code == 403

    # 3. Category creation
    resp = await client.post("/api/categories/", json={"name": "Hacked Category"}, headers=headers)
    assert resp.status_code == 403

    # 4. Reports dashboard
    resp = await client.get("/api/reports/dashboard", headers=headers)
    assert resp.status_code == 403

    # 5. Reports sales
    resp = await client.get("/api/reports/sales?start_date=2026-01-01&end_date=2026-12-31", headers=headers)
    assert resp.status_code == 403

    # 6. Order status update
    resp = await client.put("/api/orders/1/status", json={"status": "completed"}, headers=headers)
    assert resp.status_code == 403

    # 7. Push notification
    resp = await client.post("/api/notifications/", json={"user_id": test_user.id, "message": "Spam"}, headers=headers)
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_idor_protection_orders_and_notifications(client: AsyncClient, test_user: User, admin_user: User, sample_product: Product):
    """Verify users cannot access other users' orders or notifications."""
    # Create token for customer A
    token_a = create_access_token(test_user.id, test_user.role.value)
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # Admin creates order for itself (User B)
    token_admin = create_access_token(admin_user.id, admin_user.role.value)
    headers_admin = {"Authorization": f"Bearer {token_admin}"}

    order_resp = await client.post(
        "/api/orders/",
        json={"items": [{"product_id": sample_product.id, "quantity": 1}]},
        headers=headers_admin
    )
    assert order_resp.status_code == 201
    admin_order_id = order_resp.json()["id"]

    # Customer A tries to access Admin's order
    resp = await client.get(f"/api/orders/{admin_order_id}", headers=headers_a)
    assert resp.status_code == 403, "Customer A accessed Admin's order without permission (IDOR vulnerability)!"

    # Customer A tries to cancel Admin's order
    resp = await client.post(f"/api/orders/{admin_order_id}/cancel", headers=headers_a)
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_price_tampering_defense(client: AsyncClient, test_user: User, sample_product: Product):
    """Verify that client-supplied prices/subtotals are completely ignored."""
    token = create_access_token(test_user.id, test_user.role.value)
    headers = {"Authorization": f"Bearer {token}"}

    # Attempt to tamper: send price=0.01, subtotal=0.01 in order payload
    tampered_payload = {
        "items": [
            {
                "product_id": sample_product.id,
                "quantity": 2,
                "price": 0.01,
                "subtotal": 0.02,
                "total_price": 0.02
            }
        ]
    }
    resp = await client.post("/api/orders/", json=tampered_payload, headers=headers)
    assert resp.status_code == 201
    created_order = resp.json()
    
    # Verify calculated price matches database authoritative price (product price 120.0 * 2 = 240.0)
    assert created_order["total_price"] == 240.0, "Server accepted tampered price!"
    assert created_order["items"][0]["subtotal"] == 240.0


@pytest.mark.asyncio
async def test_input_validation_and_bounds(client: AsyncClient, test_user: User, sample_product: Product):
    """Verify Pydantic input validation blocks invalid numbers, empty payloads, and bad formats."""
    token = create_access_token(test_user.id, test_user.role.value)
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Negative quantity
    resp = await client.post("/api/orders/", json={"items": [{"product_id": sample_product.id, "quantity": -5}]}, headers=headers)
    assert resp.status_code == 422

    # 2. Zero quantity
    resp = await client.post("/api/orders/", json={"items": [{"product_id": sample_product.id, "quantity": 0}]}, headers=headers)
    assert resp.status_code == 422

    # 3. Excessive quantity (> 100 limit)
    resp = await client.post("/api/orders/", json={"items": [{"product_id": sample_product.id, "quantity": 5000}]}, headers=headers)
    assert resp.status_code == 422

    # 4. Invalid Egyptian phone format
    resp = await client.post("/api/auth/register", json={"phone": "123456", "full_name": "Test User", "password": "password123"})
    assert resp.status_code == 422

    # 5. Invalid Egyptian phone starting with wrong prefix
    resp = await client.post("/api/auth/register", json={"phone": "02123456789", "full_name": "Test User", "password": "password123"})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_sqli_and_xss_safety(client: AsyncClient):
    """Verify SQL injection payloads and XSS payloads are handled safely without crashing."""
    sqli_payloads = [
        "' OR '1'='1",
        "'; DROP TABLE products; --",
        "1' UNION SELECT null, null, null--",
        "admin'--",
    ]

    for payload in sqli_payloads:
        # Search endpoint
        resp = await client.get(f"/api/products/?search={payload}")
        assert resp.status_code == 200, f"Search failed on SQLi payload: {payload}"
        assert isinstance(resp.json()["items"], list)

    xss_payload = "<script>alert('xss')</script>"
    resp = await client.get(f"/api/products/?search={xss_payload}")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_file_upload_security(client: AsyncClient, admin_user: User, sample_product: Product):
    """Verify malicious or corrupted uploads are rejected."""
    token = create_access_token(admin_user.id, admin_user.role.value)
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Fake text file disguised as image
    fake_img = io.BytesIO(b"Not a real image file content")
    resp = await client.post(
        "/api/products/",
        data={"name": "Fake Image Product", "price": 50, "stock": 10, "category_id": sample_product.category_id},
        files={"image": ("malicious.jpg", fake_img, "image/jpeg")},
        headers=headers
    )
    assert resp.status_code == 400
    assert "Invalid or corrupted image" in resp.json()["detail"]

    # 2. Unsupported format (e.g. SVG script injection)
    svg_bytes = io.BytesIO(b"<svg xmlns='http://www.w3.org/2000/svg'><script>alert(1)</script></svg>")
    resp = await client.post(
        "/api/products/",
        data={"name": "SVG Product", "price": 50, "stock": 10, "category_id": sample_product.category_id},
        files={"image": ("vector.svg", svg_bytes, "image/svg+xml")},
        headers=headers
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_session_token_tampering(client: AsyncClient):
    """Verify tampered or invalid JWT tokens are strictly rejected."""
    headers = {"Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid.signature"}
    resp = await client.get("/api/auth/me", headers=headers)
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_database_backup_and_restore_verification():
    """Live test of atomic SQLite backup and temporary restoration."""
    # 1. Trigger backup
    backup_info = backup_service.create_backup()
    backup_file = backup_info["path"]
    assert os.path.exists(backup_file), "Backup file was not created!"
    assert os.path.getsize(backup_file) > 0, "Backup file is empty!"

    # 2. Restore into an isolated scratch database
    scratch_restore_db = "storage/temp/test_restore_verify.db"
    if os.path.exists(scratch_restore_db):
        os.remove(scratch_restore_db)

    shutil.copyfile(backup_file, scratch_restore_db)

    # 3. Verify SQLite integrity on restored database
    conn = sqlite3.connect(scratch_restore_db)
    cursor = conn.cursor()
    cursor.execute("PRAGMA integrity_check;")
    res = cursor.fetchone()
    assert res[0] == "ok", f"Restored DB integrity check failed: {res}"

    cursor.execute("PRAGMA foreign_key_check;")
    fk_res = cursor.fetchall()
    assert len(fk_res) == 0, f"Restored DB has foreign key violations: {fk_res}"

    # Verify tables and rows exist
    cursor.execute("SELECT COUNT(*) FROM products;")
    p_count = cursor.fetchone()[0]
    assert p_count > 0, "Restored database has no products!"

    cursor.execute("SELECT COUNT(*) FROM users;")
    u_count = cursor.fetchone()[0]
    assert u_count > 0, "Restored database has no users!"

    conn.close()

    # Clean up scratch test database
    if os.path.exists(scratch_restore_db):
        os.remove(scratch_restore_db)
