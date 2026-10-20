from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.auth.security import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.repositories.audit_repository import AuditRepository
from app.repositories.chain_of_custody_repository import ChainOfCustodyRepository
from app.services.metadata_service import MetadataService
from app.services.access_control import require_evidence_access
from app.services.verification_service import resolve_evidence_path

router = APIRouter(prefix="/metadata", tags=["Metadata"])


@router.get("/evidence/{evidence_id}", status_code=status.HTTP_200_OK)
def get_metadata_for_evidence(
    evidence_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    evidence = require_evidence_access(db, evidence_id, current_user.id)

    file_path = resolve_evidence_path(evidence.storage_path)
    if not file_path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence file not found on disk")

    result = MetadataService.extract_metadata_for_file(
        file_path,
        filename=evidence.file_name,
        mime_type=evidence.file_type,
        sha256_hash=evidence.sha256_hash,
    )
    AuditRepository(db).create_log(
        action="METADATA_EXTRACTED",
        user_id=current_user.id,
        case_id=evidence.case_id,
        evidence_id=evidence.id,
        entity_type="metadata",
        entity_id=evidence.id,
        description=f"Metadata accessed for evidence {evidence.id}",
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    ChainOfCustodyRepository(db).create(
        evidence_id=evidence.id,
        user_id=current_user.id,
        action="EVIDENCE_METADATA_VIEWED",
        description=f"Metadata viewed for evidence {evidence.id}; reference_sha256={evidence.sha256_hash}",
    )
    return result
