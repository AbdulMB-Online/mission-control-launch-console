"""Add durable provisional priority anchored to original report timestamps."""

from datetime import UTC, datetime, timedelta

from alembic import op
import sqlalchemy as sa

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("reports", sa.Column("classified_severity", sa.String(6), nullable=True))
    op.add_column("reports", sa.Column("effective_severity", sa.String(6), nullable=True))
    op.add_column("reports", sa.Column("deadline_minutes", sa.Integer(), nullable=True))
    op.add_column("reports", sa.Column("brief_by_at", sa.String(27), nullable=True))
    op.add_column("reports", sa.Column("severity_provisional", sa.Boolean(), nullable=True))

    connection = op.get_bind()
    for row in connection.execute(sa.text("SELECT id, created_at FROM reports")).mappings():
        created_at = datetime.fromisoformat(row["created_at"].replace("Z", "+00:00"))
        deadline = (created_at.astimezone(UTC) + timedelta(minutes=5)).isoformat(timespec="microseconds").replace("+00:00", "Z")
        connection.execute(sa.text(
            "UPDATE reports SET effective_severity = 'high', deadline_minutes = 5, "
            "brief_by_at = :deadline, severity_provisional = 1 WHERE id = :id"
        ), {"id": row["id"], "deadline": deadline})

    with op.batch_alter_table("reports") as batch:
        batch.alter_column("effective_severity", existing_type=sa.String(6), nullable=False)
        batch.alter_column("deadline_minutes", existing_type=sa.Integer(), nullable=False)
        batch.alter_column("brief_by_at", existing_type=sa.String(27), nullable=False)
        batch.alter_column("severity_provisional", existing_type=sa.Boolean(), nullable=False)
        batch.create_check_constraint("report_classified_severity_value", "classified_severity IS NULL OR classified_severity IN ('high', 'medium', 'low')")
        batch.create_check_constraint(
            "report_priority_mapping",
            "(effective_severity = 'high' AND deadline_minutes = 5) OR "
            "(effective_severity = 'medium' AND deadline_minutes = 15) OR "
            "(effective_severity = 'low' AND deadline_minutes = 30)",
        )
        batch.create_check_constraint("report_no_go_priority", "verdict = 'go' OR effective_severity = 'high'")


def downgrade():
    with op.batch_alter_table("reports") as batch:
        for name in ("report_no_go_priority", "report_priority_mapping", "report_classified_severity_value"):
            batch.drop_constraint(name, type_="check")
        for name in ("severity_provisional", "brief_by_at", "deadline_minutes", "effective_severity", "classified_severity"):
            batch.drop_column(name)
