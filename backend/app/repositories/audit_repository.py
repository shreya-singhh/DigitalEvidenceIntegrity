from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


class AuditRepository:
    def __init__(self, session: Session):
        self.session = session

    def create_log(
        self,
        *,
        action: str,
        user_id: int | None = None,
        case_id: int | None = None,
        evidence_id: int | None = None,
        entity_type: str | None = None,
        entity_id: int | None = None,
        description: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> AuditLog:
        log = AuditLog(
            user_id=user_id,
            case_id=case_id,
            evidence_id=evidence_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            description=description,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        self.session.add(log)
        self.session.commit()
        self.session.refresh(log)
        return log

    def get_log_by_id(self, audit_id: int) -> AuditLog | None:
        return self.session.query(AuditLog).filter(AuditLog.id == audit_id).first()

    def list_logs(self, *, skip: int = 0, limit: int = 50, user_id: int | None = None) -> list[AuditLog]:
        query = self.session.query(AuditLog)
        if user_id is not None:
            query = query.filter(AuditLog.user_id == user_id)
        return query.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit).all()

    def list_logs_by_case(self, case_id: int, *, skip: int = 0, limit: int = 50) -> list[AuditLog]:
        return (
            self.session.query(AuditLog)
            .filter(AuditLog.case_id == case_id)
            .order_by(AuditLog.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def list_logs_by_evidence(self, evidence_id: int, *, skip: int = 0, limit: int = 50) -> list[AuditLog]:
        return (
            self.session.query(AuditLog)
            .filter(AuditLog.evidence_id == evidence_id)
            .order_by(AuditLog.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def list_logs_by_user(self, user_id: int, *, skip: int = 0, limit: int = 50) -> list[AuditLog]:
        return (
            self.session.query(AuditLog)
            .filter(AuditLog.user_id == user_id)
            .order_by(AuditLog.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
