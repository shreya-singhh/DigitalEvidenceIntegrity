from __future__ import annotations

import hashlib
from datetime import datetime
from pathlib import Path

from fastapi import Request, UploadFile
from sqlalchemy.orm import Session

from app.models.chain_of_custody import ChainOfCustody
from app.models.audit_log import AuditLog
from app.models.evidence import Evidence
from app.models.user import User
from app.models.verification_log import VerificationLog
from app.schemas.verification import VerificationResult, VerificationStatus
from app.services.access_control import require_evidence_access
from app.services.audit_service import AuditService


def resolve_evidence_path(storage_path: str) -> Path:
    candidate = Path(storage_path)
    if candidate.is_absolute() and candidate.exists():
        return candidate

    candidates = [
        Path.cwd() / storage_path,
        Path.cwd().resolve() / storage_path,
    ]

    if Path.cwd().name == "backend":
        candidates.append(Path.cwd().resolve().parent / storage_path)

    for path in candidates:
        if path.exists():
            return path

    return candidate


def _hash_uploaded_file(file: UploadFile) -> str:
    digest = hashlib.sha256()
    file.file.seek(0)
    while chunk := file.file.read(1024 * 1024):
        digest.update(chunk)
    file.file.seek(0)
    return digest.hexdigest()


def verify_evidence(
    db: Session,
    evidence_id: int,
    current_user: User,
    *,
    file: UploadFile,
    request: Request | None = None,
) -> VerificationResult:
    evidence = require_evidence_access(db, evidence_id, current_user.id)

    reference_hash = evidence.sha256_hash
    current_hash = _hash_uploaded_file(file)
    verified_at = datetime.utcnow()

    if current_hash == reference_hash:
        details = (
            f"Result=VERIFIED; reason=uploaded file matches the registered reference; "
            f"reference_sha256={reference_hash}; live_sha256={current_hash}"
        )
        _record_verification(
            db,
            evidence,
            current_user,
            reference_hash,
            current_hash,
            "VERIFIED",
            details,
        )
        AuditService(db).log_verification_success(
            user=current_user,
            case_id=evidence.case_id,
            evidence_id=evidence.id,
            request=request,
            description=details,
        )
        _record_custody_event(db, evidence, current_user, "EVIDENCE_VERIFIED", details)
        return VerificationResult(
            evidence_id=evidence.id,
            verification_target="SUBMITTED_FILE",
            verification_status=VerificationStatus.VERIFIED,
            stored_hash=reference_hash,
            current_hash=current_hash,
            verified_at=verified_at,
            message="The submitted comparison file matches the registered reference.",
        )

    details = (
        f"Result=COMPARISON FAILED; reason=submitted comparison file does not match the registered reference; "
        f"reference_sha256={reference_hash}; live_sha256={current_hash}"
    )
    _record_verification(
        db,
        evidence,
        current_user,
        reference_hash,
        current_hash,
        "FAILED",
        details,
    )
    AuditService(db).log_verification_failed(
        user=current_user,
        case_id=evidence.case_id,
        evidence_id=evidence.id,
        request=request,
        description=details,
    )
    _record_custody_event(db, evidence, current_user, "EVIDENCE_VERIFICATION_FAILED", details)
    return VerificationResult(
        evidence_id=evidence.id,
        verification_target="SUBMITTED_FILE",
        verification_status=VerificationStatus.FAILED,
        stored_hash=reference_hash,
        current_hash=current_hash,
        verified_at=verified_at,
        message=(
            "The submitted comparison file does not match the registered reference. "
            "This result alone does not establish that the stored original was modified."
        ),
    )


def verify_stored_evidence(
    db: Session,
    evidence_id: int,
    current_user: User,
    *,
    request: Request | None = None,
) -> VerificationResult:
    evidence = require_evidence_access(db, evidence_id, current_user.id)
    path = resolve_evidence_path(evidence.storage_path)
    verified_at = datetime.utcnow()

    if path.is_file():
        current_hash = hashlib.sha256()
        with path.open("rb") as stored_file:
            while chunk := stored_file.read(1024 * 1024):
                current_hash.update(chunk)
        calculated_hash = current_hash.hexdigest()
        verified = calculated_hash == evidence.sha256_hash
        result_status = VerificationStatus.VERIFIED if verified else VerificationStatus.FAILED
        reason = "stored original matches the registered reference" if verified else "stored original does not match the registered reference"
        message = (
            "Stored original integrity verified successfully."
            if verified
            else "INTEGRITY FAILED: the stored original does not match its registered SHA-256 reference."
        )
        log_status = "VERIFIED" if verified else "FAILED"
    else:
        calculated_hash = None
        result_status = VerificationStatus.MISSING
        reason = "stored original is missing"
        message = "INTEGRITY FAILED: the stored original file is missing."
        log_status = "MISSING"

    details = (
        f"Result={log_status}; reason={reason}; reference_sha256={evidence.sha256_hash}; "
        f"live_sha256={calculated_hash or 'MISSING'}"
    )
    db.add(
        VerificationLog(
            evidence_id=evidence.id,
            verified_by=current_user.id,
            original_hash=evidence.sha256_hash,
            calculated_hash=calculated_hash or "",
            verification_target="STORED_ORIGINAL",
            status=log_status,
            details=details,
        )
    )
    db.add(
        ChainOfCustody(
            evidence_id=evidence.id,
            user_id=current_user.id,
            action="EVIDENCE_VERIFIED" if result_status == VerificationStatus.VERIFIED else "EVIDENCE_VERIFICATION_FAILED",
            description=details,
        )
    )
    db.add(
        AuditLog(
            user_id=current_user.id,
            case_id=evidence.case_id,
            evidence_id=evidence.id,
            action=(
                "EVIDENCE_VERIFIED"
                if result_status == VerificationStatus.VERIFIED
                else "EVIDENCE_VERIFICATION_FAILED"
            ),
            entity_type="evidence",
            entity_id=evidence.id,
            description=details,
            ip_address=request.client.host if request and request.client else None,
            user_agent=request.headers.get("user-agent") if request else None,
        )
    )
    db.commit()
    return VerificationResult(
        evidence_id=evidence.id,
        verification_target="STORED_ORIGINAL",
        verification_status=result_status,
        stored_hash=evidence.sha256_hash,
        current_hash=calculated_hash,
        verified_at=verified_at,
        message=message,
    )


def _record_verification(
    db: Session,
    evidence: Evidence,
    user: User,
    reference_hash: str,
    calculated_hash: str,
    status_value: str,
    details: str,
) -> None:
    db.add(
        VerificationLog(
            evidence_id=evidence.id,
            verified_by=user.id,
            original_hash=reference_hash,
            calculated_hash=calculated_hash,
            verification_target="SUBMITTED_FILE",
            status=status_value,
            details=details,
        )
    )
    db.commit()


def _record_custody_event(
    db: Session,
    evidence: Evidence,
    user: User,
    action: str,
    description: str,
) -> None:
    db.add(
        ChainOfCustody(
            evidence_id=evidence.id,
            user_id=user.id,
            action=action,
            description=description,
        )
    )
    db.commit()
