from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.models.case import Case
from app.models.evidence import Evidence
from app.models.verification_log import VerificationLog
from app.schemas.dashboard import DashboardSummary


def get_dashboard_data(db: Session, user_id: int) -> DashboardSummary:
    owned_case_ids = select(Case.id).where(Case.created_by == user_id)
    latest_verification_id = (
        select(func.max(VerificationLog.id))
        .where(VerificationLog.evidence_id == Evidence.id)
        .correlate(Evidence)
        .scalar_subquery()
    )
    current_statuses = (
        db.query(VerificationLog.status)
        .select_from(Evidence)
        .outerjoin(VerificationLog, VerificationLog.id == latest_verification_id)
        .filter(Evidence.case_id.in_(owned_case_ids))
        .all()
    )
    statuses = [row.status.upper() if row.status else None for row in current_statuses]
    return DashboardSummary(
        active_cases=db.query(func.count(Case.id))
        .filter(Case.created_by == user_id, func.upper(Case.status).in_(("OPEN", "UNDER_REVIEW")))
        .scalar()
        or 0,
        total_evidence=db.query(func.count(Evidence.id))
        .filter(Evidence.case_id.in_(owned_case_ids))
        .scalar()
        or 0,
        verified_evidence=sum(status == "VERIFIED" for status in statuses),
        integrity_failed_evidence=sum(status in {"FAILED", "MISSING"} for status in statuses),
        pending_verification=sum(status is None for status in statuses),
        verification_records=db.query(func.count(VerificationLog.id))
        .join(Evidence, VerificationLog.evidence_id == Evidence.id)
        .filter(Evidence.case_id.in_(owned_case_ids))
        .scalar()
        or 0,
        audit_events=db.query(func.count(AuditLog.id))
        .filter(AuditLog.user_id == user_id)
        .scalar()
        or 0,
    )
