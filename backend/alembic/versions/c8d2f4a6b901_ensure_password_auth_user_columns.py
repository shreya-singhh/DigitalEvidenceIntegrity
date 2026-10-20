"""Ensure the password-auth user profile columns exist.

Revision ID: c8d2f4a6b901
Revises: a92f6c8d31b7
Create Date: 2026-10-21 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c8d2f4a6b901"
down_revision: Union[str, Sequence[str], None] = "a92f6c8d31b7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    tables = set(inspector.get_table_names())
    if "users" not in tables:
        raise RuntimeError("The users table is missing; refusing to initialize a new production schema.")

    user_columns = {column["name"] for column in inspector.get_columns("users")}
    columns_to_add = (
        sa.Column("full_name", sa.String(length=120), nullable=False, server_default=""),
        sa.Column("terms_accepted_at", sa.DateTime(), nullable=True),
        sa.Column("phone_number", sa.String(length=32), nullable=True),
        sa.Column("phone_verified", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("email_verified", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("token_version", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("security_alerts_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
    )

    for column in columns_to_add:
        if column.name not in user_columns:
            op.add_column("users", column)

    indexes = {index["name"] for index in sa.inspect(connection).get_indexes("users")}
    if "ix_users_phone_number" not in indexes:
        op.create_index("ix_users_phone_number", "users", ["phone_number"], unique=True)


def downgrade() -> None:
    pass
