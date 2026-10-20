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

- Google Identity Services: set `GOOGLE_CLIENT_ID` on the backend Render service to the OAuth **Web application** client ID. This is the backend's expected ID-token audience and is returned by `/api/auth/options` for the frontend Google button; no separate frontend client-ID variable is needed. The ID is public and is not a client secret.
- In Google Cloud Console, open **APIs & Services → Credentials**, edit that same OAuth web client, and add `https://digital-evidence-frontend.onrender.com` under **Authorized JavaScript origins**. The current frontend flow uses the Google Identity Services popup callback and posts its ID token to the existing backend endpoint, so it does not require an authorized redirect URI. Do not add a client secret to the frontend or repository.
- After setting `GOOGLE_CLIENT_ID`, save the backend Render environment so the service restarts. Redeploy/rebuild the frontend when deploying frontend code changes; it reads the client ID at runtime from `/api/auth/options`.
- The backend verifies the token signature, expiry, audience, and issuer before using its claims. Keep `CORS_ORIGINS` set to `https://digital-evidence-frontend.onrender.com` so the browser can reach the API.
- In the Render frontend service, set the build environment variable `VITE_API_BASE_URL` to `https://digitalevidenceintegrity.onrender.com/api`. Do not set a second Google client ID on the frontend; `/api/auth/options` provides the same public ID the backend validates as its audience.
- Password recovery and email verification: set `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_FROM_EMAIL`, and `SMTP_USE_TLS` to the transactional email service credentials.

Unset providers are not simulated: Google sign-in stays unavailable, and email recovery/verification endpoints return a setup error. Store provider credentials only in Render environment settings. The browser receives only the public Google client ID through `/api/auth/options`.

The backend also persists authentication rate-limit counters in PostgreSQL: password/Google sign-in is limited per client IP, and registration and recovery requests have per-IP limits. Ensure Render's trusted proxy configuration is restricted so client IP-based limits cannot be spoofed through untrusted forwarded headers.

For local development, copy `backend/.env.example` to `backend/.env`, replace `SECRET_KEY` and the database URL with local values, and set provider variables only when using real provider accounts. `.env` files must remain untracked.

After configuration, install dependencies and run the focused backend tests:

```powershell
python -m pip install -r requirements.txt
pytest tests/test_auth.py
```
