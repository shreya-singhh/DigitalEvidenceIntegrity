import re
import traceback
from pathlib import Path
from typing import Any

from sqlalchemy.exc import DBAPIError


_SQLSTATE_PATTERN = re.compile(r"^[0-9A-Z]{5}$")


def safe_exception_diagnostics(exc: BaseException) -> dict[str, Any]:
    diagnostics: dict[str, Any] = {
        "exception_type": type(exc).__name__,
        "exception_module": type(exc).__module__,
    }

    if isinstance(exc, OSError) and isinstance(exc.errno, int):
        diagnostics["os_error_code"] = exc.errno

    if isinstance(exc, DBAPIError):
        driver_error = exc.orig
        diagnostics["database_driver_error_type"] = type(driver_error).__name__
        sqlstate = getattr(driver_error, "sqlstate", None) or getattr(driver_error, "pgcode", None)
        if isinstance(sqlstate, str) and _SQLSTATE_PATTERN.fullmatch(sqlstate):
            diagnostics["database_sqlstate"] = sqlstate

    frames = traceback.extract_tb(exc.__traceback__)
    if frames:
        diagnostics["source_frames"] = [
            f"{Path(frame.filename).name}:{frame.lineno}:{frame.name}"
            for frame in frames[-8:]
        ]

    return diagnostics
