# Deployment

## Overview

This project uses Docker Compose to run the application with PostgreSQL. The default database is PostgreSQL 16 and the backend connects using the SQLAlchemy PostgreSQL driver.

## Local compose setup

- PostgreSQL container: postgres:16
- Database: digital_evidence_db
- User: evidence_app
- Port: 5432

The backend service should use the PostgreSQL DSN in the format:

postgresql+psycopg://evidence_app:${POSTGRES_PASSWORD}@db:5432/digital_evidence_db

Production deployments should keep the database credentials in environment variables and never commit actual secrets to source control.

## Render services

The current backend Render service is a native Python service with root directory `backend/`, build command `pip install -r requirements.txt`, start command `uvicorn app.main:app --host 0.0.0.0 --port $PORT`, and auto-deploy on commits to `main`. The backend Dockerfile is for Docker-based deployments.

The frontend repository root is `frontend`, build command is `npm ci && npm run build`, and publish directory is `dist`. Set its build-time `VITE_API_BASE_URL` to `https://digitalevidenceintegrity.onrender.com/api`. The API client appends route paths without another `/api` prefix. Keep the frontend's existing SPA rewrite to serve `index.html` for client-side routes.

Configure the backend Render service with:

- `DATABASE_URL`: the existing persistent PostgreSQL connection URL; preserve the current database and credentials. Do not recreate the database.
- `SECRET_KEY`: the existing strong random signing key; do not rotate it during this deployment.
- `DEBUG`: `false`.
- `CORS_ORIGINS`: `https://digital-evidence-frontend.onrender.com` (plus any explicitly trusted development origins only if needed).
- `JWT_ALGORITHM`: `HS256` (only if not already set).
- `ACCESS_TOKEN_EXPIRE_MINUTES`: `30` (only if not already set).
- `UPLOAD_DIRECTORY` and `REPORT_DIRECTORY`: paths on a persistent disk or durable object store. The currently configured backend uses Render's Free compute plan, which does not support persistent disks; files in its container filesystem are ephemeral. Do not rely on that filesystem for evidence or reports. Upgrade to a plan supporting persistent disks and attach one, or configure durable object storage, before depending on production uploads.

`GOOGLE_CLIENT_ID`, `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_FROM_EMAIL`, `SMTP_USE_TLS`, and `PUBLIC_APP_URL` are no longer used. Remove those variables from the backend service after the new backend code is deployed. Do not place secrets in frontend `VITE_` variables.

## Database schema repair

The existing PostgreSQL database must be retained. The migration `c8d2f4a6b901` is additive and idempotent: it adds missing password-auth user profile columns and indexes without deleting or replacing users. Back up the database first. The current Free compute plan does not support Render Shell, so a plan with Shell access (or an equivalent controlled migration runner) is required. After deploying the new backend, inspect the current revision and then upgrade from the backend service's working directory:

```sh
python -m alembic current
python -m alembic upgrade head
```

If `alembic current` reports a revision that is not in the expected migration chain, stop and investigate before upgrading. Do not run schema resets or delete/recreate the PostgreSQL service. `/health/ready` reports whether the database and required user schema are available after the migration.

For local development, copy `backend/.env.example` to `backend/.env` and set local `DATABASE_URL` and `SECRET_KEY`; `.env` files must remain untracked.

Install dependencies and run the backend tests from `backend`:

```powershell
python -m pip install -r requirements.txt
pytest tests/test_auth.py
```
