"""Store v1 Python launch assessments, including existing engineer reports."""

from decimal import Decimal
import json

from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("reports", sa.Column("verdict", sa.String(5), nullable=True))
    op.add_column("reports", sa.Column("violations_json", sa.Text(), nullable=True))
    op.add_column("reports", sa.Column("rule_version", sa.String(20), nullable=True))

    connection = op.get_bind()
    # Freeze the v1 rule snapshot here so future application rules cannot change
    # the meaning of this historical migration. Do not import mutable ORM code.
    rules = (
        ("wind_knots", "<=", Decimal("25"), "Wind must be at most 25 knots."),
        ("temp_c", ">=", Decimal("4"), "Temperature must be at least 4°C."),
        ("fuel_pct", ">=", Decimal("98"), "Fuel must be at least 98%."),
        ("fuel_pct", "<=", Decimal("100"), "Fuel must be at most 100%."),
    )
    rows = connection.execute(sa.text("SELECT id, wind_knots, temp_c, fuel_pct FROM reports")).mappings()
    for row in rows:
        violations = []
        for field, operator, limit, message in rules:
            observed = Decimal(row[field])
            failed = observed > limit if operator == "<=" else observed < limit
            if failed:
                violations.append({
                    "field": field, "observed": format(observed, "f"), "operator": operator,
                    "limit": format(limit, "f"), "message": message,
                })
        connection.execute(sa.text(
            "UPDATE reports SET verdict = :verdict, violations_json = :violations, rule_version = 'v1' WHERE id = :id"
        ), {"id": row["id"], "verdict": "no_go" if violations else "go", "violations": json.dumps(violations)})

    with op.batch_alter_table("reports") as batch:
        batch.alter_column("verdict", existing_type=sa.String(5), nullable=False)
        batch.alter_column("violations_json", existing_type=sa.Text(), nullable=False)
        batch.alter_column("rule_version", existing_type=sa.String(20), nullable=False)
        batch.create_check_constraint("report_verdict_value", "verdict IN ('go', 'no_go')")


def downgrade():
    with op.batch_alter_table("reports") as batch:
        batch.drop_constraint("report_verdict_value", type_="check")
        batch.drop_column("rule_version")
        batch.drop_column("violations_json")
        batch.drop_column("verdict")
