from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.auth.security import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.repositories.audit_repository import AuditRepository
from app.schemas.evidence import EvidenceResponse
from app.schemas.verification import VerificationResult
from app.services.upload_service import get_evidence_record, list_case_evidence, list_user_evidence, upload_evidence
from app.services.verification_service import resolve_evidence_path, verify_evidence, verify_stored_evidence

router = APIRouter(prefix="/evidence", tags=["Evidence"])


@router.get("", response_model=list[EvidenceResponse])
def list_evidence_route(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[EvidenceResponse]:
    return list_user_evidence(db, current_user)


@router.post("/upload", response_model=EvidenceResponse, status_code=status.HTTP_201_CREATED)
def upload_evidence_route(
    case_id: int = Form(...),
    description: str | None = Form(default=None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> EvidenceResponse:
    evidence = upload_evidence(
        db,
        file=file,
        case_id=case_id,
        current_user=current_user,
        description=description,
    )
    return evidence


@router.get("/{evidence_id}", response_model=EvidenceResponse)
def get_evidence_route(
    evidence_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> EvidenceResponse:
    evidence = get_evidence_record(db, evidence_id, current_user)
    AuditRepository(db).create_log(
        action="EVIDENCE_ACCESSED",
        user_id=current_user.id,
        case_id=evidence.case_id,
        evidence_id=evidence.id,
        entity_type="evidence",
        entity_id=evidence.id,
        description=f"Evidence record {evidence.id} viewed",
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    return evidence


@router.get("/{evidence_id}/integrity", response_model=VerificationResult)
def verify_stored_evidence_route(
    evidence_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> VerificationResult:
    return verify_stored_evidence(db, evidence_id, current_user, request=request)


@router.get("/{evidence_id}/download")
def download_evidence_route(
    evidence_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FileResponse:
    result = verify_stored_evidence(db, evidence_id, current_user, request=request)
    evidence = get_evidence_record(db, evidence_id, current_user)
    path = resolve_evidence_path(evidence.storage_path)
    if result.verification_status.value == "MISSING" or not path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence file not found on disk")
    AuditRepository(db).create_log(
        action="EVIDENCE_DOWNLOADED",
        user_id=current_user.id,
        case_id=evidence.case_id,
        evidence_id=evidence.id,
        entity_type="evidence",
        entity_id=evidence.id,
        description=f"Evidence {evidence.id} downloaded; integrity={result.verification_status.value}",
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    return FileResponse(
        path=path,
        media_type=evidence.file_type,
        filename=evidence.file_name,
        headers={"X-Evidence-Integrity": result.verification_status.value},
    )


@router.post("/{evidence_id}/verify", response_model=VerificationResult)
def verify_evidence_route(
    evidence_id: int,
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> VerificationResult:
    return verify_evidence(db, evidence_id, current_user, file=file, request=request)


@router.get("/cases/{case_id}", response_model=list[EvidenceResponse])
def list_case_evidence_route(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[EvidenceResponse]:
    evidence_items = list_case_evidence(db, case_id, current_user)
    return evidence_items
