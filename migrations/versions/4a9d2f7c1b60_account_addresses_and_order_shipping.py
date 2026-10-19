"""Add customer addresses and order shipping snapshots.

Revision ID: 4a9d2f7c1b60
Revises: e83d939de4ca
"""
from alembic import op
import sqlalchemy as sa


revision = '4a9d2f7c1b60'
down_revision = '08f172200668'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'shipping_addresses',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('recipient', sa.String(length=255), nullable=False),
        sa.Column('phone', sa.String(length=40), nullable=False),
        sa.Column('line1', sa.String(length=255), nullable=False),
        sa.Column('line2', sa.String(length=255), nullable=True),
        sa.Column('city', sa.String(length=120), nullable=False),
        sa.Column('region', sa.String(length=120), nullable=False),
        sa.Column('postal_code', sa.String(length=30), nullable=False),
        sa.Column('country', sa.String(length=120), nullable=False),
        sa.Column('is_default', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_shipping_addresses_user_id', 'shipping_addresses', ['user_id'])

    with op.batch_alter_table('orders') as batch_op:
        batch_op.add_column(sa.Column('shipping_recipient', sa.String(length=255), nullable=False, server_default=''))
        batch_op.add_column(sa.Column('shipping_phone', sa.String(length=40), nullable=False, server_default=''))
        batch_op.add_column(sa.Column('shipping_line1', sa.String(length=255), nullable=False, server_default=''))
        batch_op.add_column(sa.Column('shipping_line2', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('shipping_city', sa.String(length=120), nullable=False, server_default=''))
        batch_op.add_column(sa.Column('shipping_region', sa.String(length=120), nullable=False, server_default=''))
        batch_op.add_column(sa.Column('shipping_postal_code', sa.String(length=30), nullable=False, server_default=''))
        batch_op.add_column(sa.Column('shipping_country', sa.String(length=120), nullable=False, server_default=''))


def downgrade():
    with op.batch_alter_table('orders') as batch_op:
        batch_op.drop_column('shipping_country')
        batch_op.drop_column('shipping_postal_code')
        batch_op.drop_column('shipping_region')
        batch_op.drop_column('shipping_city')
        batch_op.drop_column('shipping_line2')
        batch_op.drop_column('shipping_line1')
        batch_op.drop_column('shipping_phone')
        batch_op.drop_column('shipping_recipient')
    op.drop_index('ix_shipping_addresses_user_id', table_name='shipping_addresses')
    op.drop_table('shipping_addresses')
