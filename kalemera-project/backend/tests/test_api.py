import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models import User, Category, Product, Order, Notification, UserRole


@pytest.mark.asyncio
async def test_auth_flow(client: AsyncClient, db_session: AsyncSession):
    # 1. Register User
    reg_payload = {
        "phone": "01000000001",
        "password": "testpassword",
        "full_name": "Test User",
    }
    response = await client.post("/api/auth/register", json=reg_payload)
    assert response.status_code == 201
    res_data = response.json()
    assert res_data["phone"] == reg_payload["phone"]
    assert res_data["full_name"] == reg_payload["full_name"]
    assert "id" in res_data

    # 2. Login User
    login_payload = {"phone": reg_payload["phone"], "password": reg_payload["password"]}
    response = await client.post("/api/auth/login", json=login_payload)
    assert response.status_code == 200
    assert "access_token" in response.cookies

    # 3. Get Current User Info
    response = await client.get("/api/auth/me")
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["phone"] == reg_payload["phone"]


@pytest.mark.asyncio
async def test_products_flow(client: AsyncClient, db_session: AsyncSession):
    # Setup: Create Category and Product in DB
    category = Category(name="Electronics")
    db_session.add(category)
    await db_session.flush()

    product = Product(
        name="Laptop Pro",
        description="Premium laptop",
        price=999.99,
        stock=10,
        category_id=category.id,
    )
    db_session.add(product)
    await db_session.commit()

    # Test GET /api/products/
    response = await client.get("/api/products/")
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["total"] == 1
    assert res_data["items"][0]["name"] == "Laptop Pro"


@pytest.mark.asyncio
async def test_orders_flow(client: AsyncClient, db_session: AsyncSession):
    # Setup: Create User, Category, and Product in DB
    from app.security import get_password_hash

    user = User(
        phone="01000000002",
        hashed_password=get_password_hash("buyerpass"),
        full_name="Buyer User",
        role=UserRole.CUSTOMER,
    )
    category = Category(name="Fashion")
    db_session.add_all([user, category])
    await db_session.flush()

    product = Product(
        name="Winter Coat",
        description="Warm winter coat",
        price=120.00,
        stock=5,
        category_id=category.id,
    )
    db_session.add(product)
    await db_session.commit()

    # Log in as buyer
    login_response = await client.post(
        "/api/auth/login", json={"phone": "01000000002", "password": "buyerpass"}
    )
    assert login_response.status_code == 200

    # Place an Order
    order_payload = {"items": [{"product_id": product.id, "quantity": 2}]}
    response = await client.post("/api/orders/", json=order_payload)
    assert response.status_code == 201
    order_data = response.json()
    assert order_data["total_price"] == 240.00
    assert order_data["status"] == "PENDING"

    # Verify product stock was reduced
    await db_session.refresh(product)
    assert product.stock == 3

    # Verify notification was generated for the buyer
    notif_result = await db_session.execute(
        select(Notification).where(Notification.user_id == user.id)
    )
    notifications = notif_result.scalars().all()
    assert len(notifications) == 1
    assert "successfully" in notifications[0].message
    assert "EGP" in notifications[0].message


@pytest.mark.asyncio
async def test_cancel_order_flow(client: AsyncClient, db_session: AsyncSession):
    from app.security import get_password_hash

    user = User(
        phone="01000000003",
        hashed_password=get_password_hash("cancelpass"),
        full_name="Canceller",
        role=UserRole.CUSTOMER,
    )
    category = Category(name="Outdoor")
    db_session.add_all([user, category])
    await db_session.flush()

    product = Product(
        name="Tent",
        description="Camping tent",
        price=80.00,
        stock=5,
        category_id=category.id,
    )
    db_session.add(product)
    await db_session.commit()

    login_response = await client.post(
        "/api/auth/login",
        json={"phone": "01000000003", "password": "cancelpass"},
    )
    assert login_response.status_code == 200

    # Place an order for 2 units
    order_response = await client.post(
        "/api/orders/", json={"items": [{"product_id": product.id, "quantity": 2}]}
    )
    assert order_response.status_code == 201
    order_id = order_response.json()["id"]

    await db_session.refresh(product)
    assert product.stock == 3

    # Customer cancels their own pending order
    cancel_response = await client.post(f"/api/orders/{order_id}/cancel")
    assert cancel_response.status_code == 200
    assert cancel_response.json()["status"] == "CANCELLED"

    # Stock must be restored
    await db_session.refresh(product)
    assert product.stock == 5

    # Cancel again -> not pending anymore -> 400
    second_cancel = await client.post(f"/api/orders/{order_id}/cancel")
    assert second_cancel.status_code == 400


