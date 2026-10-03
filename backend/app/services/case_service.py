from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.case import Case
from app.repositories.audit_repository import AuditRepository
from app.repositories.case_repository import CaseRepository
from app.schemas.case import CaseCreate, CaseUpdate

VALID_CASE_STATUSES = {"OPEN", "UNDER_REVIEW", "CLOSED", "ARCHIVED"}
VALID_PRIORITIES = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}


class CaseService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = CaseRepository(db)

    def _ensure_valid_status(self, status_value: str | None) -> None:
        if status_value is None:
            return
        if status_value.upper() not in VALID_CASE_STATUSES:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid case status")

    def _ensure_valid_priority(self, priority_value: str | None) -> None:
        if priority_value is None:
            return
        if priority_value.upper() not in VALID_PRIORITIES:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid case priority")

    def create_case(self, user_id: int, case_in: CaseCreate) -> Case:
        normalized_case_number = case_in.case_number.strip()
        if not normalized_case_number:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Case number is required")

        existing = self.repository.get_case_by_number(normalized_case_number)
        if existing is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Case number already exists")

        self._ensure_valid_status(case_in.status)
        self._ensure_valid_priority(case_in.priority)

        case = self.repository.create_case(
            case_number=normalized_case_number,
            title=case_in.title.strip(),
            description=case_in.description.strip() if case_in.description else None,
            status=case_in.status.upper(),
            priority=case_in.priority.upper(),
            created_by=user_id,
        )
        AuditRepository(self.db).create_log(
            action="CASE_CREATED",
            user_id=user_id,
            case_id=case.id,
            entity_type="case",
            entity_id=case.id,
            description=f"Case {case.case_number} created",
        )
        return case

    def get_case(self, case_id: int, user_id: int) -> Case:
        case = self.repository.get_case_by_id(case_id)
        if case is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
        if case.created_by != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this case")
        return case

    def list_cases(self, user_id: int) -> list[Case]:
        return self.repository.list_cases(owner_id=user_id)

    def update_case(self, case_id: int, user_id: int, case_update: CaseUpdate) -> Case:
        case = self.get_case(case_id, user_id)

        if case_update.title is not None:
            case_update.title = case_update.title.strip()
            if not case_update.title:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Title cannot be empty")

        if case_update.status is not None:
            self._ensure_valid_status(case_update.status)
            case_update.status = case_update.status.upper()

        if case_update.priority is not None:
            self._ensure_valid_priority(case_update.priority)
            case_update.priority = case_update.priority.upper()

        if case_update.description is not None:
            case_update.description = case_update.description.strip() if case_update.description else None

        case = self.repository.update_case(
            case,
            title=case_update.title,
            description=case_update.description,
            status=case_update.status,
            priority=case_update.priority,
        )
        AuditRepository(self.db).create_log(
            action="CASE_UPDATED",
            user_id=user_id,
            case_id=case.id,
            entity_type="case",
            entity_id=case.id,
            description=f"Case {case.case_number} updated",
        )
        return case
