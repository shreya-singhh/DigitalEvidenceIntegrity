from sqlalchemy import create_engine, text
from app.core.config import settings

engine = create_engine(settings.database_url)
with engine.connect() as conn:
    rows = conn.execute(text("SELECT column_name, data_type, is_nullable, column_default FROM information_schema.columns WHERE table_name = 'cases' ORDER BY ordinal_position")).fetchall()
    for row in rows:
        print(row)
    print('---')
    try:
        print(conn.execute(text("SELECT version_num FROM alembic_version")).fetchall())
    except Exception as exc:
        print('alembic_version_error:', type(exc).__name__, exc)
