"""add priority column to cases

Revision ID: 91821f4a5ef7
Revises: e54541b7e2b7
Create Date: 2026-09-27 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "91821f4a5ef7"
down_revision: Union[str, Sequence[str], None] = "e54541b7e2b7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = inspector.get_columns("cases")
    if any(column["name"] == "priority" for column in columns):
        return

    op.add_column(
        "cases",
        sa.Column(
            "priority",
            sa.String(length=20),
            nullable=False,
            server_default="MEDIUM",
            default="MEDIUM",
        ),
    )
    op.execute(sa.text("UPDATE cases SET priority = 'MEDIUM' WHERE priority IS NULL OR priority = ''"))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = inspector.get_columns("cases")
    if not any(column["name"] == "priority" for column in columns):
        return

    op.drop_column("cases", "priority")
