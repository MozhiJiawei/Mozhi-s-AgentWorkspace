"""Add optional task category without rewriting historical tasks."""
from alembic import op
import sqlalchemy as sa

revision = '0002_task_category'
down_revision = '0001_initial'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('tasks', sa.Column('category', sa.String(256), nullable=True))


def downgrade() -> None:
    op.drop_column('tasks', 'category')
