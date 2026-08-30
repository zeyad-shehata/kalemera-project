from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from app.config import settings

from sqlalchemy import event

# Normalize database URL for async engines (e.g. postgres:// or postgresql:// to postgresql+asyncpg://)
db_url = settings.DATABASE_URL
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql+asyncpg://", 1)
elif db_url.startswith("postgresql://") and "+asyncpg" not in db_url:
    db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)

# Handle sslmode parameter for asyncpg compatibility
if "postgresql+asyncpg://" in db_url and "sslmode=" in db_url:
    db_url = (
        db_url.replace("sslmode=require", "ssl=require")
        .replace("sslmode=prefer", "ssl=prefer")
        .replace("sslmode=disable", "ssl=disable")
    )

# Create async engine
engine = create_async_engine(db_url, echo=False, future=True)

# Configure SQLite for high concurrency (WAL mode & busy timeout) only when using SQLite
if "sqlite" in db_url.lower():
    @event.listens_for(engine.sync_engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA busy_timeout=5000")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.close()


# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
    class_=AsyncSession,
)


# Declarative base class for SQLAlchemy 2.0
class Base(DeclarativeBase):
    pass


# Dependency to get db session
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
