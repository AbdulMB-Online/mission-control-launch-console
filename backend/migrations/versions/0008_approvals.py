"""Store explicit human approvals separately from evaluator decisions."""

from alembic import op
import sqlalchemy as sa

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "approvals",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("report_id", sa.String(36), sa.ForeignKey("reports.id", ondelete="CASCADE"), nullable=False),
        sa.Column("briefing_id", sa.String(36), sa.ForeignKey("briefings.id", ondelete="CASCADE"), nullable=False),
        sa.Column("approved_by", sa.String(100), nullable=False),
        sa.Column("approved_at", sa.String(27), nullable=False),
        sa.Column("review_acknowledged", sa.Boolean(), nullable=False),
        sa.Column("review_reasons_snapshot_json", sa.Text(), nullable=False),
        sa.UniqueConstraint("report_id", name="uq_approval_report"),
        sa.UniqueConstraint("briefing_id", name="uq_approval_briefing"),
    )


def downgrade():
    op.drop_table("approvals")
