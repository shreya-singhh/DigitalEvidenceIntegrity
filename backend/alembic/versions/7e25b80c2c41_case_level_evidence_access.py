"""add case-level evidence access grants

Revision ID: 7e25b80c2c41
Revises: 36a1b9f4d2ce
Create Date: 2026-10-20 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "7e25b80c2c41"
down_revision: Union[str, Sequence[str], None] = "36a1b9f4d2ce"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "verification_logs",
        sa.Column(
            "verification_target",
            sa.String(length=32),
            nullable=False,
            server_default="SUBMITTED_FILE",
        ),
    )
    op.create_table(
        "case_access",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("case_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("granted_by", sa.Integer(), nullable=False),
        sa.Column("granted_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["granted_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("case_id", "user_id", name="uq_case_access_case_user"),
    )
    op.create_index("ix_case_access_case_id", "case_access", ["case_id"], unique=False)
    op.create_index("ix_case_access_granted_by", "case_access", ["granted_by"], unique=False)
    op.create_index("ix_case_access_user_id", "case_access", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_case_access_user_id", table_name="case_access")
    op.drop_index("ix_case_access_granted_by", table_name="case_access")
    op.drop_index("ix_case_access_case_id", table_name="case_access")
    op.drop_table("case_access")
    op.drop_column("verification_logs", "verification_target")
