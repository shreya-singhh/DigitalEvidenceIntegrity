# Digital Evidence Integrity System

## Overview

The **Digital Evidence Integrity System (DEIS)** is a full-stack web application designed to manage and verify the integrity of digital evidence.

The system allows users to create and manage investigation cases, register digital evidence, calculate SHA-256 cryptographic hashes, extract file metadata, verify evidence integrity, maintain chain-of-custody records, generate audit logs, and produce evidence-related reports.

The primary purpose of the system is to determine whether a digital evidence file has remained unchanged after its initial registration. During verification, the system compares the newly calculated SHA-256 hash with the reference hash stored for the original evidence.

### Key Features

- Case management
- Digital evidence registration and upload
- SHA-256 evidence fingerprint generation
- Evidence integrity verification
- Tamper detection through hash comparison
- Metadata extraction
- Chain-of-custody tracking
- Audit logging
- Evidence verification records
- Case-based reports
- Secure authentication using JWT
- PostgreSQL database storage
- Web-based dashboard

## Live Demo

**Frontend:**
https://digital-evidence-frontend.onrender.com

**Backend API / Swagger Documentation:**
https://digitalevidenceintegrity.onrender.com/docs

> The application is deployed using Render. The backend API and PostgreSQL database are hosted separately from the React frontend.

## Technology Stack

- **Frontend:** React, TypeScript, Vite
- **Backend:** FastAPI, Python
- **Database:** PostgreSQL
- **ORM:** SQLAlchemy
- **Migrations:** Alembic
- **Authentication:** JWT
- **Hashing:** SHA-256
- **Metadata Extraction:** Pillow, pypdf, python-docx, Mutagen
- **API Communication:** Axios
- **Deployment:** Render

## Setup

1. Create a local PostgreSQL database named digital_evidence_db.
2. Configure the backend environment using the values in backend/.env.example.
3. Start the database with Docker Compose or a local PostgreSQL instance.
4. Install backend dependencies and start the API from the backend folder.

## Authentication providers

Password login and registration use the existing JWT API. Optional Google sign-in and SMTP password recovery are enabled only when configured in backend environment settings. See [Deployment](./docs/Deployment.md) for Render environment setup and migration commands. Never add real provider credentials or production secrets to `.env.example` or source control.

## Local development

The default PostgreSQL URL is:

postgresql+psycopg://evidence_app:YOUR_PASSWORD@localhost:5432/digital_evidence_db

This project no longer uses Oracle XE or Oracle database drivers.

## System Structure

```text
DigitalEvidenceIntegrity/
│
├── backend/
│   ├── app/
│   ├── tests/
│   ├── alembic/
│   ├── Dockerfile
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   ├── public/
│   ├── package.json
│   └── vite.config.ts
│
├── database/
│   ├── schema/
│   └── seed/
│
├── docs/
│   ├── architecture/
│   └── deployment/
│
├── uploads/
├── reports/
├── docker-compose.yml
└── README.md
