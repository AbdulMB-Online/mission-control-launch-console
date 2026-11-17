"""Persist validated classification, human-review reasons and call usage."""

from alembic import op
import sqlalchemy as sa

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("reports", sa.Column("subsystem", sa.String(32), nullable=False, server_default="unknown"))
    op.add_column("reports", sa.Column("classification_status", sa.String(12), nullable=False, server_default="not_run"))
    op.add_column("reports", sa.Column("classification_rationale", sa.String(500), nullable=False, server_default=""))
    op.add_column("reports", sa.Column("requires_review", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("reports", sa.Column("review_reasons_json", sa.Text(), nullable=False, server_default="[]"))
    with op.batch_alter_table("reports") as batch:
        batch.create_check_constraint("report_classification_status", "classification_status IN ('not_run', 'completed', 'fallback')")

    op.create_table(
        "step_traces",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("report_id", sa.String(36), sa.ForeignKey("reports.id", ondelete="CASCADE"), nullable=False),
        sa.Column("step_key", sa.String(40), nullable=False),
        sa.Column("display_order", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(12), nullable=False),
        sa.Column("started_at", sa.String(27), nullable=False),
        sa.Column("finished_at", sa.String(27), nullable=False),
        sa.Column("provider", sa.String(20), nullable=False),
        sa.Column("model", sa.String(128), nullable=True),
        sa.Column("prompt_version", sa.String(40), nullable=False),
        sa.Column("provider_response_id", sa.String(128), nullable=True),
        sa.Column("input_tokens", sa.Integer(), nullable=True),
        sa.Column("cached_input_tokens", sa.Integer(), nullable=True),
        sa.Column("output_tokens", sa.Integer(), nullable=True),
        sa.Column("usage_status", sa.String(20), nullable=False),
        sa.Column("error_code", sa.String(40), nullable=True),
        sa.UniqueConstraint("report_id", "step_key", name="uq_report_step"),
        sa.CheckConstraint("input_tokens IS NULL OR input_tokens >= 0", name="trace_input_tokens"),
        sa.CheckConstraint("output_tokens IS NULL OR output_tokens >= 0", name="trace_output_tokens"),
        sa.CheckConstraint("cached_input_tokens IS NULL OR (cached_input_tokens >= 0 AND cached_input_tokens <= input_tokens)", name="trace_cached_tokens"),
    )
    op.create_index("ix_step_traces_report_id", "step_traces", ["report_id"])


def downgrade():
    op.drop_index("ix_step_traces_report_id", table_name="step_traces")
    op.drop_table("step_traces")
    with op.batch_alter_table("reports") as batch:
        batch.drop_constraint("report_classification_status", type_="check")
        for name in ("review_reasons_json", "requires_review", "classification_rationale", "classification_status", "subsystem"):
            batch.drop_column(name)
