from __future__ import annotations

from typing import Any

from fastapi import Request
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.models.user import User
from app.repositories.audit_repository import AuditRepository

VALID_AUDIT_ACTIONS = {
    "AUTH_LOGIN",
    "AUTH_LOGOUT",
    "AUTH_LOGIN_FAILED",
    "CASE_CREATED",
    "CASE_UPDATED",
    "CASE_ARCHIVED",
    "EVIDENCE_UPLOADED",
    "EVIDENCE_VERIFIED",
    "EVIDENCE_VERIFICATION_FAILED",
    "METADATA_EXTRACTED",
    "REPORT_GENERATED",
}


class AuditService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = AuditRepository(db)

    @staticmethod
    def _get_client_ip(request: Request | None) -> str | None:
        if request is None:
            return None
        if request.client and request.client.host:
            return request.client.host
        return None

    @staticmethod
    def _get_user_agent(request: Request | None) -> str | None:
        if request is None:
            return None
        return request.headers.get("user-agent")

    def log_event(
        self,
        *,
        action: str,
        user: User | None = None,
        case_id: int | None = None,
        evidence_id: int | None = None,
        entity_type: str | None = None,
        entity_id: int | None = None,
        description: str | None = None,
        request: Request | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> AuditLog | None:
        if action not in VALID_AUDIT_ACTIONS:
            return None

        if user is not None:
            user_id = user.id
        else:
            user_id = None

        if ip_address is None:
            ip_address = self._get_client_ip(request)
        if user_agent is None:
            user_agent = self._get_user_agent(request)

        try:
            return self.repository.create_log(
                action=action,
                user_id=user_id,
                case_id=case_id,
                evidence_id=evidence_id,
                entity_type=entity_type,
                entity_id=entity_id,
                description=description,
                ip_address=ip_address,
                user_agent=user_agent,
            )
        except Exception:
            return None

    def log_login_success(self, user: User, request: Request | None = None) -> AuditLog | None:
        return self.log_event(
            action="AUTH_LOGIN",
            user=user,
            description=f"Successful login for user {user.username}",
            request=request,
        )

    def log_login_failed(self, *, user: User | None = None, description: str | None = None, request: Request | None = None) -> AuditLog | None:
        return self.log_event(
            action="AUTH_LOGIN_FAILED",
            user=user,
            description=description or "Failed login attempt",
            request=request,
        )

    def log_case_created(self, user: User, case_id: int, request: Request | None = None, description: str | None = None) -> AuditLog | None:
        return self.log_event(
            action="CASE_CREATED",
            user=user,
            case_id=case_id,
            entity_type="case",
            entity_id=case_id,
            description=description or "Case created",
            request=request,
        )

    def log_case_updated(self, user: User, case_id: int, request: Request | None = None, description: str | None = None) -> AuditLog | None:
        return self.log_event(
            action="CASE_UPDATED",
            user=user,
            case_id=case_id,
            entity_type="case",
            entity_id=case_id,
            description=description or "Case updated",
            request=request,
        )

    def log_case_archived(self, user: User, case_id: int, request: Request | None = None, description: str | None = None) -> AuditLog | None:
        return self.log_event(
            action="CASE_ARCHIVED",
            user=user,
            case_id=case_id,
            entity_type="case",
            entity_id=case_id,
            description=description or "Case archived",
            request=request,
        )

    def log_evidence_uploaded(self, user: User, case_id: int, evidence_id: int, request: Request | None = None, description: str | None = None) -> AuditLog | None:
        return self.log_event(
            action="EVIDENCE_UPLOADED",
            user=user,
            case_id=case_id,
            evidence_id=evidence_id,
            entity_type="evidence",
            entity_id=evidence_id,
            description=description or "Evidence uploaded",
            request=request,
        )

    def log_metadata_extracted(self, user: User, case_id: int | None, evidence_id: int | None, request: Request | None = None, description: str | None = None) -> AuditLog | None:
        return self.log_event(
            action="METADATA_EXTRACTED",
            user=user,
            case_id=case_id,
            evidence_id=evidence_id,
            entity_type="metadata",
            entity_id=evidence_id,
            description=description or "Metadata extracted",
            request=request,
        )

    def log_verification_success(self, user: User, case_id: int | None, evidence_id: int | None, request: Request | None = None, description: str | None = None) -> AuditLog | None:
        return self.log_event(
            action="EVIDENCE_VERIFIED",
            user=user,
            case_id=case_id,
            evidence_id=evidence_id,
            entity_type="evidence",
            entity_id=evidence_id,
            description=description or "Evidence verification succeeded",
            request=request,
        )

    def log_verification_failed(self, user: User, case_id: int | None, evidence_id: int | None, request: Request | None = None, description: str | None = None) -> AuditLog | None:
        return self.log_event(
            action="EVIDENCE_VERIFICATION_FAILED",
            user=user,
            case_id=case_id,
            evidence_id=evidence_id,
            entity_type="evidence",
            entity_id=evidence_id,
            description=description or "Evidence verification failed",
            request=request,
        )

    def list_user_logs(self, user_id: int, *, skip: int = 0, limit: int = 50) -> list[AuditLog]:
        return self.repository.list_logs_by_user(user_id, skip=skip, limit=limit)

    def list_case_logs(self, case_id: int, *, skip: int = 0, limit: int = 50) -> list[AuditLog]:
        return self.repository.list_logs_by_case(case_id, skip=skip, limit=limit)

    def list_evidence_logs(self, evidence_id: int, *, skip: int = 0, limit: int = 50) -> list[AuditLog]:
        return self.repository.list_logs_by_evidence(evidence_id, skip=skip, limit=limit)
