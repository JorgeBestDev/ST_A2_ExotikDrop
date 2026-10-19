"""Compatibility bridge for databases stamped with the legacy revision.

Revision ID: 08f172200668
Revises: e83d939de4ca

The current baseline migration represents the schema already present in
databases that were stamped with the legacy revision. Keep this revision as an
empty bridge so those databases and fresh installs share the same migration
head without replaying schema creation.
"""

revision = '08f172200668'
down_revision = 'e83d939de4ca'
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
