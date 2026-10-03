from sqlalchemy.orm import Session

from app.models.case import Case
from app.models.evidence import Evidence


class EvidenceRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, evidence_id: int) -> Evidence | None:
        return self.session.query(Evidence).filter(Evidence.id == evidence_id).first()

    def get_by_case_id(self, case_id: int) -> list[Evidence]:
        return (
            self.session.query(Evidence)
            .filter(Evidence.case_id == case_id)
            .order_by(Evidence.uploaded_at.desc())
            .all()
        )

    def get_by_user_id(self, user_id: int) -> list[Evidence]:
        return (
            self.session.query(Evidence)
            .join(Case, Evidence.case_id == Case.id)
            .filter(Case.created_by == user_id)
            .order_by(Evidence.uploaded_at.desc())
            .all()
        )

    def create(
        self,
        *,
        case_id: int,
        owner_id: int,
        file_name: str,
        file_type: str,
        file_size: int,
        storage_path: str,
        sha256_hash: str,
        description: str | None,
        status: str = "uploaded",
    ) -> Evidence:
        evidence = Evidence(
            case_id=case_id,
            owner_id=owner_id,
            file_name=file_name,
            file_type=file_type,
            file_size=file_size,
            storage_path=storage_path,
            sha256_hash=sha256_hash,
            description=description,
            status=status,
        )
        self.session.add(evidence)
        self.session.commit()
        self.session.refresh(evidence)
        return evidence
