import pytest
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("post", "/api/auth/email-otp/send"),
        ("post", "/api/auth/email-otp/verify"),
    ],
)
def test_removed_email_otp_endpoints_are_not_exposed(method: str, path: str) -> None:
    response = getattr(client, method)(path)

    assert response.status_code == 404
