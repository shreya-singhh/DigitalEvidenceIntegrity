import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import settings
from app.hashing.sha256 import compute_sha256_file
from app.models.audit_log import AuditLog
from app.models.case import Case
from app.models.chain_of_custody import ChainOfCustody
from app.models.evidence import Evidence
from app.models.report import Report
from app.models.user import User
from app.models.verification_log import VerificationLog
from app.repositories.audit_repository import AuditRepository
from app.repositories.chain_of_custody_repository import ChainOfCustodyRepository
from app.repositories.evidence_repository import EvidenceRepository
from app.services.verification_service import resolve_evidence_path


def generate_case_report(db: Session, case: Case, user: User) -> Path:
    evidence_items = EvidenceRepository(db).get_by_case_id(case.id)
    generated_at = datetime.now(timezone.utc)
    report_evidence: list[dict[str, object]] = []
    evidence_ids = [evidence.id for evidence in evidence_items]
    audit_events = (
        db.query(AuditLog)
        .filter(AuditLog.case_id == case.id)
        .order_by(AuditLog.created_at.asc(), AuditLog.id.asc())
        .all()
    )
    custody_events = (
        db.query(ChainOfCustody)
        .filter(ChainOfCustody.evidence_id.in_(evidence_ids))
        .order_by(ChainOfCustody.timestamp.asc(), ChainOfCustody.id.asc())
        .all()
        if evidence_ids
        else []
    )

    for evidence in evidence_items:
        file_path = resolve_evidence_path(evidence.storage_path)
        current_hash = compute_sha256_file(file_path) if file_path.is_file() else None
        if current_hash is None:
            integrity_status = "MISSING"
        elif current_hash == evidence.sha256_hash:
            integrity_status = "MATCH"
        else:
            integrity_status = "MISMATCH"
        verification_logs = (
            db.query(VerificationLog)
            .filter(VerificationLog.evidence_id == evidence.id)
            .order_by(VerificationLog.created_at.asc(), VerificationLog.id.asc())
            .all()
        )
        latest_verification = verification_logs[-1] if verification_logs else None
        report_evidence.append(
            {
                "evidence_id": evidence.id,
                "filename": evidence.file_name,
                "file_type": evidence.file_type,
                "file_size": evidence.file_size,
                "uploaded_at": evidence.uploaded_at.isoformat(),
                "sha256_stored": evidence.sha256_hash,
                "reference_sha256": evidence.sha256_hash,
                "sha256_current": current_hash,
                "integrity_status": integrity_status,
                "verification_status": latest_verification.status if latest_verification else "PENDING",
                "verification_history": [
                    {
                        "timestamp": log.created_at.isoformat(),
                        "verified_by": log.verifier.username,
                        "status": log.status,
                        "reference_sha256": log.original_hash,
                        "live_sha256": log.calculated_hash,
                        "details": log.details,
                    }
                    for log in verification_logs
                ],
                "integrity_failures": [
                    {
                        "timestamp": log.created_at.isoformat(),
                        "verified_by": log.verifier.username,
                        "reference_sha256": log.original_hash,
                        "live_sha256": log.calculated_hash,
                        "details": log.details,
                    }
                    for log in verification_logs
                    if log.status.upper() in {"FAILED", "MISSING"}
                ],
            }
        )

    report_data = {
        "report_type": "case_integrity",
        "generated_at": generated_at.isoformat(),
        "generated_by": {"id": user.id, "username": user.username},
        "case": {
            "id": case.id,
            "case_number": case.case_number,
            "title": case.title,
            "description": case.description,
            "status": case.status,
            "priority": case.priority,
            "created_by": case.creator_username,
            "created_at": case.created_at.isoformat(),
            "updated_at": case.updated_at.isoformat(),
        },
        "evidence_count": len(report_evidence),
        "evidence": report_evidence,
        "audit_events": [
            {
                "timestamp": event.created_at.isoformat(),
                "user": event.user.username if event.user else None,
                "evidence_id": event.evidence_id,
                "action": event.action,
                "description": event.description,
            }
            for event in audit_events
        ],
        "chain_of_custody": [
            {
                "timestamp": event.timestamp.isoformat(),
                "user": event.user.username,
                "evidence_id": event.evidence_id,
                "action": event.action,
                "description": event.description,
            }
            for event in custody_events
        ],
    }
    settings.report_directory.mkdir(parents=True, exist_ok=True)
    report_path = settings.report_directory / f"case-{case.id}-{uuid.uuid4().hex}.json"
    report_path.write_text(json.dumps(report_data, indent=2, ensure_ascii=False), encoding="utf-8")

    summary = f"Integrity report for {case.case_number}: {len(report_evidence)} evidence record(s)."
    db.add_all(
        [
            Report(
                evidence_id=evidence.id,
                generated_by=user.id,
                report_path=str(report_path),
                summary=summary,
            )
            for evidence in evidence_items
        ]
    )
    db.commit()
    AuditRepository(db).create_log(
        action="REPORT_GENERATED",
        user_id=user.id,
        case_id=case.id,
        entity_type="case_report",
        entity_id=case.id,
        description=summary,
    )
    custody_repository = ChainOfCustodyRepository(db)
    for evidence in evidence_items:
        custody_repository.create(
            evidence_id=evidence.id,
            user_id=user.id,
            action="EVIDENCE_REPORT_GENERATED",
            description=f"Case integrity report generated for {case.case_number}; reference_sha256={evidence.sha256_hash}",
        )
    return report_path
