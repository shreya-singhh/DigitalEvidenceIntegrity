import os
import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.hashing.sha256 import compute_sha256_file
from app.models.case import Case
from app.models.chain_of_custody import ChainOfCustody
from app.models.evidence import Evidence
from app.models.user import User
from app.repositories.audit_repository import AuditRepository
from app.repositories.evidence_repository import EvidenceRepository
from app.utils.validators import is_valid_extension, is_valid_upload_size


def _sanitize_filename(filename: str) -> str:
    if not filename or not filename.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Filename is required")

    sanitized = Path(filename).name.strip()
    if not sanitized or sanitized in {".", ".."}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid filename")

    if sanitized != filename.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsafe filename")

    if not is_valid_extension(sanitized):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported file type")

    return sanitized


def _validate_case_access(db: Session, case_id: int, current_user: User) -> Case:
    case = db.query(Case).filter(Case.id == case_id).first()
    if case is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
    if case.created_by != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized for this case")
    return case


def _build_relative_storage_path(path: Path) -> str:
    try:
        relative = path.relative_to(Path.cwd())
    except ValueError:
        relative = path
    return relative.as_posix()


def upload_evidence(
    db: Session,
    file: UploadFile,
    case_id: int,
    current_user: User,
    description: str | None = None,
) -> Evidence:
    if file is None or file.filename is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No file uploaded")

    safe_filename = _sanitize_filename(file.filename)
    _validate_case_access(db, case_id, current_user)

    file.file.seek(0, os.SEEK_END)
    file_size = file.file.tell()
    file.file.seek(0)

    if not is_valid_upload_size(file_size):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid file size")

    if file_size == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty file is not allowed")

    upload_dir = Path(settings.upload_directory)
    upload_dir.mkdir(parents=True, exist_ok=True)
    case_dir = upload_dir / f"case_{case_id}"
    case_dir.mkdir(parents=True, exist_ok=True)

    unique_name = f"{uuid.uuid4().hex}_{safe_filename}"
    storage_path = case_dir / unique_name
    if storage_path.exists():
        unique_name = f"{uuid.uuid4().hex}_{safe_filename}"
        storage_path = case_dir / unique_name

    with storage_path.open("wb") as destination:
        while True:
            chunk = file.file.read(1024 * 1024)
            if not chunk:
                break
            destination.write(chunk)

    sha256_hash = compute_sha256_file(storage_path)
    relative_storage_path = _build_relative_storage_path(storage_path)
    repository = EvidenceRepository(db)

    evidence = repository.create(
        case_id=case_id,
        owner_id=current_user.id,
        file_name=safe_filename,
        file_type=file.content_type or Path(safe_filename).suffix.lstrip("."),
        file_size=file_size,
        storage_path=relative_storage_path,
        sha256_hash=sha256_hash,
        description=description.strip() if description else None,
    )
    AuditRepository(db).create_log(
        action="EVIDENCE_UPLOADED",
        user_id=current_user.id,
        case_id=case_id,
        evidence_id=evidence.id,
        entity_type="evidence",
        entity_id=evidence.id,
        description=f"Evidence {safe_filename} uploaded to case {case_id}",
    )
    db.add(
        ChainOfCustody(
            evidence_id=evidence.id,
            user_id=current_user.id,
            action="EVIDENCE_REGISTERED",
            description=f"Evidence registered; reference_sha256={sha256_hash}",
        )
    )
    db.commit()
    return evidence


def get_evidence_record(db: Session, evidence_id: int, current_user: User) -> Evidence:
    evidence = db.query(Evidence).filter(Evidence.id == evidence_id).first()
    if evidence is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence not found")
    if evidence.case is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
    if evidence.case.created_by != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this evidence")
    return evidence


def list_case_evidence(db: Session, case_id: int, current_user: User) -> list[Evidence]:
    case = _validate_case_access(db, case_id, current_user)
    repository = EvidenceRepository(db)
    return repository.get_by_case_id(case.id)


def list_user_evidence(db: Session, current_user: User) -> list[Evidence]:
    return EvidenceRepository(db).get_by_user_id(current_user.id)
