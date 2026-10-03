from __future__ import annotations

import hashlib
from datetime import datetime
from pathlib import Path

from fastapi import HTTPException, Request, UploadFile, status
from sqlalchemy.orm import Session

from app.models.chain_of_custody import ChainOfCustody
from app.models.evidence import Evidence
from app.models.user import User
from app.models.verification_log import VerificationLog
from app.schemas.verification import VerificationResult, VerificationStatus
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
    evidence = db.query(Evidence).filter(Evidence.id == evidence_id).first()
    if evidence is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence not found")

    if evidence.case is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")

    if evidence.case.created_by != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this evidence")

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
            verification_status=VerificationStatus.VERIFIED,
            stored_hash=reference_hash,
            current_hash=current_hash,
            verified_at=verified_at,
            message="Evidence integrity verified successfully.",
        )

    details = (
        f"Result=INTEGRITY FAILED; reason=uploaded file does not match the registered reference; "
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
        verification_status=VerificationStatus.FAILED,
        stored_hash=reference_hash,
        current_hash=current_hash,
        verified_at=verified_at,
        message="INTEGRITY FAILED: possible tampering or modification detected.",
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
