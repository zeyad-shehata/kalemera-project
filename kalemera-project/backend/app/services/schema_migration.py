"""Safe, idempotent, additive schema migration for existing PostgreSQL tables.

Background:
-----------
The deployed app bootstraps its schema with ``Base.metadata.create_all()``
(see ``app.database.ensure_tables_created``). ``create_all`` only creates tables
that do not already exist; it NEVER adds new columns to an already-existing table.

When a new column is added to an ORM model after the production table was first
created (e.g. ``Order.delivery_address``), the production table is left without
that column, and any INSERT referencing it fails with:
    UndefinedColumn: column orders.delivery_address does not exist

This module closes that gap with additive, idempotent ``ALTER TABLE ... ADD
COLUMN IF NOT EXISTS`` calls that:
  * add columns only if they are missing (never touched if already present)
  * preserve all existing rows and their values
  * never drop or alter existing columns / data
  * are safe to run repeatedly (startup, each cold start, tests)

PostgreSQL (including Neon) supports ``ADD COLUMN IF NOT EXISTS`` natively.
For the SQLite test database the same helpers are applied with a ``PRAGMA
table_info`` check so the test schema also stays in sync.
"""
import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection

logger = logging.getLogger("kalemera.schema_migration")


def _required_columns(table: str) -> dict:
    """Return the authoritative column definitions for a table from the ORM model.

    drivern: keep this in sync with the SQLAlchemy models in ``app.models``.
    """
    from app.models import Order, OrderItem  # noqa: F401

    columns: dict[str, str] = {}
    if table == "orders":
        columns["delivery_address"] = "VARCHAR(255) NULL"
        columns["delivery_fee"] = "NUMERIC(10,2) NOT NULL DEFAULT 0"
    elif table == "order_items":
        columns["product_name_snapshot"] = "VARCHAR(255) NOT NULL DEFAULT ''"
        columns["product_name_en_snapshot"] = "VARCHAR(255) NULL"
        columns["variant_id"] = "BIGINT NULL"
        columns["variant_name_snapshot"] = "VARCHAR(50) NULL"
        columns["price_snapshot"] = "NUMERIC(10,2) NULL"
        columns["subtotal"] = "NUMERIC(10,2) NULL"
    return columns


async def _driver_name(conn_or_session) -> str:
    bind = getattr(conn_or_session, "get_bind", None)
    if callable(bind):
        return bind().dialect.name
    return conn_or_session.dialect.name


async def _existing_columns_sqlite(conn, table: str) -> set[str]:
    result = await conn.execute(text(f"PRAGMA table_info({table})"))
    return {row[1] for row in result.fetchall()}


async def ensure_column(conn, driver: str, table: str, name: str, definition: str) -> bool:
    """Add a single column to ``table`` if it does not already exist.

    Returns True if the column was added, False if it already existed.
    Never deletes or modifies data.
    """
    if driver == "postgresql":
        await conn.execute(
            text(f'ALTER TABLE "{table}" ADD COLUMN IF NOT EXISTS "{name}" {definition}')
        )
        return True  # cannot easily know if added; idempotent regardless
    # SQLite has no IF NOT EXISTS for columns, so gate on PRAGMA info
    existing = await _existing_columns_sqlite(conn, table)
    if name in existing:
        return False
    await conn.execute(text(f'ALTER TABLE "{table}" ADD COLUMN "{name}" {definition}'))
    return True


async def migrate_schema(conn: AsyncConnection) -> dict:
    """Apply additive schema changes required by the ORM models.

    Idempotent and data-preserving. Returns a summary of applied changes.
    Accepts either an AsyncConnection or an AsyncSession.
    """
    driver = await _driver_name(conn)
    changes: dict[str, list[str]] = {}

    for table in ("orders", "order_items"):
        added = []
        # Verify table exists before touching it (fresh databases may still be
        # creating tables via create_all depending on call order).
        if not await _table_exists(conn, table):
            continue
        for name, definition in _required_columns(table).items():
            try:
                if await ensure_column(conn, driver, table, name, definition):
                    added.append(name)
            except Exception as exc:  # pragma: no cover - defensive
                logger.warning("Unable to add column %s.%s: %s", table, name, exc)
        if added:
            changes[table] = added

    return changes


async def _table_exists(conn, table: str) -> bool:
    driver = await _driver_name(conn)
    if driver == "postgresql":
        result = await conn.execute(
            text(
                "SELECT to_regclass(:tbl) IS NOT NULL"
            ),
            {"tbl": table},
        )
        return bool(result.scalar())
    result = await conn.execute(
        text(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=:tbl"
        ),
        {"tbl": table},
    )
    return result.scalar() is not None
