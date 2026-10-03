from pathlib import Path

from fastapi.testclient import TestClient

from app.api.routes.audit import router as audit_router
from app.api.routes.cases import router as cases_router
from app.api.routes.evidence import router as evidence_router
from app.auth.security import get_current_user
from app.main import app
from app.models.audit_log import AuditLog
from app.models.case import Case
from app.models.evidence import Evidence
from app.models.user import User
from app.models.verification_log import VerificationLog
from app.auth.hashing import get_password_hash
from tests.conftest import TestSessionLocal

client = TestClient(app)


def register_user(username: str, email: str, password: str = "StrongPass123!"):
    return client.post(
        "/api/auth/register",
        json={"username": username, "email": email, "password": password},
    )


def login_user(username: str, password: str = "StrongPass123!"):
    response = client.post(
        "/api/auth/login",
        json={"username": username, "password": password},
    )
    return response.json()["access_token"]


def create_case_for_user(username: str, case_number: str = "CASE-VERIFY-01"):
    register_user(username, f"{username}@example.com")
    token = login_user(username)
    response = client.post(
        "/api/cases",
        json={
            "case_number": case_number,
            "title": "Verification Case",
            "description": "Test verification",
            "status": "OPEN",
            "priority": "HIGH",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    return token, response.json()["id"]


def get_evidence_record_by_name(file_name: str):
    db = TestSessionLocal()
    try:
        return db.query(Evidence).filter(Evidence.file_name == file_name).order_by(Evidence.id.desc()).first()
    finally:
        db.close()


def test_authenticated_verification_succeeds_when_hash_matches():
    username = "verifyuser1"
    token, case_id = create_case_for_user(username, "CASE-VERIFY-01")

    upload_response = client.post(
        "/api/evidence/upload",
        data={"case_id": case_id, "description": "hash matches"},
        files={"file": ("match.txt", b"hello integrity", "text/plain")},
        headers={"Authorization": f"Bearer {token}"},
    )
    evidence_id = upload_response.json()["id"]

    response = client.post(
        f"/api/evidence/{evidence_id}/verify",
        files={"file": ("match.txt", b"hello integrity", "text/plain")},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["verification_status"] == "VERIFIED"
    assert data["stored_hash"] == data["current_hash"]
    assert data["message"]


def test_verification_fails_when_file_contents_have_changed():
    username = "verifyuser2"
    token, case_id = create_case_for_user(username, "CASE-VERIFY-02")

    upload_response = client.post(
        "/api/evidence/upload",
        data={"case_id": case_id, "description": "hash mismatch"},
        files={"file": ("mismatch.txt", b"original content", "text/plain")},
        headers={"Authorization": f"Bearer {token}"},
    )
    evidence_id = upload_response.json()["id"]
    response = client.post(
        f"/api/evidence/{evidence_id}/verify",
        files={"file": ("mismatch.txt", b"tampered content", "text/plain")},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["verification_status"] == "FAILED"
    assert data["stored_hash"] == upload_response.json()["sha256_hash"]
    assert data["current_hash"] != data["stored_hash"]
    assert data["message"] == "INTEGRITY FAILED: possible tampering or modification detected."

    db = TestSessionLocal()
    try:
        evidence = db.query(Evidence).filter(Evidence.id == evidence_id).one()
        verification = db.query(VerificationLog).filter(VerificationLog.evidence_id == evidence_id).one()
        assert evidence.sha256_hash == upload_response.json()["sha256_hash"]
        assert db.query(Evidence).filter(Evidence.case_id == evidence.case_id).count() == 1
        assert verification.original_hash == data["stored_hash"]
        assert verification.calculated_hash == data["current_hash"]
        assert verification.status == "FAILED"
    finally:
        db.close()


def test_new_upload_is_a_valid_independent_evidence_record():
    username = "verifyuser-new-record"
    token, case_id = create_case_for_user(username, "CASE-VERIFY-NEW")

    original_upload = client.post(
        "/api/evidence/upload",
        data={"case_id": case_id, "description": "original evidence"},
        files={"file": ("evidence.txt", b"original evidence bytes", "text/plain")},
        headers={"Authorization": f"Bearer {token}"},
    )
    modified_copy_upload = client.post(
        "/api/evidence/upload",
        data={"case_id": case_id, "description": "separately registered copy"},
        files={"file": ("evidence-copy.txt", b"modified copy bytes", "text/plain")},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert original_upload.status_code == 201, original_upload.text
    assert modified_copy_upload.status_code == 201, modified_copy_upload.text
    original = original_upload.json()
    modified_copy = modified_copy_upload.json()
    assert original["id"] != modified_copy["id"]
    assert original["sha256_hash"] != modified_copy["sha256_hash"]

    original_verification = client.post(
        f"/api/evidence/{original['id']}/verify",
        files={"file": ("evidence.txt", b"original evidence bytes", "text/plain")},
        headers={"Authorization": f"Bearer {token}"},
    )
    copy_verification = client.post(
        f"/api/evidence/{modified_copy['id']}/verify",
        files={"file": ("evidence-copy.txt", b"modified copy bytes", "text/plain")},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert original_verification.status_code == 200, original_verification.text
    assert copy_verification.status_code == 200, copy_verification.text
    assert original_verification.json()["verification_status"] == "VERIFIED"
    assert copy_verification.json()["verification_status"] == "VERIFIED"
    assert copy_verification.json()["stored_hash"] == modified_copy["sha256_hash"]
    assert copy_verification.json()["current_hash"] == modified_copy["sha256_hash"]


def test_missing_evidence_returns_404():
    username = "verifyuser3"
    token, _ = create_case_for_user(username, "CASE-VERIFY-03")

    response = client.post(
        "/api/evidence/999999/verify",
        files={"file": ("missing.txt", b"payload", "text/plain")},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404


def test_verification_hashes_the_submitted_file_even_if_server_copy_is_missing():
    username = "verifyuser4"
    token, case_id = create_case_for_user(username, "CASE-VERIFY-04")

    upload_response = client.post(
        "/api/evidence/upload",
        data={"case_id": case_id, "description": "missing file"},
        files={"file": ("missing.txt", b"payload", "text/plain")},
        headers={"Authorization": f"Bearer {token}"},
    )
    evidence_id = upload_response.json()["id"]
    storage_path = Path(upload_response.json()["storage_path"])
    storage_path.unlink(missing_ok=True)

    response = client.post(
        f"/api/evidence/{evidence_id}/verify",
        files={"file": ("missing.txt", b"payload", "text/plain")},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200, response.text
    assert response.json()["verification_status"] == "VERIFIED"
    assert response.json()["current_hash"] == response.json()["stored_hash"]


def test_unauthenticated_verification_is_rejected():
    response = client.post(
        "/api/evidence/1/verify",
        files={"file": ("test.txt", b"body", "text/plain")},
    )
    assert response.status_code == 401


def test_verification_rejects_an_invalid_jwt():
    response = client.post(
        "/api/evidence/1/verify",
        files={"file": ("test.txt", b"body", "text/plain")},
        headers={"Authorization": "Bearer invalid.jwt.token"},
    )

    assert response.status_code == 401


def test_verification_uses_the_same_current_user_dependency_as_working_routes():
    protected_routes = (
        (cases_router, "/cases", "POST"),
        (evidence_router, "/evidence/upload", "POST"),
        (audit_router, "/audit/evidence/{evidence_id}", "GET"),
        (evidence_router, "/evidence/{evidence_id}/verify", "POST"),
    )

    for router, path, method in protected_routes:
        route = next(
            route
            for route in router.routes
            if getattr(route, "path", None) == path and method in (getattr(route, "methods", set()) or set())
        )
        user_dependencies = [
            dependency.call
            for dependency in route.dependant.dependencies
            if dependency.name == "current_user"
        ]
        assert user_dependencies == [get_current_user]


def test_unauthorized_verification_is_rejected():
    register_user("owner1", "owner1@example.com")
    owner_token = login_user("owner1")
    register_user("owner2", "owner2@example.com")
    attacker_token = login_user("owner2")

    case_response = client.post(
        "/api/cases",
        json={
            "case_number": "CASE-VERIFY-UNAUTH",
            "title": "Private evidence",
            "description": "should not verify",
            "status": "OPEN",
            "priority": "HIGH",
        },
        headers={"Authorization": f"Bearer {owner_token}"},
    )

    evidence_response = client.post(
        "/api/evidence/upload",
        data={"case_id": case_response.json()["id"], "description": "private evidence"},
        files={"file": ("private.txt", b"secret", "text/plain")},
        headers={"Authorization": f"Bearer {owner_token}"},
    )

    response = client.post(
        f"/api/evidence/{evidence_response.json()['id']}/verify",
        files={"file": ("private.txt", b"secret", "text/plain")},
        headers={"Authorization": f"Bearer {attacker_token}"},
    )

    assert response.status_code == 403


def test_stored_sha256_hash_is_not_modified_after_verification():
    username = "verifyuser5"
    token, case_id = create_case_for_user(username, "CASE-VERIFY-05")

    upload_response = client.post(
        "/api/evidence/upload",
        data={"case_id": case_id, "description": "stored hash check"},
        files={"file": ("hash-stay.txt", b"preserve", "text/plain")},
        headers={"Authorization": f"Bearer {token}"},
    )
    evidence_id = upload_response.json()["id"]
    initial_hash = upload_response.json()["sha256_hash"]

    response = client.post(
        f"/api/evidence/{evidence_id}/verify",
        files={"file": ("hash-stay.txt", b"preserve", "text/plain")},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    db = TestSessionLocal()
    try:
        evidence = db.query(Evidence).filter(Evidence.id == evidence_id).first()
        assert evidence.sha256_hash == initial_hash
    finally:
        db.close()


def test_current_sha256_is_calculated_from_the_actual_file():
    username = "verifyuser6"
    token, case_id = create_case_for_user(username, "CASE-VERIFY-06")

    upload_response = client.post(
        "/api/evidence/upload",
        data={"case_id": case_id, "description": "calc from file"},
        files={"file": ("actual-file.txt", b"actual file data", "text/plain")},
        headers={"Authorization": f"Bearer {token}"},
    )
    evidence_id = upload_response.json()["id"]

    response = client.post(
        f"/api/evidence/{evidence_id}/verify",
        files={"file": ("actual-file.txt", b"actual file data", "text/plain")},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["current_hash"] == "0b08d45e45ad4bfa6f12efa663385f07bd2ab69375831b50fb435164573e3828"


def test_successful_verification_creates_an_audit_event():
    username = "verifyuser7"
    token, case_id = create_case_for_user(username, "CASE-VERIFY-07")

    upload_response = client.post(
        "/api/evidence/upload",
        data={"case_id": case_id, "description": "audit success"},
        files={"file": ("audit-success.txt", b"success data", "text/plain")},
        headers={"Authorization": f"Bearer {token}"},
    )
    evidence_id = upload_response.json()["id"]

    verify_response = client.post(
        f"/api/evidence/{evidence_id}/verify",
        files={"file": ("audit-success.txt", b"success data", "text/plain")},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert verify_response.status_code == 200
    db = TestSessionLocal()
    try:
        logs = db.query(AuditLog).filter(AuditLog.evidence_id == evidence_id, AuditLog.action == "EVIDENCE_VERIFIED").all()
        user = db.query(User).filter(User.username == username).one()
        assert len(logs) == 1
        assert logs[0].user_id == user.id
        assert logs[0].case_id == case_id
        assert logs[0].entity_type == "evidence"
        assert logs[0].entity_id == evidence_id
        assert "reference_sha256=" in logs[0].description
        assert "live_sha256=" in logs[0].description
    finally:
        db.close()


def test_failed_verification_creates_an_audit_event():
    username = "verifyuser8"
    token, case_id = create_case_for_user(username, "CASE-VERIFY-08")

    upload_response = client.post(
        "/api/evidence/upload",
        data={"case_id": case_id, "description": "audit fail"},
        files={"file": ("audit-fail.txt", b"original bytes", "text/plain")},
        headers={"Authorization": f"Bearer {token}"},
    )
    evidence_id = upload_response.json()["id"]
    response = client.post(
        f"/api/evidence/{evidence_id}/verify",
        files={"file": ("audit-fail.txt", b"modified bytes", "text/plain")},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    db = TestSessionLocal()
    try:
        logs = db.query(AuditLog).filter(AuditLog.evidence_id == evidence_id, AuditLog.action == "EVIDENCE_VERIFICATION_FAILED").all()
        user = db.query(User).filter(User.username == username).one()
        assert len(logs) == 1
        assert logs[0].user_id == user.id
        assert logs[0].case_id == case_id
        assert logs[0].entity_type == "evidence"
        assert logs[0].entity_id == evidence_id
        assert logs[0].created_at is not None
        assert "Result=INTEGRITY FAILED" in logs[0].description
        assert "reference_sha256=" in logs[0].description
        assert "live_sha256=" in logs[0].description
    finally:
        db.close()


def test_repeated_verification_does_not_corrupt_the_evidence_record():
    username = "verifyuser9"
    token, case_id = create_case_for_user(username, "CASE-VERIFY-09")

    upload_response = client.post(
        "/api/evidence/upload",
        data={"case_id": case_id, "description": "repeat verify"},
        files={"file": ("repeat.txt", b"repeat data", "text/plain")},
        headers={"Authorization": f"Bearer {token}"},
    )
    evidence_id = upload_response.json()["id"]
    first_hash = upload_response.json()["sha256_hash"]

    first = client.post(
        f"/api/evidence/{evidence_id}/verify",
        files={"file": ("repeat.txt", b"repeat data", "text/plain")},
        headers={"Authorization": f"Bearer {token}"},
    )
    second = client.post(
        f"/api/evidence/{evidence_id}/verify",
        files={"file": ("repeat.txt", b"repeat data", "text/plain")},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert first.status_code == 200
    assert second.status_code == 200

    db = TestSessionLocal()
    try:
        evidence = db.query(Evidence).filter(Evidence.id == evidence_id).first()
        assert evidence.sha256_hash == first_hash
        assert evidence.status == "uploaded"
    finally:
        db.close()


def test_verification_endpoint_follows_existing_api_routing_conventions():
    username = "verifyuser10"
    token, case_id = create_case_for_user(username, "CASE-VERIFY-10")

    upload_response = client.post(
        "/api/evidence/upload",
        data={"case_id": case_id, "description": "route"},
        files={"file": ("route.txt", b"route data", "text/plain")},
        headers={"Authorization": f"Bearer {token}"},
    )
    evidence_id = upload_response.json()["id"]

    response = client.post(
        f"/api/evidence/{evidence_id}/verify",
        files={"file": ("route.txt", b"route data", "text/plain")},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["evidence_id"] == evidence_id
