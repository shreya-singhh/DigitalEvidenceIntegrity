from sqlalchemy import create_engine, text

urls = [
    'postgresql+psycopg://evidence_app:chintu2006@localhost:5432/digital_evidence_db',
    'postgresql+psycopg://postgres@localhost:5432/digital_evidence_db',
    'postgresql+psycopg://postgres:postgres@localhost:5432/digital_evidence_db',
    'postgresql+psycopg://postgres:chintu2006@localhost:5432/digital_evidence_db',
    'postgresql+psycopg://postgres:password@localhost:5432/digital_evidence_db',
    'postgresql+psycopg://postgres:admin@localhost:5432/digital_evidence_db',
]

for url in urls:
    try:
        engine = create_engine(url, isolation_level='AUTOCOMMIT')
        with engine.connect() as conn:
            print('OK', url)
            print('CURRENT_USER', conn.execute(text('SELECT current_user, session_user')).fetchall())
            print('TABLE_OWNERS', conn.execute(text("SELECT tableowner, schemaname, tablename FROM pg_tables WHERE schemaname='public' AND tablename='cases'")).fetchall())
            print('COLUMNS', conn.execute(text("SELECT column_name, data_type, is_nullable, column_default FROM information_schema.columns WHERE table_name='cases' ORDER BY ordinal_position")).fetchall())
            break
    except Exception as exc:
        print('FAIL', url, type(exc).__name__, exc)
