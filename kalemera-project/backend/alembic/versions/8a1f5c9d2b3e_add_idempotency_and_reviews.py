"""Add order idempotency key, orders workflow index, and reviews table

Revision ID: 8a1f5c9d2b3e
Revises: 71489946dd34
Create Date: 2026-09-03 19:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8a1f5c9d2b3e'
down_revision: Union[str, None] = '71489946dd34'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Additive, data-preserving: nullable column, new unique constraint (existing
    # rows have NULL keys so the constraint is trivially satisfied), new index.
    # Batch mode is required for SQLite (no native ALTER for constraints); it is
    # a no-op wrapper (plain ALTER statements) on PostgreSQL/Neon.
    with op.batch_alter_table('orders') as batch_op:
        batch_op.add_column(sa.Column('idempotency_key', sa.String(length=100), nullable=True))
        batch_op.create_unique_constraint(
            'uq_orders_user_idempotency_key', ['user_id', 'idempotency_key']
        )
        batch_op.create_index(
            'ix_orders_status_created_at_id', ['status', 'created_at', 'id']
        )

    op.create_table(
        'reviews',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('order_id', sa.Integer(), sa.ForeignKey('orders.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('rating', sa.Integer(), nullable=False),
        sa.Column('comment', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint('order_id', name='uq_reviews_order_id'),
        sa.CheckConstraint('rating >= 1 AND rating <= 5', name='ck_reviews_rating_range'),
    )
    op.create_index('ix_reviews_order_id', 'reviews', ['order_id'], unique=False)
    op.create_index('ix_reviews_user_id', 'reviews', ['user_id'], unique=False)
    op.create_index('ix_reviews_created_at', 'reviews', ['created_at'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_reviews_created_at', table_name='reviews')
    op.drop_index('ix_reviews_user_id', table_name='reviews')
    op.drop_index('ix_reviews_order_id', table_name='reviews')
    op.drop_table('reviews')

    with op.batch_alter_table('orders') as batch_op:
        batch_op.drop_index('ix_orders_status_created_at_id')
        batch_op.drop_constraint('uq_orders_user_idempotency_key', type_='unique')
        batch_op.drop_column('idempotency_key')
