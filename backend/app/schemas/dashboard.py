from pydantic import BaseModel


class DashboardSummary(BaseModel):
    active_cases: int
    total_evidence: int
    verified_evidence: int
    integrity_failed_evidence: int
    pending_verification: int
    verification_records: int
    audit_events: int
