from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.auth.security import get_current_user
from app.database.session import get_db
from app.models.case_access import CaseAccess
from app.models.user import User
from app.repositories.audit_repository import AuditRepository
from app.schemas.case_access import CaseAccessGrantRequest, CaseAccessResponse
from app.schemas.case import CaseCreate, CaseResponse, CaseUpdate
from app.services.case_service import CaseService
from app.services.access_control import require_case_owner

router = APIRouter(prefix="/cases", tags=["Cases"])


@router.post("", response_model=CaseResponse, status_code=status.HTTP_201_CREATED)
def create_case(
    case_in: CaseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CaseResponse:
    service = CaseService(db)
    case = service.create_case(current_user.id, case_in)
    return case


@router.get("", response_model=list[CaseResponse])
def list_cases(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[CaseResponse]:
    service = CaseService(db)
    return service.list_cases(current_user.id)


@router.get("/{case_id}", response_model=CaseResponse)
def get_case(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CaseResponse:
    service = CaseService(db)
    return service.get_case(case_id, current_user.id)


@router.patch("/{case_id}", response_model=CaseResponse)
def update_case(
    case_id: int,
    case_in: CaseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CaseResponse:
    service = CaseService(db)
    return service.update_case(case_id, current_user.id, case_in)


@router.get("/{case_id}/access", response_model=list[CaseAccessResponse])
def list_case_access(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[CaseAccessResponse]:
    require_case_owner(db, case_id, current_user.id)
    grants = (
        db.query(CaseAccess, User)
        .join(User, User.id == CaseAccess.user_id)
        .filter(CaseAccess.case_id == case_id)
        .order_by(CaseAccess.granted_at.asc())
        .all()
    )
    return [
        CaseAccessResponse(
            user_id=grant.user_id,
            username=granted_user.username,
            email=granted_user.email,
            granted_by=grant.granted_by,
            granted_at=grant.granted_at,
        )
        for grant, granted_user in grants
    ]


@router.post("/{case_id}/access", response_model=CaseAccessResponse, status_code=status.HTTP_201_CREATED)
def grant_case_access(
    case_id: int,
    access_in: CaseAccessGrantRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CaseAccessResponse:
    require_case_owner(db, case_id, current_user.id)
    investigator = (
        db.query(User)
        .filter(func.lower(User.email) == access_in.email.lower(), User.is_active.is_(True))
        .first()
    )
    if investigator is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Registered active user not found")
    if investigator.id == current_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Case owner already has access")
    if db.query(CaseAccess.id).filter(
        CaseAccess.case_id == case_id,
        CaseAccess.user_id == investigator.id,
    ).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User already has case access")

    grant = CaseAccess(case_id=case_id, user_id=investigator.id, granted_by=current_user.id)
    db.add(grant)
    db.commit()
    db.refresh(grant)
    AuditRepository(db).create_log(
        action="CASE_ACCESS_GRANTED",
        user_id=current_user.id,
        case_id=case_id,
        entity_type="case_access",
        entity_id=grant.id,
        description=f"Case access granted to user {investigator.id}",
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    return CaseAccessResponse(
        user_id=investigator.id,
        username=investigator.username,
        email=investigator.email,
        granted_by=grant.granted_by,
        granted_at=grant.granted_at,
    )


@router.delete("/{case_id}/access/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_case_access(
    case_id: int,
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    require_case_owner(db, case_id, current_user.id)
    grant = db.query(CaseAccess).filter(
        CaseAccess.case_id == case_id,
        CaseAccess.user_id == user_id,
    ).first()
    if grant is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case access grant not found")
    grant_id = grant.id
    db.delete(grant)
    db.commit()
    AuditRepository(db).create_log(
        action="CASE_ACCESS_REVOKED",
        user_id=current_user.id,
        case_id=case_id,
        entity_type="case_access",
        entity_id=grant_id,
        description=f"Case access revoked from user {user_id}",
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
