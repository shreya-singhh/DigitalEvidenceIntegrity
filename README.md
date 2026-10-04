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
