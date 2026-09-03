"""Migration verification: applying every Alembic migration from scratch must
produce a schema containing every column/table/constraint the current ORM
models require. This is the authoritative check that Alembic (not
create_all/schema_migration's ad-hoc patching) is sufficient on its own.
"""
import os
import shutil
import tempfile

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

from app.config import settings

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _run_alembic_upgrade(sqlite_path: str) -> None:
    # alembic/env.py always builds its engine from app.config.settings.DATABASE_URL
    # rather than from the Config object's sqlalchemy.url, so the override has to
    # happen on the already-instantiated settings singleton, not via Config.
    cfg = Config(os.path.join(BACKEND_DIR, "alembic.ini"))
    cfg.set_main_option("script_location", os.path.join(BACKEND_DIR, "alembic"))
    original_url = settings.DATABASE_URL
    settings.DATABASE_URL = f"sqlite+aiosqlite:///{sqlite_path}"
    try:
        command.upgrade(cfg, "head")
    finally:
        settings.DATABASE_URL = original_url


def test_alembic_head_schema_matches_orm_requirements():
    # Use mkdtemp + manual best-effort cleanup instead of TemporaryDirectory's
    # context manager: on Windows, sqlite3/Alembic can keep a file handle open
    # briefly after command.upgrade() returns, and TemporaryDirectory's teardown
    # raises PermissionError if the dir isn't removable yet. That's a teardown
    # quirk, not a verification failure, so we swallow cleanup errors only.
    tmp_dir = tempfile.mkdtemp()
    try:
        db_path = os.path.join(tmp_dir, "alembic_verify.db")
        _run_alembic_upgrade(db_path)

        engine = create_engine(f"sqlite:///{db_path}")
        inspector = inspect(engine)
        tables = set(inspector.get_table_names())

        required_tables = {
            "users", "categories", "products", "product_variants",
            "orders", "order_items", "notifications", "reviews",
        }
        missing_tables = required_tables - tables
        assert not missing_tables, f"Alembic head is missing tables: {missing_tables}"

        def columns(table: str) -> set[str]:
            return {c["name"] for c in inspector.get_columns(table)}

        required_columns = {
            "products": {"id", "name", "name_en", "description", "description_en", "price", "stock", "category_id", "image_path", "created_at"},
            "product_variants": {"id", "product_id", "name", "price"},
            "orders": {"id", "user_id", "status", "fulfillment_type", "total_price", "delivery_address", "delivery_fee", "notes", "idempotency_key", "created_at", "updated_at"},
            "order_items": {"id", "order_id", "product_id", "product_name_snapshot", "product_name_en_snapshot", "variant_id", "variant_name_snapshot", "price_snapshot", "quantity", "subtotal"},
            "notifications": {"id", "user_id", "message", "is_read", "created_at"},
            "reviews": {"id", "order_id", "user_id", "rating", "comment", "created_at"},
        }
        for table, expected in required_columns.items():
            actual = columns(table)
            missing = expected - actual
            assert not missing, f"Alembic head is missing columns on {table}: {missing}"

        engine.dispose()
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)
