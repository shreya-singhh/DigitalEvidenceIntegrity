from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.auth.security import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.services.case_service import CaseService
from app.services.report_service import generate_case_report

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("/case/{case_id}")
def download_case_report(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FileResponse:
    case = CaseService(db).get_case(case_id, current_user.id)
    report_path = generate_case_report(db, case, current_user)
    return FileResponse(
        path=report_path,
        media_type="application/json",
        filename=report_path.name,
    )
