from sqlalchemy.exc import DBAPIError

from app.core.diagnostics import safe_exception_diagnostics


def test_database_diagnostics_include_sqlstate_without_exposing_error_text():
    class FakeDatabaseError(Exception):
        sqlstate = "28P01"

    try:
        raise DBAPIError(
            "SELECT 1",
            {"password": "must-not-be-logged"},
            FakeDatabaseError("database-password=must-not-be-logged"),
        )
    except DBAPIError as exc:
        diagnostics = safe_exception_diagnostics(exc)

    assert diagnostics["exception_type"] == "DBAPIError"
    assert diagnostics["database_driver_error_type"] == "FakeDatabaseError"
    assert diagnostics["database_sqlstate"] == "28P01"
    assert "must-not-be-logged" not in repr(diagnostics)
    assert diagnostics["source_frames"]


def test_unstructured_exception_diagnostics_omit_exception_message():
    try:
        raise RuntimeError("secret-value-must-not-be-logged")
    except RuntimeError as exc:
        diagnostics = safe_exception_diagnostics(exc)

    assert diagnostics["exception_type"] == "RuntimeError"
    assert "secret-value-must-not-be-logged" not in repr(diagnostics)
    assert diagnostics["source_frames"]
