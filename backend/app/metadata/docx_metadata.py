from __future__ import annotations

from docx import Document

from app.metadata.metadata import build_extraction_result, normalize_datetime


def extract_docx_metadata(path: str):
    try:
        document = Document(path)
        core = document.core_properties
        metadata = {
            "title": core.title,
            "subject": core.subject,
            "author": core.author,
            "keywords": core.keywords,
            "comments": core.comments,
            "last_modified_by": core.last_modified_by,
            "created": normalize_datetime(core.created),
            "modified": normalize_datetime(core.modified),
        }
        cleaned = {key: value for key, value in metadata.items() if value not in (None, "", " ")}
        return build_extraction_result(
            metadata=cleaned,
            extraction_status="success" if cleaned else "partial",
            extraction_errors=[] if cleaned else ["DOCX metadata is empty or missing."],
        )
    except Exception as exc:  # pragma: no cover - defensive error handling
        return build_extraction_result(
            metadata={},
            extraction_status="failed",
            extraction_errors=[f"DOCX metadata extraction failed: {exc}"],
        )
