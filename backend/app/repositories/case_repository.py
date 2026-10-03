from sqlalchemy.orm import Session

from app.models.case import Case


class CaseRepository:
    def __init__(self, session: Session):
        self.session = session

    def create_case(self, *, case_number: str, title: str, description: str | None, status: str, priority: str, created_by: int) -> Case:
        case = Case(
            case_number=case_number,
            title=title,
            description=description,
            status=status,
            priority=priority,
            created_by=created_by,
        )
        self.session.add(case)
        self.session.commit()
        self.session.refresh(case)
        return case

    def get_case_by_id(self, case_id: int) -> Case | None:
        return self.session.query(Case).filter(Case.id == case_id).first()

    def get_case_by_number(self, case_number: str) -> Case | None:
        return self.session.query(Case).filter(Case.case_number == case_number).first()

    def list_cases(self, *, owner_id: int | None = None) -> list[Case]:
        query = self.session.query(Case)
        if owner_id is not None:
            query = query.filter(Case.created_by == owner_id)
        return query.order_by(Case.created_at.desc()).all()

    def update_case(self, case: Case, *, title: str | None = None, description: str | None = None, status: str | None = None, priority: str | None = None) -> Case:
        if title is not None:
            case.title = title
        if description is not None:
            case.description = description
        if status is not None:
            case.status = status
        if priority is not None:
            case.priority = priority
        case.updated_at = case.updated_at
        self.session.commit()
        self.session.refresh(case)
        return case
