import importlib.util
from pathlib import Path

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, inspect, text


MIGRATION_PATH = (
    Path(__file__).parents[1]
    / "alembic"
    / "versions"
    / "c8d2f4a6b901_ensure_password_auth_user_columns.py"
)


def test_profile_migration_adds_missing_columns_and_preserves_users():
    spec = importlib.util.spec_from_file_location("profile_migration", MIGRATION_PATH)
    assert spec and spec.loader
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)

    engine = create_engine("sqlite://")
    with engine.begin() as connection:
        connection.execute(
            text(
                "CREATE TABLE users ("
                "id INTEGER PRIMARY KEY, username VARCHAR(50) NOT NULL, "
                "email VARCHAR(255) NOT NULL, hashed_password VARCHAR(255) NOT NULL, "
                "created_at DATETIME NOT NULL, is_active BOOLEAN NOT NULL)"
            )
        )
        connection.execute(
            text(
                "INSERT INTO users (id, username, email, hashed_password, created_at, is_active) "
                "VALUES (1, 'legacy_user', 'legacy@example.com', 'existing-hash', "
                "'2026-01-01 00:00:00', 1)"
            )
        )

        context = MigrationContext.configure(connection)
        with Operations.context(context):
            migration.upgrade()
            migration.upgrade()

        columns = {column["name"] for column in inspect(connection).get_columns("users")}
        row = connection.execute(
            text(
                "SELECT username, email, hashed_password, full_name, token_version "
                "FROM users WHERE id = 1"
            )
        ).one()

    assert {
        "full_name",
        "terms_accepted_at",
        "phone_number",
        "phone_verified",
        "email_verified",
        "token_version",
        "security_alerts_enabled",
    } <= columns
    assert tuple(row) == ("legacy_user", "legacy@example.com", "existing-hash", "", 0)
