"""Allow in-flight traces and persist their original cost/rate snapshot."""
from alembic import op
import sqlalchemy as sa

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None


def upgrade():
    # Only this leaf table is rebuilt; reports/briefings/approvals stay intact.
    with op.batch_alter_table("step_traces") as batch:
        batch.alter_column("finished_at", existing_type=sa.String(27), nullable=True)
        batch.add_column(sa.Column("cost_usd", sa.Text(), nullable=True))
        batch.add_column(sa.Column("rate_snapshot_json", sa.Text(), nullable=True))
    # Historic provider rates weren't captured. Leave those costs unknown.
    op.execute("UPDATE step_traces SET cost_usd = '0' WHERE provider IN ('fake', 'python', 'human') AND status != 'running'")


def downgrade():
    op.execute("UPDATE step_traces SET finished_at = started_at WHERE finished_at IS NULL")
    with op.batch_alter_table("step_traces") as batch:
        batch.drop_column("rate_snapshot_json")
        batch.drop_column("cost_usd")
        batch.alter_column("finished_at", existing_type=sa.String(27), nullable=False)
