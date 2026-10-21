
from sqlalchemy import create_engine, text
from app.core.config import settings

engine = create_engine(settings.database_url)

columns = [
    """
    ALTER TABLE public.users
    ADD COLUMN IF NOT EXISTS full_name VARCHAR(120) NOT NULL DEFAULT ''
    """,
    """
    ALTER TABLE public.users
    ADD COLUMN IF NOT EXISTS terms_accepted_at TIMESTAMP WITHOUT TIME ZONE
    """,
    """
    ALTER TABLE public.users
    ADD COLUMN IF NOT EXISTS phone_number VARCHAR(32)
    """,
    """
    ALTER TABLE public.users
    ADD COLUMN IF NOT EXISTS phone_verified BOOLEAN NOT NULL DEFAULT FALSE
    """,
    """
    ALTER TABLE public.users
    ADD COLUMN IF NOT EXISTS email_verified BOOLEAN NOT NULL DEFAULT FALSE
    """,
    """
    ALTER TABLE public.users
    ADD COLUMN IF NOT EXISTS token_version INTEGER NOT NULL DEFAULT 0
    """,
    """
    ALTER TABLE public.users
    ADD COLUMN IF NOT EXISTS security_alerts_enabled BOOLEAN NOT NULL DEFAULT TRUE
    """,
    """
    CREATE UNIQUE INDEX IF NOT EXISTS ix_users_phone_number
    ON public.users (phone_number)
    """,
]

try:
    with engine.begin() as connection:
        db_name = connection.execute(
            text("SELECT current_database()")
        ).scalar_one()

        if db_name != "digital_evidence_db":
            raise RuntimeError(
                f"Unexpected database: {db_name}. No changes applied."
            )

        print("Connected to:", db_name)

        for statement in columns:
            connection.execute(text(statement))

        print("Schema update completed.")

        result = connection.execute(
            text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name = 'users'
                ORDER BY ordinal_position
            """)
        ).scalars().all()

        print("Current users columns:", result)

finally:
    engine.dispose()
