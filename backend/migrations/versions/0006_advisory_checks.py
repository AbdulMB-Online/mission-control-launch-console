"""Persist independent advisory checks and their shared execution group."""

from alembic import op
import sqlalchemy as sa

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("step_traces", sa.Column("parallel_group", sa.String(36), nullable=True))
    op.create_table(
        "pipeline_checks",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("report_id", sa.String(36), sa.ForeignKey("reports.id", ondelete="CASCADE"), nullable=False),
        sa.Column("kind", sa.String(24), nullable=False),
        sa.Column("status", sa.String(12), nullable=False),
        sa.Column("flagged", sa.Boolean(), nullable=True),
        sa.Column("details_json", sa.Text(), nullable=False),
        sa.Column("error_code", sa.String(40), nullable=True),
        sa.UniqueConstraint("report_id", "kind", name="uq_report_check_kind"),
        sa.CheckConstraint("kind IN ('injection', 'missing_information', 'tone')", name="check_kind_value"),
        sa.CheckConstraint("status IN ('completed', 'error')", name="check_status_value"),
        sa.CheckConstraint("(status = 'error' AND flagged IS NULL) OR (status = 'completed' AND flagged IS NOT NULL)", name="check_flag_known"),
    )
    op.create_index("ix_pipeline_checks_report_id", "pipeline_checks", ["report_id"])


def downgrade():
    op.drop_index("ix_pipeline_checks_report_id", table_name="pipeline_checks")
    op.drop_table("pipeline_checks")
    with op.batch_alter_table("step_traces") as batch:
        batch.drop_column("parallel_group")
