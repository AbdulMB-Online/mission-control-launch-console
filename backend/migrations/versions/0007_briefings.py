"""Persist bounded briefing rounds and terminal selection without approval."""

from alembic import op
import sqlalchemy as sa

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade():
    # Add columns directly: rebuilding reports with foreign keys enabled could
    # delete existing child checks/traces through their ON DELETE CASCADE.
    op.add_column("reports", sa.Column("pipeline_status", sa.String(10),
                  sa.CheckConstraint("pipeline_status IN ('queued', 'processing', 'completed', 'failed')", name="report_pipeline_status"),
                  nullable=False, server_default="queued"))
    op.add_column("reports", sa.Column("error_code", sa.String(40), nullable=True))
    op.add_column("step_traces", sa.Column("round_number", sa.Integer(), nullable=True))
    op.create_table(
        "briefings",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("report_id", sa.String(36), sa.ForeignKey("reports.id", ondelete="CASCADE"), nullable=False),
        sa.Column("round_number", sa.Integer(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("actions_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.String(27), nullable=False),
        sa.Column("evaluation_status", sa.String(14), nullable=False),
        sa.Column("feedback_json", sa.Text(), nullable=False),
        sa.Column("evaluated_at", sa.String(27), nullable=True),
        sa.Column("is_selected", sa.Boolean(), nullable=False),
        sa.UniqueConstraint("report_id", "round_number", name="uq_report_briefing_round"),
        sa.CheckConstraint("round_number BETWEEN 1 AND 3", name="briefing_round_bound"),
        sa.CheckConstraint("length(summary) BETWEEN 1 AND 1200", name="briefing_summary_length"),
        sa.CheckConstraint("evaluation_status IN ('pending', 'accepted', 'needs_revision', 'error')", name="briefing_evaluation_status"),
        sa.CheckConstraint("is_selected = 0 OR evaluation_status != 'pending'", name="briefing_selectable"),
    )
    op.create_index("ix_briefings_report_id", "briefings", ["report_id"])
    op.create_index("ix_briefings_selected", "briefings", ["report_id"], unique=True, sqlite_where=sa.text("is_selected = 1"))


def downgrade():
    op.drop_index("ix_briefings_selected", table_name="briefings")
    op.drop_index("ix_briefings_report_id", table_name="briefings")
    op.drop_table("briefings")
    op.drop_column("step_traces", "round_number")
    op.drop_column("reports", "error_code")
    op.drop_column("reports", "pipeline_status")
