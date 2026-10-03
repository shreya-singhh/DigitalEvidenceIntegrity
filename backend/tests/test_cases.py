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
    return response.json()["access_token"]


def test_authenticated_case_creation():
    register_user("caseuser1", "caseuser1@example.com")
    token = login_user("caseuser1")

    response = client.post(
        "/api/cases",
        json={
            "case_number": "CASE-1001",
            "title": "Initial Investigation",
            "description": "Evidence review",
            "status": "OPEN",
            "priority": "HIGH",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 201, response.text
    data = response.json()
    assert data["case_number"] == "CASE-1001"
    assert data["title"] == "Initial Investigation"
    assert data["status"] == "OPEN"
    assert data["priority"] == "HIGH"


def test_unauthenticated_case_creation_rejected():
    response = client.post(
        "/api/cases",
        json={
            "case_number": "CASE-1002",
            "title": "Unauthenticated Case",
            "description": "Should fail",
            "status": "OPEN",
            "priority": "MEDIUM",
        },
    )

    assert response.status_code == 401


def test_successful_case_retrieval():
    register_user("caseuser2", "caseuser2@example.com")
    token = login_user("caseuser2")

    create_response = client.post(
        "/api/cases",
        json={
            "case_number": "CASE-2001",
            "title": "Retrieval Test",
            "description": "Retrieve case",
            "status": "UNDER_REVIEW",
            "priority": "MEDIUM",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    case_id = create_response.json()["id"]

    response = client.get(f"/api/cases/{case_id}", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200, response.text
    assert response.json()["id"] == case_id


def test_nonexistent_case_returns_404():
    register_user("caseuser3", "caseuser3@example.com")
    token = login_user("caseuser3")

    response = client.get("/api/cases/99999", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 404


def test_case_listing():
    register_user("caseuser4", "caseuser4@example.com")
    token = login_user("caseuser4")

    client.post(
        "/api/cases",
        json={
            "case_number": "CASE-3001",
            "title": "Listing Test A",
            "description": "Alpha",
            "status": "OPEN",
            "priority": "LOW",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    client.post(
        "/api/cases",
        json={
            "case_number": "CASE-3002",
            "title": "Listing Test B",
            "description": "Beta",
            "status": "CLOSED",
            "priority": "CRITICAL",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    response = client.get("/api/cases", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2


def test_case_update():
    register_user("caseuser5", "caseuser5@example.com")
    token = login_user("caseuser5")

    create_response = client.post(
        "/api/cases",
        json={
            "case_number": "CASE-4001",
            "title": "Update Test",
            "description": "Original",
            "status": "OPEN",
            "priority": "MEDIUM",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    case_id = create_response.json()["id"]

    response = client.patch(
        f"/api/cases/{case_id}",
        json={"title": "Updated Title", "status": "UNDER_REVIEW", "priority": "HIGH"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["title"] == "Updated Title"
    assert data["status"] == "UNDER_REVIEW"
    assert data["priority"] == "HIGH"


def test_duplicate_case_number_rejected():
    register_user("caseuser6", "caseuser6@example.com")
    token = login_user("caseuser6")

    payload = {
        "case_number": "CASE-5001",
        "title": "Duplicate Test",
        "description": "One",
        "status": "OPEN",
        "priority": "MEDIUM",
    }
    first = client.post("/api/cases", json=payload, headers={"Authorization": f"Bearer {token}"})
    assert first.status_code == 201

    second = client.post("/api/cases", json=payload, headers={"Authorization": f"Bearer {token}"})
    assert second.status_code == 409


def test_invalid_case_data_rejected():
    register_user("caseuser7", "caseuser7@example.com")
    token = login_user("caseuser7")

    response = client.post(
        "/api/cases",
        json={
            "case_number": "A",
            "title": "",
            "description": "bad case",
            "status": "INVALID",
            "priority": "INVALID",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code in {400, 422}


def test_user_cannot_access_another_users_case():
    register_user("owner1", "owner1@example.com")
    owner_token = login_user("owner1")
    register_user("owner2", "owner2@example.com")
    attacker_token = login_user("owner2")

    response = client.post(
        "/api/cases",
        json={
            "case_number": "CASE-6001",
            "title": "Private Case",
            "description": "Sensitive",
            "status": "OPEN",
            "priority": "HIGH",
        },
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    case_id = response.json()["id"]

    forbidden = client.get(f"/api/cases/{case_id}", headers={"Authorization": f"Bearer {attacker_token}"})
    assert forbidden.status_code == 403


def test_case_status_update():
    register_user("caseuser8", "caseuser8@example.com")
    token = login_user("caseuser8")

    created = client.post(
        "/api/cases",
        json={
            "case_number": "CASE-7001",
            "title": "Status Update",
            "description": "Status",
            "status": "OPEN",
            "priority": "MEDIUM",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    case_id = created.json()["id"]

    response = client.patch(
        f"/api/cases/{case_id}",
        json={"status": "CLOSED"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "CLOSED"


def test_priority_update():
    register_user("caseuser9", "caseuser9@example.com")
    token = login_user("caseuser9")

    created = client.post(
        "/api/cases",
        json={
            "case_number": "CASE-8001",
            "title": "Priority Update",
            "description": "Priority",
            "status": "OPEN",
            "priority": "LOW",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    case_id = created.json()["id"]

    response = client.patch(
        f"/api/cases/{case_id}",
        json={"priority": "CRITICAL"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["priority"] == "CRITICAL"
