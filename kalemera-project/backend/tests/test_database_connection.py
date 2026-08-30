import pytest
from sqlalchemy.engine.url import make_url
from sqlalchemy.dialects.postgresql.asyncpg import PGDialect_asyncpg
from app.database import prepare_database_connection, Base
import app.models  # noqa: F401


def test_prepare_database_connection_neon_with_channel_binding():
    """Verifies that Neon PostgreSQL URLs with sslmode and channel_binding
    are cleanly stripped of invalid asyncpg parameters and properly set ssl=require.
    """
    raw_neon_url = (
        "postgresql://neondb_owner:npg_secret123@"
        "ep-cool-fog-12345-pooler.us-east-2.aws.neon.tech/neondb?"
        "sslmode=require&channel_binding=require&endpoint=ep-cool-fog-12345"
    )

    cleaned_url, connect_args = prepare_database_connection(raw_neon_url)

    # 1. Check scheme conversion
    assert cleaned_url.startswith("postgresql+asyncpg://")

    # 2. Check query string is stripped
    url_obj = make_url(cleaned_url)
    assert "channel_binding" not in url_obj.query
    assert "sslmode" not in url_obj.query
    assert "endpoint" not in url_obj.query

    # 3. Check connect_args
    assert connect_args.get("ssl") == "require"

    # 4. Verify what SQLAlchemy's asyncpg dialect produces for asyncpg.connect()
    dialect = PGDialect_asyncpg()
    _, kwargs = dialect.create_connect_args(url_obj)
    final_kwargs = {**kwargs, **connect_args}

    assert "channel_binding" not in final_kwargs
    assert "sslmode" not in final_kwargs
    assert "endpoint" not in final_kwargs
    assert final_kwargs["ssl"] == "require"
    assert final_kwargs["user"] == "neondb_owner"
    assert final_kwargs["password"] == "npg_secret123"
    assert final_kwargs["database"] == "neondb"
    assert final_kwargs["host"] == "ep-cool-fog-12345-pooler.us-east-2.aws.neon.tech"


def test_prepare_database_connection_sqlite():
    """Verifies SQLite URLs remain unmodified without extra connect_args."""
    sqlite_url = "sqlite+aiosqlite:///./test.db"
    cleaned_url, connect_args = prepare_database_connection(sqlite_url)
    assert cleaned_url == sqlite_url
    assert connect_args == {}


def test_models_metadata_tables():
    """Verifies all expected models and tables are registered in Base.metadata."""
    table_names = set(Base.metadata.tables.keys())
    expected = {
        "users",
        "categories",
        "products",
        "product_variants",
        "orders",
        "order_items",
        "notifications",
    }
    assert expected.issubset(table_names), f"Missing tables: {expected - table_names}"
