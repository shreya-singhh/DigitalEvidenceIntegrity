from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app
from app.models.audit_log import AuditLog
from app.models.case import Case
from app.models.user import User
from app.models.verification_log import VerificationLog
from app.services.verification_service import resolve_evidence_path
from tests.conftest import TestSessionLocal


client = TestClient(app)


def create_user(prefix: str) -> tuple[str, str, dict[str, str]]:
    suffix = uuid4().hex[:10]
    username = f"{prefix}_{suffix}"
    email = f"{username}@example.com"
    password = "StrongPass123!"
    response = client.post(
        "/api/auth/register",
        json={"username": username, "email": email, "password": password},
    )
    assert response.status_code == 201, response.text
    login = client.post("/api/auth/login", json={"username": username, "password": password})
    assert login.status_code == 200, login.text
    return username, email, {"Authorization": f"Bearer {login.json()['access_token']}"}


def create_case(headers: dict[str, str]) -> int:
    response = client.post(
        "/api/cases",
        json={
            "case_number": f"SHARE-{uuid4().hex[:12]}",
            "title": "Shared evidence case",
            "description": "Permission test",
            "status": "OPEN",
            "priority": "MEDIUM",
        },
        headers=headers,
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


def upload_evidence(case_id: int, headers: dict[str, str], content: bytes = b"original evidence") -> dict:
    response = client.post(
        "/api/evidence/upload",
        data={"case_id": case_id, "description": "Access test"},
        files={"file": ("original.txt", content, "text/plain")},
        headers=headers,
    )
    assert response.status_code == 201, response.text
    return response.json()


def grant_access(case_id: int, email: str, owner_headers: dict[str, str]) -> dict:
    response = client.post(
        f"/api/cases/{case_id}/access",
        json={"email": email},
        headers=owner_headers,
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_shared_user_can_access_download_and_audit_until_revoked():
    owner_name, _, owner_headers = create_user("owner")
    investigator_name, investigator_email, investigator_headers = create_user("investigator")
    outsider_name, _, outsider_headers = create_user("outsider")
    case_id = create_case(owner_headers)
    evidence = upload_evidence(case_id, owner_headers)
    evidence_id = evidence["id"]

    assert client.get(f"/api/cases/{case_id}", headers=outsider_headers).status_code == 403
    assert client.get(f"/api/evidence/{evidence_id}", headers=outsider_headers).status_code == 403
    assert client.get(f"/api/evidence/{evidence_id}/integrity", headers=outsider_headers).status_code == 403
    assert client.get(f"/api/evidence/{evidence_id}/download", headers=outsider_headers).status_code == 403
    assert client.get(f"/api/metadata/evidence/{evidence_id}", headers=outsider_headers).status_code == 403
    assert client.get(f"/api/chain-of-custody/evidence/{evidence_id}", headers=outsider_headers).status_code == 403
    assert client.get(f"/api/audit/evidence/{evidence_id}", headers=outsider_headers).status_code == 403
    assert client.get(f"/api/audit/case/{case_id}", headers=outsider_headers).status_code == 403
    assert client.post(
        f"/api/evidence/{evidence_id}/verify",
        files={"file": ("guess.txt", b"guess", "text/plain")},
        headers=outsider_headers,
    ).status_code == 403

    grant = grant_access(case_id, investigator_email, owner_headers)
    assert grant["username"] == investigator_name
    assert client.get(f"/api/cases/{case_id}/access", headers=investigator_headers).status_code == 403
    assert client.patch(
        f"/api/cases/{case_id}",
        json={"title": "Investigator cannot amend"},
        headers=investigator_headers,
    ).status_code == 403
    assert client.post(
        "/api/evidence/upload",
        data={"case_id": case_id},
        files={"file": ("unauthorized.txt", b"payload", "text/plain")},
        headers=investigator_headers,
    ).status_code == 403
    assert client.get(f"/api/cases/{case_id}", headers=investigator_headers).status_code == 200
    assert client.get("/api/cases", headers=investigator_headers).json()[0]["id"] == case_id
    assert client.get("/api/evidence", headers=investigator_headers).json()[0]["id"] == evidence_id
    assert client.get(f"/api/evidence/cases/{case_id}", headers=investigator_headers).status_code == 200
    assert client.get(f"/api/evidence/{evidence_id}", headers=investigator_headers).status_code == 200
    assert client.get(f"/api/metadata/evidence/{evidence_id}", headers=investigator_headers).status_code == 200
    assert client.get(f"/api/chain-of-custody/evidence/{evidence_id}", headers=investigator_headers).status_code == 200
    assert client.get(f"/api/audit/evidence/{evidence_id}", headers=investigator_headers).status_code == 200

    with TestSessionLocal() as db:
        investigator_user_id = db.query(User.id).filter(User.username == investigator_name).scalar()
        owner_user_id = db.query(User.id).filter(User.username == owner_name).scalar()
    path = resolve_evidence_path(evidence["storage_path"])
    original_bytes = path.read_bytes()
    integrity = client.get(f"/api/evidence/{evidence_id}/integrity", headers=investigator_headers)
    assert integrity.status_code == 200, integrity.text
    assert integrity.json()["verification_status"] == "VERIFIED"
    download = client.get(f"/api/evidence/{evidence_id}/download", headers=investigator_headers)
    assert download.status_code == 200, download.text
    assert download.content == original_bytes
    assert download.headers["x-evidence-integrity"] == "VERIFIED"
    assert path.read_bytes() == original_bytes

    with TestSessionLocal() as db:
        investigator_audit = (
            db.query(AuditLog)
            .filter(AuditLog.case_id == case_id, AuditLog.user_id == investigator_user_id)
            .all()
        )
        assert any(row.action == "EVIDENCE_ACCESSED" for row in investigator_audit)
        assert any(row.action == "EVIDENCE_DOWNLOADED" for row in investigator_audit)
        assert any(row.action == "EVIDENCE_VERIFIED" for row in investigator_audit)

    owner_audit = client.get(f"/api/audit/case/{case_id}", headers=owner_headers).json()
    assert any(
        row["action"] == "CASE_ACCESS_GRANTED" and row["user_id"] == owner_user_id
        for row in owner_audit
    )

    revoked = client.delete(f"/api/cases/{case_id}/access/{grant['user_id']}", headers=owner_headers)
    assert revoked.status_code == 204, revoked.text
    assert client.get(f"/api/evidence/{evidence_id}", headers=investigator_headers).status_code == 403
    assert client.get(f"/api/evidence/{evidence_id}/download", headers=investigator_headers).status_code == 403
    assert client.get(f"/api/audit/case/{case_id}", headers=investigator_headers).status_code == 403
    assert client.get(f"/api/cases/{case_id}/access", headers=outsider_headers).status_code == 403
    assert client.patch(
        f"/api/evidence/{evidence_id}",
        json={"description": "overwrite"},
        headers=owner_headers,
    ).status_code == 405
    assert client.delete(f"/api/evidence/{evidence_id}", headers=owner_headers).status_code == 405
    assert outsider_name


def test_stored_integrity_detects_tampering_without_blaming_separate_copy():
    _, _, owner_headers = create_user("integrity_owner")
    investigator_name, investigator_email, investigator_headers = create_user("integrity_investigator")
    case_id = create_case(owner_headers)
    evidence = upload_evidence(case_id, owner_headers, b"trusted original")
    evidence_id = evidence["id"]
    grant_access(case_id, investigator_email, owner_headers)
    path = resolve_evidence_path(evidence["storage_path"])
    original_bytes = path.read_bytes()

    changed_copy = client.post(
        f"/api/evidence/{evidence_id}/verify",
        files={"file": ("changed-copy.txt", b"separately modified copy", "text/plain")},
        headers=investigator_headers,
    )
    assert changed_copy.status_code == 200, changed_copy.text
    assert changed_copy.json()["verification_status"] == "FAILED"
    assert "does not establish that the stored original was modified" in changed_copy.json()["message"]
    assert path.read_bytes() == original_bytes
    assert client.get(f"/api/evidence/{evidence_id}/integrity", headers=investigator_headers).json()[
        "verification_status"
    ] == "VERIFIED"

    separate = upload_evidence(case_id, owner_headers, b"separately modified copy")
    assert separate["id"] != evidence_id
    path.write_bytes(b"tampered stored original")
    integrity = client.get(f"/api/evidence/{evidence_id}/integrity", headers=investigator_headers)
    assert integrity.status_code == 200, integrity.text
    assert integrity.json()["verification_status"] == "FAILED"
    assert integrity.json()["current_hash"] != integrity.json()["stored_hash"]

    download = client.get(f"/api/evidence/{evidence_id}/download", headers=investigator_headers)
    assert download.status_code == 200
    assert download.headers["x-evidence-integrity"] == "FAILED"
    assert download.content == b"tampered stored original"

    with TestSessionLocal() as db:
        investigator_user_id = db.query(User.id).filter(User.username == investigator_name).scalar()
        stored_checks = (
            db.query(VerificationLog)
            .filter(
                VerificationLog.evidence_id == evidence_id,
                VerificationLog.verified_by == investigator_user_id,
            )
            .all()
        )
        assert any(row.status == "FAILED" for row in stored_checks)
        failed_logs = (
            db.query(AuditLog)
            .filter(
                AuditLog.evidence_id == evidence_id,
                AuditLog.action == "EVIDENCE_VERIFICATION_FAILED",
                AuditLog.user_id == investigator_user_id,
            )
            .all()
        )
        assert failed_logs