@pytest.mark.asyncio
async def test_customer_cannot_cancel_others_order(
    client: AsyncClient, db_session: AsyncSession
):
    from app.security import get_password_hash

    owner = User(
        phone="01000000004",
        hashed_password=get_password_hash("ownerpass"),
        full_name="Owner",
        role=UserRole.CUSTOMER,
    )
    other = User(
        phone="01000000005",
        hashed_password=get_password_hash("otherpass"),
        full_name="Other",
        role=UserRole.CUSTOMER,
    )
    category = Category(name="Garden")
    db_session.add_all([owner, other, category])
    await db_session.flush()

    product = Product(
        name="Shovel",
        description="Garden shovel",
        price=15.00,
        stock=4,
        category_id=category.id,
    )
    db_session.add(product)
    await db_session.commit()

    # Owner places an order
    await client.post(
        "/api/auth/login", json={"phone": "01000000004", "password": "ownerpass"}
    )
    order_response = await client.post(
        "/api/orders/", json={"items": [{"product_id": product.id, "quantity": 1}]}
    )
    assert order_response.status_code == 201
    order_id = order_response.json()["id"]

    # Another customer tries to cancel it -> 403
    await client.post("/api/auth/logout")
    await client.post(
        "/api/auth/login", json={"phone": "01000000005", "password": "otherpass"}
    )
    cancel_response = await client.post(f"/api/orders/{order_id}/cancel")
    assert cancel_response.status_code == 403


@pytest.mark.asyncio
async def test_admin_cancel_restores_stock(
    client: AsyncClient, db_session: AsyncSession
):
    from app.security import get_password_hash

    admin = User(
        phone="01000000006",
        hashed_password=get_password_hash("adminpass"),
        full_name="Admin",
        role=UserRole.ADMIN,
    )
    customer = User(
        phone="01000000007",
        hashed_password=get_password_hash("custpass"),
        full_name="Customer",
        role=UserRole.CUSTOMER,
    )
    category = Category(name="Tools")
    db_session.add_all([admin, customer, category])
    await db_session.flush()

    product = Product(
        name="Hammer",
        description="Claw hammer",
        price=12.00,
        stock=6,
        category_id=category.id,
    )
    db_session.add(product)
    await db_session.commit()

    # Customer places order for 3 units
    await client.post(
        "/api/auth/login",
        json={"phone": "01000000007", "password": "custpass"},
    )
    order_response = await client.post(
        "/api/orders/", json={"items": [{"product_id": product.id, "quantity": 3}]}
    )
    assert order_response.status_code == 201
    order_id = order_response.json()["id"]

    await db_session.refresh(product)
    assert product.stock == 3

    # Admin logs in and cancels the order via status update
    await client.post("/api/auth/logout")
    await client.post(
        "/api/auth/login",
        json={"phone": "01000000006", "password": "adminpass"},
    )
    status_response = await client.put(
        f"/api/orders/{order_id}/status", json={"status": "CANCELLED"}
    )
    assert status_response.status_code == 200

    await db_session.refresh(product)
    assert product.stock == 6


