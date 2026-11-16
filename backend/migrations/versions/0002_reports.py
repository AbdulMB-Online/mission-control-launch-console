"""Persist engineer reports with exact readings and server-owned metadata."""

from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "reports",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("engineer_name", sa.String(100), nullable=False),
        sa.Column("station", sa.String(50), nullable=False),
        sa.Column("wind_knots", sa.Text(), nullable=False),
        sa.Column("temp_c", sa.Text(), nullable=False),
        sa.Column("fuel_pct", sa.Text(), nullable=False),
        sa.Column("note", sa.Text(), nullable=False),
        sa.Column("created_at", sa.String(27), nullable=False),
        sa.CheckConstraint("length(engineer_name) BETWEEN 1 AND 100", name="report_name_length"),
        sa.CheckConstraint("length(station) BETWEEN 1 AND 50", name="report_station_length"),
        sa.CheckConstraint("length(note) BETWEEN 1 AND 4000", name="report_note_length"),
    )
    op.create_index("ix_reports_created_id", "reports", ["created_at", "id"])


def downgrade():
    op.drop_table("reports")
