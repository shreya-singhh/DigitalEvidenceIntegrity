# Digital Evidence Integrity

## Overview

A full-stack application for managing digital evidence, case records, metadata extraction, verification workflows, and audit logging.

## Technology Stack

- Database: PostgreSQL
- ORM: SQLAlchemy
- Migrations: Alembic
- Backend: FastAPI
- Frontend: React + TypeScript
- Hashing: SHA-256

## Structure

- backend/: FastAPI backend and database configuration
- frontend/: React + Vite frontend
- database/: PostgreSQL schema and seed scripts
- docs/: architecture and deployment documentation

## Setup

1. Create a local PostgreSQL database named digital_evidence_db.
2. Configure the backend environment using the values in backend/.env.example.
3. Start the database with Docker Compose or a local PostgreSQL instance.
4. Install backend dependencies and start the API from the backend folder.

## Local development

The default PostgreSQL URL is:

postgresql+psycopg://evidence_app:YOUR_PASSWORD@localhost:5432/digital_evidence_db

This project no longer uses Oracle XE or Oracle database drivers.
