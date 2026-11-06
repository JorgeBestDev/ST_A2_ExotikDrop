"""Add administrative CAPTCHA, user status, and order drop snapshots."""

from alembic import op
import sqlalchemy as sa


revision = '91c8abf0d2e1'
down_revision = '4a9d2f7c1b60'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('users') as batch_op:
        batch_op.add_column(sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()))

    with op.batch_alter_table('order_items') as batch_op:
        batch_op.add_column(sa.Column('drop_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('fk_order_items_drop_id_drops', 'drops', ['drop_id'], ['id'])
    op.execute(
        'UPDATE order_items SET drop_id = '
        '(SELECT products.drop_id FROM products WHERE products.id = order_items.product_id)'
    )

    op.create_table(
        'admin_captcha_challenges',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('answer_hash', sa.String(length=64), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('consumed', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('client_fingerprint', sa.String(length=64), nullable=True),
        sa.Column('login_failed', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.PrimaryKeyConstraint('id'),
    )

    with op.batch_alter_table('users') as batch_op:
        batch_op.alter_column('is_active', server_default=None)


def downgrade():
    op.drop_table('admin_captcha_challenges')
    with op.batch_alter_table('order_items') as batch_op:
        batch_op.drop_constraint('fk_order_items_drop_id_drops', type_='foreignkey')
        batch_op.drop_column('drop_id')
    with op.batch_alter_table('users') as batch_op:
        batch_op.drop_column('is_active')
