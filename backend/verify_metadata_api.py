import hashlib
import json
import os
import threading
import time
import urllib.request
from pathlib import Path

os.environ["DATABASE_URL"] = "sqlite:///metadata_api_verify.db"
os.environ["SECRET_KEY"] = "verify-secret-key"
os.environ["JWT_ALGORITHM"] = "HS256"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "30"
os.environ["UPLOAD_DIRECTORY"] = r"c:\Users\shrey\OneDrive\Desktop\DigitalEvidenceIntegrity\backend\uploads"
os.environ["REPORT_DIRECTORY"] = r"c:\Users\shrey\OneDrive\Desktop\DigitalEvidenceIntegrity\backend\reports"
os.chdir(r"c:\Users\shrey\OneDrive\Desktop\DigitalEvidenceIntegrity\backend")

from app.auth.hashing import get_password_hash
from app.database.base import Base
from app.database.session import engine
from app.models.case import Case
from app.models.evidence import Evidence
from app.models.user import User
from sqlalchemy.orm import Session

Base.metadata.create_all(bind=engine)

with Session(engine) as session:
    user = session.query(User).filter_by(email="apiuser@example.com").first()
    if user is None:
        user = User(
            username="apiuser",
            email="apiuser@example.com",
            hashed_password=get_password_hash("StrongPass123!"),
            is_active=True,
        )
        session.add(user)
        session.commit()
        session.refresh(user)

    case = session.query(Case).filter_by(case_number="CASE-API-2").first()
    if case is None:
        case = Case(
            case_number="CASE-API-2",
            title="API Metadata Case",
            description="Live verification case",
            created_by=user.id,
            status="open",
        )
        session.add(case)
        session.commit()
        session.refresh(case)

    evidence = session.query(Evidence).filter_by(file_name="report.txt").first()
    if evidence is None:
        seed = Evidence(
            case_id=case.id,
            owner_id=user.id,
            file_name="seed.txt",
            file_type="text/plain",
            file_size=0,
            storage_path="",
            sha256_hash="0" * 64,
            description="seed record",
        )
        session.add(seed)
        session.commit()
        session.refresh(seed)
        evidence = seed

    if evidence.id != 2:
        # Explicitly create a second record to satisfy the requested evidence ID 2 flow.
        evidence_two = session.query(Evidence).filter_by(file_name="report.txt").first()
        if evidence_two is None:
            evidence_two = Evidence(
                case_id=case.id,
                owner_id=user.id,
                file_name="report.txt",
                file_type="text/plain",
                file_size=0,
                storage_path="",
                sha256_hash="0" * 64,
                description="text evidence",
            )
            session.add(evidence_two)
            session.commit()
            session.refresh(evidence_two)
            evidence = evidence_two
        else:
            evidence = evidence_two

    upload_dir = Path(r"c:\Users\shrey\OneDrive\Desktop\DigitalEvidenceIntegrity\backend\uploads")
    upload_dir.mkdir(exist_ok=True)
    file_path = upload_dir / "report.txt"
    file_path.write_text("alpha beta gamma\nline two\n", encoding="utf-8")
    sha = hashlib.sha256(file_path.read_bytes()).hexdigest()
    evidence.file_name = "report.txt"
    evidence.file_type = "text/plain"
    evidence.file_size = file_path.stat().st_size
    evidence.storage_path = str(file_path)
    evidence.sha256_hash = sha
    evidence.description = "text evidence"
    session.commit()
    session.refresh(evidence)
    print(f"EVIDENCE_ID={evidence.id}")

import uvicorn

config = uvicorn.Config("app.main:app", host="127.0.0.1", port=8000, log_level="warning")
server = uvicorn.Server(config)
thread = threading.Thread(target=server.run, daemon=True)
thread.start()

for _ in range(40):
    time.sleep(0.25)
    try:
        with urllib.request.urlopen("http://127.0.0.1:8000/health", timeout=1) as resp:
            if resp.status == 200:
                break
    except Exception:
        pass

login_payload = json.dumps({"username": "apiuser", "password": "StrongPass123!"}).encode()
login_req = urllib.request.Request(
    "http://127.0.0.1:8000/api/auth/login",
    data=login_payload,
    headers={"Content-Type": "application/json"},
    method="POST",
)
with urllib.request.urlopen(login_req, timeout=10) as login_resp:
    token = json.loads(login_resp.read().decode())["access_token"]

metadata_req = urllib.request.Request(
    f"http://127.0.0.1:8000/api/metadata/evidence/{evidence.id}",
    headers={"Authorization": f"Bearer {token}"},
    method="GET",
)
with urllib.request.urlopen(metadata_req, timeout=10) as metadata_resp:
    payload = metadata_resp.read().decode()
    print(payload)

server.should_exit = True
thread.join(timeout=10)