@pytest.mark.asyncio
async def test_cannot_delete_product_referenced_in_order(
    client: AsyncClient, db_session: AsyncSession
):
    from app.security import get_password_hash

    admin = User(
        phone="01000000008",
        hashed_password=get_password_hash("adminpass"),
        full_name="Admin",
        role=UserRole.ADMIN,
    )
    customer = User(
        phone="01000000009",
        hashed_password=get_password_hash("custpass"),
        full_name="Customer",
        role=UserRole.CUSTOMER,
    )
    category = Category(name="Books")
    db_session.add_all([admin, customer, category])
    await db_session.flush()

    product = Product(
        name="Novel",
        description="A great book",
        price=10.00,
        stock=2,
        category_id=category.id,
    )
    db_session.add(product)
    await db_session.commit()

    # Customer buys it so it becomes referenced in an order
    await client.post(
        "/api/auth/login",
        json={"phone": "01000000009", "password": "custpass"},
    )
    order_response = await client.post(
        "/api/orders/", json={"items": [{"product_id": product.id, "quantity": 1}]}
    )
    assert order_response.status_code == 201

    # Admin tries to delete the product -> must be rejected with 400, not 500
    await client.post("/api/auth/logout")
    await client.post(
        "/api/auth/login",
        json={"phone": "01000000008", "password": "adminpass"},
    )
    delete_response = await client.delete(f"/api/products/{product.id}")
    assert delete_response.status_code == 400


@pytest.mark.asyncio
async def test_cannot_delete_category_with_ordered_products(
    client: AsyncClient, db_session: AsyncSession
):
    from app.security import get_password_hash

    admin = User(
        phone="01000000010",
        hashed_password=get_password_hash("adminpass"),
        full_name="Admin",
        role=UserRole.ADMIN,
    )
    customer = User(
        phone="01000000011",
        hashed_password=get_password_hash("custpass"),
        full_name="Customer",
        role=UserRole.CUSTOMER,
    )
    category = Category(name="Sports")
    db_session.add_all([admin, customer, category])
    await db_session.flush()

    product = Product(
        name="Football",
        description="Round ball",
        price=20.00,
        stock=3,
        category_id=category.id,
    )
    db_session.add(product)
    await db_session.commit()

    # Customer buys it
    await client.post(
        "/api/auth/login", json={"phone": "01000000011", "password": "custpass"}
    )
    order_response = await client.post(
        "/api/orders/", json={"items": [{"product_id": product.id, "quantity": 1}]}
    )
    assert order_response.status_code == 201

    # Admin tries to delete the category -> must be rejected with 400, not 500
    await client.post("/api/auth/logout")
    await client.post(
        "/api/auth/login",
        json={"phone": "01000000010", "password": "adminpass"},
    )
    delete_response = await client.delete(f"/api/categories/{category.id}")
    assert delete_response.status_code == 400


@pytest.mark.asyncio
async def test_product_form_validation(client: AsyncClient, db_session: AsyncSession):
    from app.security import get_password_hash

    admin = User(
        phone="01000000012",
        hashed_password=get_password_hash("adminpass"),
        full_name="Admin",
        role=UserRole.ADMIN,
    )
    category = Category(name="Misc")
    db_session.add_all([admin, category])
    await db_session.commit()

    await client.post(
        "/api/auth/login",
        json={"phone": "01000000012", "password": "adminpass"},
    )

    # Negative price -> 400
    bad_price = await client.post(
        "/api/products/",
        data={
            "name": "Bad Price",
            "price": "-5",
            "stock": "1",
            "category_id": str(category.id),
        },
    )
    assert bad_price.status_code == 400

    # Negative stock -> 400
    bad_stock = await client.post(
        "/api/products/",
        data={
            "name": "Bad Stock",
            "price": "5",
            "stock": "-1",
            "category_id": str(category.id),
        },
    )
    assert bad_stock.status_code == 400

    # Whitespace-only name -> 400 (empty strings are rejected with 422 by FastAPI)
    bad_name = await client.post(
        "/api/products/",
        data={
            "name": "   ",
            "price": "5",
            "stock": "1",
            "category_id": str(category.id),
        },
    )
    assert bad_name.status_code == 400
