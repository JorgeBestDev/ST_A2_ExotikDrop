"""Add persistent checkout reservations for limited-drop inventory.

Revision ID: 7b41c2d9e508
Revises: 91c8abf0d2e1
"""
from alembic import op
import sqlalchemy as sa


revision = '7b41c2d9e508'
down_revision = '91c8abf0d2e1'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('orders') as batch_op:
        batch_op.add_column(sa.Column('checkout_key', sa.String(length=64), nullable=True))
        batch_op.create_unique_constraint(
            'uq_order_user_checkout_key',
            ['user_id', 'checkout_key'],
        )

    with op.batch_alter_table('products') as batch_op:
        batch_op.create_check_constraint('ck_products_stock_nonnegative', 'stock >= 0')

    op.create_table(
        'inventory_reservations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('order_id', sa.Integer(), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "status IN ('active', 'consumed', 'expired', 'released')",
            name='ck_inventory_reservation_status',
        ),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('order_id'),
    )
    op.create_index(
        'uq_inventory_reservation_active_user',
        'inventory_reservations',
        ['user_id'],
        unique=True,
        postgresql_where=sa.text("status = 'active'"),
        sqlite_where=sa.text("status = 'active'"),
    )
    op.create_index(
        'ix_inventory_reservation_expiry',
        'inventory_reservations',
        ['status', 'expires_at'],
    )

    op.create_table(
        'inventory_reservation_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('reservation_id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.CheckConstraint('quantity > 0', name='ck_reservation_item_quantity_positive'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id']),
        sa.ForeignKeyConstraint(['reservation_id'], ['inventory_reservations.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('reservation_id', 'product_id', name='uq_reservation_product'),
    )
    op.create_index(
        'ix_inventory_reservation_item_product',
        'inventory_reservation_items',
        ['product_id'],
    )


def downgrade():
    op.drop_index('ix_inventory_reservation_item_product', table_name='inventory_reservation_items')
    op.drop_table('inventory_reservation_items')
    op.drop_index('ix_inventory_reservation_expiry', table_name='inventory_reservations')
    op.drop_index('uq_inventory_reservation_active_user', table_name='inventory_reservations')
    op.drop_table('inventory_reservations')

    with op.batch_alter_table('products') as batch_op:
        batch_op.drop_constraint('ck_products_stock_nonnegative', type_='check')

    with op.batch_alter_table('orders') as batch_op:
        batch_op.drop_constraint('uq_order_user_checkout_key', type_='unique')
        batch_op.drop_column('checkout_key')
