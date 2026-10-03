from fastapi.testclient import TestClient

from app.main import app

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
    return response


def test_authenticated_audit_access():
    register_user("audituser1", "audituser1@example.com")
    login_response = login_user("audituser1")
    token = login_response.json()["access_token"]

    response = client.get("/api/audit", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_unauthenticated_audit_access_rejected():
    response = client.get("/api/audit")
    assert response.status_code == 401


def test_audit_record_creation():
    register_user("audituser2", "audituser2@example.com")
    login_response = login_user("audituser2")
    token = login_response.json()["access_token"]

    response = client.get("/api/audit", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert any(item["action"] == "AUTH_LOGIN" for item in data)


def test_audit_retrieval():
    register_user("audituser3", "audituser3@example.com")
    login_response = login_user("audituser3")
    token = login_response.json()["access_token"]

    logs = client.get("/api/audit", headers={"Authorization": f"Bearer {token}"})
    audit_id = logs.json()[0]["id"]
    detail = client.get(f"/api/audit/{audit_id}", headers={"Authorization": f"Bearer {token}"})
    assert detail.status_code == 200
    assert detail.json()["id"] == audit_id


def test_case_audit_filtering():
    register_user("audituser4", "audituser4@example.com")
    token = login_user("audituser4").json()["access_token"]

    created = client.post(
        "/api/cases",
        json={
            "case_number": "AUDIT-CASE-001",
            "title": "Audit Case",
            "description": "Case audit test",
            "status": "OPEN",
            "priority": "HIGH",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    case_id = created.json()["id"]

    response = client.get(f"/api/audit/case/{case_id}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert any(item["action"] == "CASE_CREATED" for item in response.json())


def test_evidence_audit_filtering():
    register_user("audituser5", "audituser5@example.com")
    token = login_user("audituser5").json()["access_token"]

    case_response = client.post(
        "/api/cases",
        json={
            "case_number": "AUDIT-CASE-002",
            "title": "Evidence Audit Case",
            "description": "Audit evidence test",
            "status": "OPEN",
            "priority": "MEDIUM",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    case_id = case_response.json()["id"]

    evidence_response = client.post(
        "/api/evidence/upload",
        data={"case_id": case_id, "description": "audit evidence"},
        files={"file": ("audit.txt", b"audit", "text/plain")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert evidence_response.status_code == 201
    evidence_id = evidence_response.json()["id"]

    response = client.get(f"/api/audit/evidence/{evidence_id}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert any(item["action"] == "EVIDENCE_UPLOADED" for item in response.json())


def test_user_audit_filtering():
    register_user("audituser6", "audituser6@example.com")
    token = login_user("audituser6").json()["access_token"]

    response = client.get("/api/audit", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert any(item["action"] == "AUTH_LOGIN" for item in response.json())


def test_missing_audit_record_returns_404():
    register_user("audituser7", "audituser7@example.com")
    token = login_user("audituser7").json()["access_token"]

    response = client.get("/api/audit/999999", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 404


def test_audit_records_cannot_be_updated():
    register_user("audituser8", "audituser8@example.com")
    token = login_user("audituser8").json()["access_token"]

    logs = client.get("/api/audit", headers={"Authorization": f"Bearer {token}"})
    audit_id = logs.json()[0]["id"]

    response = client.patch(f"/api/audit/{audit_id}", json={"description": "tampered"}, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 405


def test_audit_records_cannot_be_deleted():
    register_user("audituser9", "audituser9@example.com")
    token = login_user("audituser9").json()["access_token"]

    logs = client.get("/api/audit", headers={"Authorization": f"Bearer {token}"})
    audit_id = logs.json()[0]["id"]

    response = client.delete(f"/api/audit/{audit_id}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code in {405, 404}


def test_unauthorized_audit_access_rejected():
    register_user("auditowner1", "auditowner1@example.com")
    owner_token = login_user("auditowner1").json()["access_token"]
    register_user("auditowner2", "auditowner2@example.com")
    other_token = login_user("auditowner2").json()["access_token"]

    case_response = client.post(
        "/api/cases",
        json={
            "case_number": "AUDIT-CASE-003",
            "title": "Private Case",
            "description": "Private audit",
            "status": "OPEN",
            "priority": "HIGH",
        },
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    case_id = case_response.json()["id"]

    response = client.get(f"/api/audit/case/{case_id}", headers={"Authorization": f"Bearer {other_token}"})
    assert response.status_code == 403


def test_audit_event_created_after_case_creation():
    register_user("audituser10", "audituser10@example.com")
    token = login_user("audituser10").json()["access_token"]

    response = client.post(
        "/api/cases",
        json={
            "case_number": "AUDIT-CASE-004",
            "title": "Case Audit Event",
            "description": "Created event",
            "status": "OPEN",
            "priority": "LOW",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    case_id = response.json()["id"]

    logs = client.get("/api/audit", headers={"Authorization": f"Bearer {token}"})
    assert any(log["case_id"] == case_id and log["action"] == "CASE_CREATED" for log in logs.json())


def test_audit_event_created_after_evidence_upload():
    register_user("audituser11", "audituser11@example.com")
    token = login_user("audituser11").json()["access_token"]

    case_response = client.post(
        "/api/cases",
        json={
            "case_number": "AUDIT-CASE-005",
            "title": "Evidence Audit Event",
            "description": "Upload event",
            "status": "OPEN",
            "priority": "MEDIUM",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    case_id = case_response.json()["id"]

    upload = client.post(
        "/api/evidence/upload",
        data={"case_id": case_id, "description": "audit upload"},
        files={"file": ("audit-upload.txt", b"content", "text/plain")},
        headers={"Authorization": f"Bearer {token}"},
    )
    evidence_id = upload.json()["id"]

    logs = client.get("/api/audit", headers={"Authorization": f"Bearer {token}"})
    assert any(log["evidence_id"] == evidence_id and log["action"] == "EVIDENCE_UPLOADED" for log in logs.json())
