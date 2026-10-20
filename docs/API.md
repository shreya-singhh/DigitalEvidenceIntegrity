# API

## Overview

Document API endpoints, request shapes, and response shapes.

## Authentication

Protected routes require the existing JWT bearer token. Google sign-in continues to use the same authentication flow and receives the same case permissions as other authenticated users.

### Email OTP sign-in

Email OTP uses existing registered DEIS accounts and the normal JWT session:

| Method | Route | Purpose |
| --- | --- | --- |
| `POST` | `/api/auth/email-otp/send` | Send a six-digit, five-minute code to an email address; always returns a generic eligibility message |
| `POST` | `/api/auth/email-otp/verify` | Verify `{"email":"user@example.com","code":"123456"}` and return the regular bearer token |

Configure SMTP on the backend before using these routes. Codes are HMAC-hashed at rest, expire after five minutes, are single-use, and permit at most five guesses. Sending is limited by IP and email with a 60-second resend cooldown. Unknown addresses receive the same send response but cannot sign in. A successful code verifies the email on an existing active account whose terms were accepted; OTP never creates accounts or changes roles.

## Case access

Cases are visible to their creator and to active registered users with a case-level grant. A case creator can manage grants using the recipient's registered email:

| Method | Route | Purpose |
| --- | --- | --- |
| `GET` | `/api/cases/{case_id}/access` | List grants (case creator only) |
| `POST` | `/api/cases/{case_id}/access` | Grant access with `{"email":"investigator@example.com"}` (case creator only) |
| `DELETE` | `/api/cases/{case_id}/access/{user_id}` | Revoke access (case creator only) |

Grant and revoke operations are written to the case audit trail. Authorization checks use the current database grant on each request, so revocation takes effect immediately. Investigators have read, evidence-verification, and download access; case updates and evidence uploads remain owner-only.

## Evidence access and integrity

| Method | Route | Purpose |
| --- | --- | --- |
| `GET` | `/api/evidence/{evidence_id}` | Read the evidence record; requires case access |
| `GET` | `/api/evidence/{evidence_id}/integrity` | Recalculate SHA-256 from the stored original and compare it with the registration reference |
| `GET` | `/api/evidence/{evidence_id}/download` | Download the stored original; requires case access and returns `X-Evidence-Integrity: VERIFIED`, `FAILED`, or `MISSING` |
| `POST` | `/api/evidence/{evidence_id}/verify` | Compare the uploaded file with the registered reference; response target is `SUBMITTED_FILE` |

Stored-original checks return `verification_target: "STORED_ORIGINAL"` and record the actor, result, and hashes. Submitted-file comparisons return `verification_target: "SUBMITTED_FILE"`; a failed comparison does not by itself mean that the server's stored original changed. Each newly uploaded copy creates its own evidence record and reference hash.

Evidence retrieval, downloads, verification, access changes, and existing metadata, chain-of-custody, report, and audit operations enforce case access in the backend. Non-owners cannot update or delete registered evidence through the API.
