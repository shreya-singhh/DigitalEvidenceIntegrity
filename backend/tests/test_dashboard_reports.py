import json
import uuid
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.core.config import settings
from app.models.report import Report
from app.models.verification_log import VerificationLog
from tests.conftest import TestSessionLocal

client = TestClient(app)


def create_authenticated_user():
    suffix = uuid.uuid4().hex[:10]
    username = f"workflow-{suffix}"
    password = "StrongPass123!"
    registered = client.post(
        "/api/auth/register",
        json={"username": username, "email": f"{username}@example.com", "password": password},
    )
    assert registered.status_code == 201, registered.text
    logged_in = client.post("/api/auth/login", json={"username": username, "password": password})
    assert logged_in.status_code == 200, logged_in.text
    return {"Authorization": f"Bearer {logged_in.json()['access_token']}"}


def test_dashboard_evidence_verification_metadata_and_report_workflow(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "upload_directory", tmp_path / "uploads")
    monkeypatch.setattr(settings, "report_directory", tmp_path / "reports")
    headers = create_authenticated_user()
    case_response = client.post(
        "/api/cases",
        json={
            "case_number": f"WORKFLOW-{uuid.uuid4().hex[:10]}",
            "title": "Workflow integration case",
            "status": "OPEN",
            "priority": "HIGH",
        },
        headers=headers,
    )
    assert case_response.status_code == 201, case_response.text
    case = case_response.json()
    assert case["creator_username"].startswith("workflow-")

    initial_dashboard = client.get("/api/dashboard", headers=headers)
    assert initial_dashboard.status_code == 200, initial_dashboard.text
    assert initial_dashboard.json()["active_cases"] == 1
    assert initial_dashboard.json()["total_evidence"] == 0

    uploaded = client.post(
        "/api/evidence/upload",
        data={"case_id": case["id"], "description": "Integration evidence"},
        files={"file": ("workflow.txt", b"forensic evidence", "text/plain")},
        headers=headers,
    )
    assert uploaded.status_code == 201, uploaded.text
    evidence = uploaded.json()
    assert len(evidence["sha256_hash"]) == 64

    evidence_list = client.get("/api/evidence", headers=headers)
    assert evidence_list.status_code == 200, evidence_list.text
    assert any(item["id"] == evidence["id"] for item in evidence_list.json())

    metadata = client.get(f"/api/metadata/evidence/{evidence['id']}", headers=headers)
    assert metadata.status_code == 200, metadata.text
    assert metadata.json()["metadata"]["filename"] == "workflow.txt"

    verification = client.post(
        f"/api/evidence/{evidence['id']}/verify",
        files={"file": ("workflow.txt", b"forensic evidence", "text/plain")},
        headers=headers,
    )
    assert verification.status_code == 200, verification.text
    assert verification.json()["verification_status"] == "VERIFIED"

    mismatch = client.post(
        f"/api/evidence/{evidence['id']}/verify",
        files={"file": ("workflow-tampered.txt", b"modified evidence", "text/plain")},
        headers=headers,
    )
    assert mismatch.status_code == 200, mismatch.text
    assert mismatch.json()["verification_status"] == "FAILED"

    dashboard = client.get("/api/dashboard", headers=headers)
    assert dashboard.status_code == 200, dashboard.text
    assert dashboard.json()["total_evidence"] == 1
    assert dashboard.json()["verified_evidence"] == 0
    assert dashboard.json()["integrity_failed_evidence"] == 1
    assert dashboard.json()["pending_verification"] == 0
    assert dashboard.json()["verification_records"] == 2

    report = client.get(f"/api/reports/case/{case['id']}", headers=headers)
    assert report.status_code == 200, report.text
    data = json.loads(report.content)
    assert data["case"]["id"] == case["id"]
    report_evidence = next(item for item in data["evidence"] if item["evidence_id"] == evidence["id"])
    assert report_evidence["integrity_status"] == "MATCH"
    assert report_evidence["verification_status"] == "FAILED"
    assert report_evidence["reference_sha256"] == evidence["sha256_hash"]
    assert report_evidence["integrity_failures"][0]["live_sha256"] == mismatch.json()["current_hash"]
    assert data["audit_events"]
    assert data["chain_of_custody"]

    events = client.get("/api/audit", headers=headers)
    actions = {entry["action"] for entry in events.json()}
    assert {
        "AUTH_LOGIN",
        "CASE_CREATED",
        "EVIDENCE_UPLOADED",
        "METADATA_EXTRACTED",
        "EVIDENCE_VERIFIED",
        "EVIDENCE_VERIFICATION_FAILED",
        "REPORT_GENERATED",
    } <= actions

    custody = client.get(f"/api/chain-of-custody/evidence/{evidence['id']}", headers=headers)
    assert custody.status_code == 200, custody.text
    custody_data = custody.json()
    assert custody_data["evidence_id"] == evidence["id"]
    assert custody_data["file_name"] == evidence["file_name"]
    assert custody_data["case_number"] == case["case_number"]
    assert custody_data["reference_hash"] == evidence["sha256_hash"]
    assert [event["action"] for event in custody_data["events"]] == [
        "EVIDENCE_REGISTERED",
        "EVIDENCE_METADATA_VIEWED",
        "EVIDENCE_VERIFIED",
        "EVIDENCE_VERIFICATION_FAILED",
        "EVIDENCE_REPORT_GENERATED",
    ]
    assert all(event["username"] for event in custody_data["events"])

    db = TestSessionLocal()
    try:
        verification_logs = db.query(VerificationLog).filter_by(evidence_id=evidence["id"]).all()
        assert len(verification_logs) == 2
        assert {entry.status for entry in verification_logs} == {"VERIFIED", "FAILED"}
        assert db.query(Report).filter_by(evidence_id=evidence["id"]).count() == 1
    finally:
        db.close()


