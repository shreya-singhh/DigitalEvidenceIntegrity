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

## Render authentication configuration

Run the backend as a Render web service with the repository's `backend/Dockerfile`. Configure `DATABASE_URL`, `SECRET_KEY`, and `CORS_ORIGINS` in the Render environment settings. Set `CORS_ORIGINS` to the exact HTTPS origin of the deployed frontend (comma-separated only when using multiple trusted origins), and set `PUBLIC_APP_URL` to that frontend origin. Do not set `CORS_ORIGINS=*` for production.

Apply schema changes from the backend working directory before deploying the new code:

```powershell
alembic upgrade head
```

Authentication providers are optional but remain unavailable until configured:

- Google Identity Services: set `GOOGLE_CLIENT_ID` to the OAuth web client ID. Add the deployed frontend origin to the authorized JavaScript origins in Google Cloud. The backend verifies the returned ID token and does not need a Google client secret for this credential flow.
- Password recovery and email verification: set `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_FROM_EMAIL`, and `SMTP_USE_TLS` to the transactional email service credentials.

Unset providers are not simulated: Google sign-in stays unavailable, and email recovery/verification endpoints return a setup error. Store provider credentials only in Render environment settings. The browser receives only the public Google client ID through `/api/auth/options`.

The backend also persists authentication rate-limit counters in PostgreSQL: password/Google sign-in is limited per client IP, and registration and recovery requests have per-IP limits. Ensure Render's trusted proxy configuration is restricted so client IP-based limits cannot be spoofed through untrusted forwarded headers.

For local development, copy `backend/.env.example` to `backend/.env`, replace `SECRET_KEY` and the database URL with local values, and set provider variables only when using real provider accounts. `.env` files must remain untracked.

After configuration, install dependencies and run the focused backend tests:

```powershell
python -m pip install -r requirements.txt
pytest tests/test_auth.py
```
