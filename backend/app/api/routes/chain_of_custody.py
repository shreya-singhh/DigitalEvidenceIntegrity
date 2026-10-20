from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.security import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.repositories.chain_of_custody_repository import ChainOfCustodyRepository
from app.schemas.chain_of_custody import (
    ChainOfCustodyEventResponse,
    EvidenceCustodyResponse,
)
from app.services.access_control import require_evidence_access

router = APIRouter(prefix="/chain-of-custody", tags=["Chain of Custody"])


@router.get("/evidence/{evidence_id}", response_model=EvidenceCustodyResponse)
def get_evidence_custody(
    evidence_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> EvidenceCustodyResponse:
    evidence = require_evidence_access(db, evidence_id, current_user.id)

    events = ChainOfCustodyRepository(db).list_for_evidence(evidence.id)
    return EvidenceCustodyResponse(
        evidence_id=evidence.id,
        file_name=evidence.file_name,
        case_id=evidence.case_id,
        case_number=evidence.case.case_number,
        reference_hash=evidence.sha256_hash,
        events=[
            ChainOfCustodyEventResponse(
                id=event.id,
                evidence_id=event.evidence_id,
                user_id=event.user_id,
                username=event.user.username,
                action=event.action,
                description=event.description,
                timestamp=event.timestamp,
            )
            for event in events
        ],
    )
