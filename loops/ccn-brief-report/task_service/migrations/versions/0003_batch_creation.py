"""Persist batch responses independently from task lifetime; no automatic TTL."""
from alembic import op
import sqlalchemy as sa

revision = "0003_batch_creation"
down_revision = "0002_task_category"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("batch_creations",
        sa.Column("key", sa.String(128), primary_key=True),
        sa.Column("request_hash", sa.String(64), nullable=False),
        sa.Column("response_body", sa.JSON(), nullable=False),
        sa.Column("status_code", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.add_column("audit_events", sa.Column("batch_counts", sa.JSON(), nullable=True))


def downgrade():
    op.drop_column("audit_events", "batch_counts")
    op.drop_table("batch_creations")
