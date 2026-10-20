
"""add authentication profile and challenge metadata

Revision ID: 36a1b9f4d2ce
Revises: 91821f4a5ef7
Create Date: 2026-10-19 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "36a1b9f4d2ce"
down_revision: Union[str, Sequence[str], None] = "91821f4a5ef7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    # Add only missing columns to the existing users table.
    user_columns = {
        col["name"] for col in inspector.get_columns("users")
    }

    columns_to_add = [
        sa.Column(
            "full_name", sa.String(120),
            nullable=False, server_default=""
        ),
        sa.Column("terms_accepted_at", sa.DateTime(), nullable=True),
        sa.Column("phone_number", sa.String(32), nullable=True),
        sa.Column(
            "phone_verified", sa.Boolean(),
            nullable=False, server_default=sa.false()
        ),
        sa.Column(
            "email_verified", sa.Boolean(),
            nullable=False, server_default=sa.false()
        ),
        sa.Column("google_subject", sa.String(255), nullable=True),
        sa.Column(
            "token_version", sa.Integer(),
            nullable=False, server_default="0"
        ),
        sa.Column(
            "security_alerts_enabled", sa.Boolean(),
            nullable=False, server_default=sa.true()
        ),
    ]

    for column in columns_to_add:
        if column.name not in user_columns:
            op.add_column("users", column)

    # Refresh index metadata after adding the columns.
    inspector = sa.inspect(conn)
    user_indexes = {
        index["name"] for index in inspector.get_indexes("users")
    }

    if "ix_users_phone_number" not in user_indexes:
        op.create_index(
            "ix_users_phone_number",
            "users",
            ["phone_number"],
            unique=True,
        )

    if "ix_users_google_subject" not in user_indexes:
        op.create_index(
            "ix_users_google_subject",
            "users",
            ["google_subject"],
            unique=True,
        )

    # These tables already exist in the local database.
    # Validate their columns instead of recreating them.
    expected_columns = {
        "auth_challenges": {
            "id", "user_id", "purpose", "token_hash",
            "expires_at", "used_at", "created_at",
        },
        "auth_rate_limits": {
            "id", "action", "key_hash", "created_at",
        },
    }

    table_names = set(inspector.get_table_names())

    for table_name, expected in expected_columns.items():
        if table_name not in table_names:
            raise RuntimeError(
                f"Expected existing table '{table_name}' is missing. "
                "Create and validate it in a separate migration."
            )

        actual = {
            col["name"]
            for col in inspector.get_columns(table_name)
        }
        missing = expected - actual

        if missing:
            raise RuntimeError(
                f"Table '{table_name}' is missing columns: "
                f"{sorted(missing)}. Repair its schema before continuing."
            )


def downgrade() -> None:
    # The authentication tables predated this migration in this database.
    # Preserve them and their data during downgrade.
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    user_indexes = {
        index["name"] for index in inspector.get_indexes("users")
    }

    if "ix_users_google_subject" in user_indexes:
        op.drop_index("ix_users_google_subject", table_name="users")

    if "ix_users_phone_number" in user_indexes:
        op.drop_index("ix_users_phone_number", table_name="users")

    user_columns = {
        col["name"] for col in sa.inspect(conn).get_columns("users")
    }

    for column_name in [
        "security_alerts_enabled",
        "token_version",
        "google_subject",
        "email_verified",
        "phone_verified",
        "phone_number",
        "terms_accepted_at",
        "full_name",
    ]:
        if column_name in user_columns:
            op.drop_column("users", column_name)
