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
