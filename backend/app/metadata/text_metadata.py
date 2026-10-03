from __future__ import annotations

import codecs
import re
from datetime import datetime
from pathlib import Path

from app.metadata.metadata import build_extraction_result


def _detect_text_encoding(raw: bytes) -> str | None:
    if not raw:
        return "utf-8"

    if raw.startswith(codecs.BOM_UTF8):
        return "utf-8-sig"
    if raw.startswith(codecs.BOM_UTF16_LE) or raw.startswith(codecs.BOM_UTF16_BE):
        return "utf-16"
    if raw.startswith(codecs.BOM_UTF32_LE) or raw.startswith(codecs.BOM_UTF32_BE):
        return "utf-32"

    if b"\x00" not in raw:
        for candidate in ("utf-8", "cp1252"):
            try:
                raw.decode(candidate)
                return candidate
            except UnicodeDecodeError:
                continue
        return None

    for candidate in ("utf-16", "utf-16-le", "utf-16-be", "utf-32", "utf-32-le", "utf-32-be"):
        try:
            raw.decode(candidate)
            return candidate
        except UnicodeDecodeError:
            continue
    return None


def extract_text_metadata(path: str, filename: str | None = None, mime_type: str | None = None, sha256_hash: str | None = None):
    file_path = Path(path)
    try:
        stats = file_path.stat()
        raw = file_path.read_bytes()
        encoding = _detect_text_encoding(raw) or "utf-8"
        text = raw.decode(encoding, errors="strict") if encoding else raw.decode("utf-8", errors="replace")

        created_ts = datetime.fromtimestamp(stats.st_ctime).isoformat()
        modified_ts = datetime.fromtimestamp(stats.st_mtime).isoformat()
        file_name = filename or file_path.name
        extension = file_path.suffix or ""

        metadata = {
            "filename": file_name,
            "extension": extension,
            "mime_type": (mime_type or "text/plain").lower(),
            "file_size": stats.st_size,
            "sha256_hash": sha256_hash,
            "character_count": len(text),
            "line_count": len(text.splitlines()) if text else 0,
            "word_count": len(re.findall(r"\b\w+\b", text)),
            "encoding": encoding,
            "created_at": created_ts,
            "modified_at": modified_ts,
            "created": created_ts,
            "modified": modified_ts,
        }
        metadata = {key: value for key, value in metadata.items() if value not in (None, "", [], {})}

        return build_extraction_result(
            metadata=metadata,
            extraction_status="success" if metadata else "partial",
            extraction_errors=[],
        )
    except Exception as exc:  # pragma: no cover - defensive guard
        return build_extraction_result(
            metadata={},
            extraction_status="failed",
            extraction_errors=[f"Text metadata extraction failed: {exc}"],
        )
