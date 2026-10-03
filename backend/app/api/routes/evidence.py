from fastapi import APIRouter, Depends, File, Form, Request, UploadFile, status
from sqlalchemy.orm import Session

from app.auth.security import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.schemas.evidence import EvidenceResponse
from app.schemas.verification import VerificationResult
from app.services.upload_service import get_evidence_record, list_case_evidence, list_user_evidence, upload_evidence
from app.services.verification_service import verify_evidence

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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> EvidenceResponse:
    evidence = get_evidence_record(db, evidence_id, current_user)
    return evidence


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