def test_dashboard_counts_latest_verified_failed_and_pending_evidence(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "upload_directory", tmp_path / "uploads")
    headers = create_authenticated_user()
    case_response = client.post(
        "/api/cases",
        json={
            "case_number": f"DASHBOARD-{uuid.uuid4().hex[:10]}",
            "title": "Dashboard integrity counts",
            "status": "OPEN",
            "priority": "MEDIUM",
        },
        headers=headers,
    )
    assert case_response.status_code == 201, case_response.text
    case_id = case_response.json()["id"]

    evidence_payloads = [
        ("verified.txt", b"verified payload"),
        ("failed.txt", b"failed payload"),
        ("pending.txt", b"pending payload"),
    ]
    uploaded = []
    for filename, content in evidence_payloads:
        response = client.post(
            "/api/evidence/upload",
            data={"case_id": case_id},
            files={"file": (filename, content, "text/plain")},
            headers=headers,
        )
        assert response.status_code == 201, response.text
        uploaded.append(response.json())

    for index, file_content in ((0, evidence_payloads[0][1]), (1, b"changed payload")):
        response = client.post(
            f"/api/evidence/{uploaded[index]['id']}/verify",
            files={"file": (evidence_payloads[index][0], file_content, "text/plain")},
            headers=headers,
        )
        assert response.status_code == 200, response.text

    dashboard = client.get("/api/dashboard", headers=headers)
    assert dashboard.status_code == 200, dashboard.text
    assert dashboard.json()["total_evidence"] == 3
    assert dashboard.json()["verified_evidence"] == 1
    assert dashboard.json()["integrity_failed_evidence"] == 1
    assert dashboard.json()["pending_verification"] == 1

    recent_audit = client.get("/api/audit", headers=headers)
    assert any(event["action"] == "EVIDENCE_VERIFICATION_FAILED" for event in recent_audit.json())


def test_dashboard_evidence_and_reports_require_authentication():
    assert client.get("/api/dashboard").status_code == 401
    assert client.get("/api/evidence").status_code == 401
    assert client.get("/api/reports/case/1").status_code == 401
