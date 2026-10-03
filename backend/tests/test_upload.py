from pathlib import Path

from fastapi.testclient import TestClient

from app.auth.hashing import get_password_hash
from app.main import app
from app.models.case import Case
from app.models.user import User
from tests.conftest import TestSessionLocal

client = TestClient(app)


def create_user_and_case(username: str = "alice", email: str = "alice@example.com"):
    db = TestSessionLocal()
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        user = User(
            username=username,
            email=email,
            hashed_password=get_password_hash("StrongPass123!"),
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    case = db.query(Case).filter(Case.case_number == "CASE-001").first()
    if case is None:
        case = Case(
            case_number="CASE-001",
            title="Evidence Case",
            description="Test case",
            created_by=user.id,
            status="open",
        )
        db.add(case)
        db.commit()
        db.refresh(case)

    db.close()
    return user, case


def get_auth_headers(username: str = "alice", password: str = "StrongPass123!"):
    response = client.post(
        "/api/auth/login",
        json={"username": username, "password": password},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_successful_authenticated_upload():
    _, case = create_user_and_case()
    headers = get_auth_headers()
    file_content = b"test evidence payload"
    response = client.post(
        "/api/evidence/upload",
        data={"case_id": case.id, "description": "Uploaded file"},
        files={"file": ("sample.txt", file_content, "text/plain")},
        headers=headers,
    )

    assert response.status_code == 201, response.text
    data = response.json()
    assert data["file_name"] == "sample.txt"
    assert data["case_id"] == case.id
    assert data["status"] == "uploaded"


def test_unauthenticated_upload_rejected():
    response = client.post(
        "/api/evidence/upload",
        data={"case_id": 1, "description": "Uploaded file"},
        files={"file": ("sample.txt", b"body", "text/plain")},
    )

    assert response.status_code == 401


def test_empty_file_rejected():
    _, case = create_user_and_case()
    headers = get_auth_headers()
    response = client.post(
        "/api/evidence/upload",
        data={"case_id": case.id, "description": "empty file"},
        files={"file": ("empty.txt", b"", "text/plain")},
        headers=headers,
    )

    assert response.status_code == 400


def test_invalid_nonexistent_case_rejected():
    create_user_and_case()
    headers = get_auth_headers()
    response = client.post(
        "/api/evidence/upload",
        data={"case_id": 999, "description": "invalid case"},
        files={"file": ("sample.txt", b"body", "text/plain")},
        headers=headers,
    )

    assert response.status_code == 404


def test_sha256_stored_correctly():
    _, case = create_user_and_case()
    headers = get_auth_headers()
    payload = b"abc123"
    response = client.post(
        "/api/evidence/upload",
        data={"case_id": case.id, "description": "hash test"},
        files={"file": ("hash.txt", payload, "text/plain")},
        headers=headers,
    )

    assert response.status_code == 201, response.text
    data = response.json()
    assert data["case_id"] == case.id
    assert data["sha256_hash"] == "6ca13d52ca70c883e0f0bb101e425a89e8624de51db2d2392593af6a84118090"


def test_uploaded_file_exists():
    _, case = create_user_and_case()
    headers = get_auth_headers()
    response = client.post(
        "/api/evidence/upload",
        data={"case_id": case.id, "description": "file existence"},
        files={"file": ("physical.txt", b"hello world", "text/plain")},
        headers=headers,
    )

    assert response.status_code == 201, response.text
    storage_path = response.json()["storage_path"]
    assert Path(storage_path).exists(), storage_path


def test_evidence_database_record_created():
    _, case = create_user_and_case()
    headers = get_auth_headers()
    response = client.post(
        "/api/evidence/upload",
        data={"case_id": case.id, "description": "db record"},
        files={"file": ("db-record.txt", b"record", "text/plain")},
        headers=headers,
    )

    assert response.status_code == 201, response.text
    evidence_id = response.json()["id"]
    retrieval = client.get(f"/api/evidence/{evidence_id}", headers=headers)
    assert retrieval.status_code == 200, retrieval.text
    assert retrieval.json()["id"] == evidence_id


def test_evidence_retrieval():
    _, case = create_user_and_case()
    headers = get_auth_headers()
    response = client.post(
        "/api/evidence/upload",
        data={"case_id": case.id, "description": "retrieval"},
        files={"file": ("retrieval.txt", b"retrieve me", "text/plain")},
        headers=headers,
    )

    evidence_id = response.json()["id"]
    retrieval = client.get(f"/api/evidence/{evidence_id}", headers=headers)
    assert retrieval.status_code == 200
    data = retrieval.json()
    assert data["file_name"] == "retrieval.txt"
    assert "C:\\" not in data["storage_path"]
