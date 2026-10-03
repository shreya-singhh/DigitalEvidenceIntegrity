from sqlalchemy.orm import Session

from app.models.chain_of_custody import ChainOfCustody


class ChainOfCustodyRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(
        self,
        *,
        evidence_id: int,
        user_id: int,
        action: str,
        description: str | None = None,
    ) -> ChainOfCustody:
        event = ChainOfCustody(
            evidence_id=evidence_id,
            user_id=user_id,
            action=action,
            description=description,
        )
        self.session.add(event)
        self.session.commit()
        self.session.refresh(event)
        return event

    def list_for_evidence(self, evidence_id: int) -> list[ChainOfCustody]:
        return (
            self.session.query(ChainOfCustody)
            .filter(ChainOfCustody.evidence_id == evidence_id)
            .order_by(ChainOfCustody.timestamp.asc(), ChainOfCustody.id.asc())
            .all()
        )
