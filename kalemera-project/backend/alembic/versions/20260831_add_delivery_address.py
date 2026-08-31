"""add delivery_address and order item snapshot columns

Revision ID: 20260831_add_delivery_address
Revises: 20230829_initial
Create Date: 2026-08-31 00:00:00.000000

Adds the additive columns required by the current ORM models to the
already-deployed `orders` and `order_items` tables.

Migration style:
  * Defensive + idempotent: each column is added only when it does not already
    exist (PostgreSQL: `ADD COLUMN IF NOT EXISTS`; for MySQL a
    `information_schema` check is used, though this project targets Postgres).
  * Preserves all existing rows and column values.
  * Never drops, renames, or alters existing columns/data.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision: str = "20260831_add_delivery_address"
down_revision: Union[str, None] = "20230829_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(table: str) -> bool:
    return inspect(op.get_bind()).has_table(table)


def _columns(table: str) -> set[str]:
    return {c["name"] for c in inspect(op.get_bind()).get_columns(table)}


def _add_column_if_missing(table: str, name: str, column: sa.Column) -> None:
    if not _table_exists(table) or name in _columns(table):
        return
    op.add_column(table, column)


def upgrade() -> None:
    # orders.delivery_address (newly required by the Order model)
    _add_column_if_missing(
        "orders",
        "delivery_address",
        sa.Column("delivery_address", sa.String(length=255), nullable=True),
    )

    # order_items snapshot columns required by the OrderItem model
    if not _table_exists("order_items"):
        return
    existing = _columns("order_items")

    if "product_name_snapshot" not in existing:
        op.add_column(
            "order_items",
            sa.Column(
                "product_name_snapshot",
                sa.String(length=255),
                nullable=False,
                server_default="",
            ),
        )

    if "product_name_en_snapshot" not in existing:
        op.add_column(
            "order_items",
            sa.Column("product_name_en_snapshot", sa.String(length=255), nullable=True),
        )

    if "variant_id" not in existing:
        op.add_column(
            "order_items", sa.Column("variant_id", sa.Integer(), nullable=True)
        )

    if "variant_name_snapshot" not in existing:
        op.add_column(
            "order_items",
            sa.Column("variant_name_snapshot", sa.String(length=50), nullable=True),
        )

    if "price_snapshot" not in existing:
        op.add_column(
            "order_items", sa.Column("price_snapshot", sa.Numeric(10, 2), nullable=True)
        )

    if "subtotal" not in existing:
        op.add_column(
            "order_items", sa.Column("subtotal", sa.Numeric(10, 2), nullable=True)
        )


def downgrade() -> None:
    # Downgrades are intentionally limited to columns this migration added.
    # Additive-only downgrade that drops only the columns this migration added;
    # used for clean rollback on fresh environments. Existing production data is
    # not dropped in a normal downgrade flow.
    if _table_exists("orders") and "delivery_address" in _columns("orders"):
        op.drop_column("orders", "delivery_address")

    if _table_exists("order_items"):
        existing = _columns("order_items")
        for name in (
            "product_name_snapshot",
            "product_name_en_snapshot",
            "variant_id",
            "variant_name_snapshot",
            "price_snapshot",
            "subtotal",
        ):
            if name in existing:
                op.drop_column("order_items", name)
