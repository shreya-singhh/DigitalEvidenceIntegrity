from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.case import Case
from app.models.case_access import CaseAccess
from app.models.evidence import Evidence


def can_access_case(db: Session, case: Case, user_id: int) -> bool:
    if case.created_by == user_id:
        return True
    return (
        db.query(CaseAccess.id)
        .filter(CaseAccess.case_id == case.id, CaseAccess.user_id == user_id)
        .first()
        is not None
    )


def require_case_access(db: Session, case_id: int, user_id: int) -> Case:
    case = db.query(Case).filter(Case.id == case_id).first()
    if case is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
    if not can_access_case(db, case, user_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized for this case")
    return case


def require_case_owner(db: Session, case_id: int, user_id: int) -> Case:
    case = db.query(Case).filter(Case.id == case_id).first()
    if case is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
    if case.created_by != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the case owner can manage access")
    return case


def require_evidence_access(db: Session, evidence_id: int, user_id: int) -> Evidence:
    evidence = db.query(Evidence).filter(Evidence.id == evidence_id).first()
    if evidence is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence not found")
    if evidence.case is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
    if not can_access_case(db, evidence.case, user_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this evidence")
    return evidence
