from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.auth.security import get_current_user
from app.database.session import get_db
from app.models.case import Case
from app.models.evidence import Evidence
from app.models.user import User
from app.schemas.audit import AuditLogResponse
from app.services.audit_service import AuditService

router = APIRouter(prefix="/audit", tags=["Audit"])


@router.get("", response_model=list[AuditLogResponse])
def list_audit_logs(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[AuditLogResponse]:
    service = AuditService(db)
    return service.list_user_logs(current_user.id, skip=skip, limit=limit)


@router.get("/case/{case_id}", response_model=list[AuditLogResponse])
def list_case_audit_logs(
    case_id: int,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[AuditLogResponse]:
    case = db.query(Case).filter(Case.id == case_id).first()
    if case is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
    if case.created_by != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this case")

    service = AuditService(db)
    return service.list_case_logs(case_id, skip=skip, limit=limit)


@router.get("/evidence/{evidence_id}", response_model=list[AuditLogResponse])
def list_evidence_audit_logs(
    evidence_id: int,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[AuditLogResponse]:
    evidence = db.query(Evidence).filter(Evidence.id == evidence_id).first()
    if evidence is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence not found")
    if evidence.case is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
    if evidence.case.created_by != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this evidence")

    service = AuditService(db)
    return service.list_evidence_logs(evidence_id, skip=skip, limit=limit)


@router.get("/{audit_id}", response_model=AuditLogResponse)
def get_audit_log(
    audit_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AuditLogResponse:
    service = AuditService(db)
    log = service.repository.get_log_by_id(audit_id)
    if log is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Audit log not found")

    if log.user_id != current_user.id:
        if log.case_id is not None:
            case = db.query(Case).filter(Case.id == log.case_id).first()
            if case is not None and case.created_by == current_user.id:
                return log
        if log.evidence_id is not None:
            evidence = db.query(Evidence).filter(Evidence.id == log.evidence_id).first()
            if evidence is not None and evidence.case is not None and evidence.case.created_by == current_user.id:
                return log
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this audit log")

    return log
