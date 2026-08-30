import logging
import urllib.parse
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import event

from app.config import settings

logger = logging.getLogger("kalemera.database")


def prepare_database_connection(raw_url: str):
    """Normalizes database connection string and prepares connect_args for asyncpg/sqlite.
    Handles Neon / cloud PostgreSQL URLs containing incompatible query parameters (sslmode, channel_binding, etc.).
    """
    connect_args = {}

    # Convert standard postgres schemes to asyncpg
    if raw_url.startswith("postgres://"):
        raw_url = raw_url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif raw_url.startswith("postgresql://") and "+asyncpg" not in raw_url:
        raw_url = raw_url.replace("postgresql://", "postgresql+asyncpg://", 1)

    parsed = urllib.parse.urlparse(raw_url)

    if "postgresql+asyncpg" in parsed.scheme:
        # Extract and clean query parameters for asyncpg
        query_params = urllib.parse.parse_qs(parsed.query)

        sslmode = query_params.pop("sslmode", [None])[0]
        ssl = query_params.pop("ssl", [None])[0]
        # Remove parameters not supported by asyncpg connect
        query_params.pop("channel_binding", None)
        query_params.pop("endpoint", None)

        if sslmode in ("require", "verify-ca", "verify-full") or ssl in ("require", "true", "1", "True"):
            connect_args["ssl"] = "require"
        elif sslmode == "disable" or ssl in ("disable", "false", "0", "False"):
            connect_args["ssl"] = False

        new_query = urllib.parse.urlencode({k: v[0] for k, v in query_params.items()}) if query_params else ""
        cleaned_url = urllib.parse.urlunparse(
            (parsed.scheme, parsed.netloc, parsed.path, parsed.params, new_query, parsed.fragment)
        )
        return cleaned_url, connect_args

    return raw_url, connect_args


cleaned_db_url, db_connect_args = prepare_database_connection(settings.DATABASE_URL)

# Create async engine with serverless-safe pooling (pool_pre_ping ensures stale/idle connections are refreshed)
engine_kwargs = {
    "echo": False,
    "future": True,
}
if db_connect_args:
    engine_kwargs["connect_args"] = db_connect_args

if "sqlite" not in cleaned_db_url.lower():
    engine_kwargs["pool_pre_ping"] = True
    engine_kwargs["pool_recycle"] = 300

engine = create_async_engine(cleaned_db_url, **engine_kwargs)

# Configure SQLite for high concurrency only when using SQLite
if "sqlite" in cleaned_db_url.lower():
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


_tables_initialized = False


async def ensure_tables_created():
    """Idempotently creates all database tables if they do not exist."""
    global _tables_initialized
    if not _tables_initialized:
        # Import models so Base.metadata is fully populated
        import app.models  # noqa: F401
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        _tables_initialized = True
        logger.info("Database schema verified / initialized successfully.")


# Dependency to get db session
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    global _tables_initialized
    if not _tables_initialized:
        try:
            await ensure_tables_created()
        except Exception as e:
            logger.warning(f"Schema verification note: {e}")
            _tables_initialized = True

    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
