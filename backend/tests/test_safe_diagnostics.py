import importlib
from io import StringIO

import pytest
from sqlalchemy.exc import DBAPIError, OperationalError

from app.core.diagnostics import safe_exception_diagnostics
from app.core.logging import logger


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


def test_database_initialization_logs_safe_diagnostics(monkeypatch):
    init_db_module = importlib.import_module("app.database.init_db")

    class FakeDatabaseError(Exception):
        sqlstate = "28P01"

    def fail_to_initialize(*, bind):
        raise OperationalError(
            "SELECT 1",
            {"password": "must-not-be-logged"},
            FakeDatabaseError("database-password=must-not-be-logged"),
        )

    monkeypatch.setattr(init_db_module.Base.metadata, "create_all", fail_to_initialize)
    output = StringIO()
    sink_id = logger.add(output, format="{message}", level="ERROR", enqueue=False)
    try:
        with pytest.raises(OperationalError):
            init_db_module.init_db()
    finally:
        logger.remove(sink_id)

    assert "OperationalError" in output.getvalue()
    assert "28P01" in output.getvalue()
    assert "must-not-be-logged" not in output.getvalue()
