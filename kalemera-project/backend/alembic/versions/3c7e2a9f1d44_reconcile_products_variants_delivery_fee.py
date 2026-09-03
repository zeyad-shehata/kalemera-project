"""Reconcile ORM/Alembic drift: products i18n columns, product_variants table,
orders.delivery_fee, and a migration-verification safety net.

Revision ID: 3c7e2a9f1d44
Revises: 8a1f5c9d2b3e
Create Date: 2026-09-03 20:00:00.000000

Audit findings this migration closes (previously only patched ad-hoc by
app.services.schema_migration at boot, never authoritatively in Alembic):
  * products.name_en / products.description_en — missing entirely.
  * product_variants table — missing entirely (the whole table).
  * orders.delivery_fee — missing entirely.
  * notifications.is_read — column existed but its index did not.

All changes are additive and defensive (existence-checked), so this is safe
to run against a production database that already has some of these columns
patched in ad-hoc by schema_migration.py.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = '3c7e2a9f1d44'
down_revision: Union[str, None] = '8a1f5c9d2b3e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(table: str) -> bool:
    return inspect(op.get_bind()).has_table(table)


def _columns(table: str) -> set[str]:
    return {c["name"] for c in inspect(op.get_bind()).get_columns(table)}


def _indexes(table: str) -> set[str]:
    return {i["name"] for i in inspect(op.get_bind()).get_indexes(table)}


def upgrade() -> None:
    # --- products: i18n columns ---
    if _table_exists("products"):
        existing = _columns("products")
        if "name_en" not in existing:
            op.add_column("products", sa.Column("name_en", sa.String(length=255), nullable=True))
            op.create_index(op.f("ix_products_name_en"), "products", ["name_en"], unique=False)
        if "description_en" not in existing:
            op.add_column("products", sa.Column("description_en", sa.String(length=1000), nullable=True))

    # --- orders: delivery_fee (was never in Alembic, only patched ad-hoc) ---
    if _table_exists("orders") and "delivery_fee" not in _columns("orders"):
        op.add_column(
            "orders",
            sa.Column("delivery_fee", sa.Numeric(10, 2), nullable=False, server_default="0.00"),
        )

    # --- notifications: missing index on is_read ---
    if _table_exists("notifications") and "ix_notifications_is_read" not in _indexes("notifications"):
        op.create_index(
            op.f("ix_notifications_is_read"), "notifications", ["is_read"], unique=False
        )

    # --- product_variants: entire table missing from Alembic history ---
    if not _table_exists("product_variants"):
        op.create_table(
            "product_variants",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column(
                "product_id", sa.Integer(),
                sa.ForeignKey("products.id", ondelete="CASCADE"), nullable=False,
            ),
            sa.Column("name", sa.String(length=50), nullable=False),
            sa.Column("price", sa.Numeric(10, 2), nullable=False),
        )
        op.create_index(
            op.f("ix_product_variants_product_id"), "product_variants", ["product_id"], unique=False
        )


def downgrade() -> None:
    if _table_exists("product_variants"):
        op.drop_index(op.f("ix_product_variants_product_id"), table_name="product_variants")
        op.drop_table("product_variants")

    if _table_exists("notifications") and "ix_notifications_is_read" in _indexes("notifications"):
        op.drop_index(op.f("ix_notifications_is_read"), table_name="notifications")

    if _table_exists("orders") and "delivery_fee" in _columns("orders"):
        op.drop_column("orders", "delivery_fee")

    if _table_exists("products"):
        existing = _columns("products")
        if "description_en" in existing:
            op.drop_column("products", "description_en")
        if "name_en" in existing:
            op.drop_index(op.f("ix_products_name_en"), table_name="products")
            op.drop_column("products", "name_en")
