from __future__ import annotations

import re
from datetime import date, datetime
from pathlib import Path
from typing import Any


def _to_serializable(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, (list, tuple, set)):
        return [_to_serializable(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _to_serializable(item) for key, item in value.items()}
    return str(value)


def normalize_datetime(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if not isinstance(value, str):
        return _to_serializable(value)

    text = value.strip()
    if not text:
        return None

    if text.startswith("/D:"):
        text = text[3:]
    if text.startswith("D:"):
        text = text[2:]

    text = text.replace("Z", "+00:00")
    text = text.replace("'", "")

    try:
        if text.endswith("+00:00"):
            return datetime.fromisoformat(text).isoformat()
        if re.fullmatch(r"\d{8}", text):
            return datetime.strptime(text, "%Y%m%d").isoformat()
        if re.fullmatch(r"\d{14}", text):
            return datetime.strptime(text, "%Y%m%d%H%M%S").isoformat()
        if re.fullmatch(r"\d{14}Z", text):
            return datetime.strptime(text[:-1], "%Y%m%d%H%M%S").replace(tzinfo=None).isoformat()
        return datetime.fromisoformat(text).isoformat()
    except ValueError:
        return text


def build_extraction_result(
    metadata: dict[str, Any] | None = None,
    extraction_status: str = "success",
    extraction_errors: list[str] | None = None,
) -> dict[str, Any]:
    normalized_metadata = _to_serializable(metadata or {})
    normalized_errors = _to_serializable(extraction_errors or [])
    return {
        "metadata": normalized_metadata,
        "extraction_status": extraction_status,
        "extraction_errors": normalized_errors,
    }
