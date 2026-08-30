from typing import AsyncGenerator
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.database import Base, get_db

# Test database URL (Async SQLite in-memory)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Create async engine for tests
test_engine = create_async_engine(
    TEST_DATABASE_URL, connect_args={"check_same_thread": False}
)

# Create async session factory for tests
TestingSessionLocal = async_sessionmaker(
    bind=test_engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
    class_=AsyncSession,
)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_test_db():
    """Create the database tables and drop them after tests complete."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provides a fresh database session for a test, rolled back afterwards."""
    async with TestingSessionLocal() as session:
        try:
            yield session
        finally:
            await session.rollback()
            await session.close()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Provides an AsyncClient bound to the FastAPI app with overridden DB dependency."""

    async def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as async_client:
        yield async_client

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession):
    import uuid
    from app.models import User, UserRole
    from app.security import get_password_hash
    phone = f"010{uuid.uuid4().int % 100000000:08d}"
    user = User(
        phone=phone,
        hashed_password=get_password_hash("password123"),
        full_name="Customer User",
        role=UserRole.CUSTOMER
    )
    db_session.add(user)
    await db_session.flush()
    return user


@pytest_asyncio.fixture
async def admin_user(db_session: AsyncSession):
    import uuid
    from app.models import User, UserRole
    from app.security import get_password_hash
    phone = f"011{uuid.uuid4().int % 100000000:08d}"
    admin = User(
        phone=phone,
        hashed_password=get_password_hash("adminpass123"),
        full_name="Admin User",
        role=UserRole.ADMIN
    )
    db_session.add(admin)
    await db_session.flush()
    return admin


@pytest_asyncio.fixture
async def sample_product(db_session: AsyncSession):
    import uuid
    from app.models import Category, Product
    cat_name = f"Test Fast Food {uuid.uuid4().hex[:6]}"
    cat = Category(name=cat_name)
    db_session.add(cat)
    await db_session.flush()

    prod = Product(
        name=f"Burger Supreme {uuid.uuid4().hex[:4]}",
        name_en="Supreme Burger",
        description="Juicy burger",
        price=120.0,
        stock=15,
        category_id=cat.id
    )
    db_session.add(prod)
    await db_session.flush()
    return prod
