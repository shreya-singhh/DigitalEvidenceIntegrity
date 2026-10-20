from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.auth.security import get_current_user
from app.database.session import get_db
from app.models.audit_log import AuditLog
from app.models.case import Case
from app.models.case_access import CaseAccess
from app.models.evidence import Evidence
from app.models.user import User
from app.schemas.audit import AuditLogResponse
from app.services.audit_service import AuditService
from app.services.access_control import require_case_access, require_evidence_access

router = APIRouter(prefix="/audit", tags=["Audit"])


@router.get("", response_model=list[AuditLogResponse])
def list_audit_logs(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[AuditLogResponse]:
    return (
        db.query(AuditLog)
        .outerjoin(Evidence, AuditLog.evidence_id == Evidence.id)
        .outerjoin(Case, Case.id == func.coalesce(AuditLog.case_id, Evidence.case_id))
        .outerjoin(CaseAccess, CaseAccess.case_id == Case.id)
        .filter(
            AuditLog.user_id == current_user.id,
            or_(
                func.coalesce(AuditLog.case_id, Evidence.case_id).is_(None),
                Case.created_by == current_user.id,
                CaseAccess.user_id == current_user.id,
            ),
        )
        .distinct()
        .order_by(AuditLog.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


@router.get("/case/{case_id}", response_model=list[AuditLogResponse])
def list_case_audit_logs(
    case_id: int,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[AuditLogResponse]:
    require_case_access(db, case_id, current_user.id)

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
    require_evidence_access(db, evidence_id, current_user.id)

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

    case_id = log.case_id
    if case_id is None and log.evidence_id is not None:
        evidence = db.query(Evidence).filter(Evidence.id == log.evidence_id).first()
        case_id = evidence.case_id if evidence is not None else None
    if case_id is not None:
        require_case_access(db, case_id, current_user.id)
    elif log.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this audit log")

    return log
