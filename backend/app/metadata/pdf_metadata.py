from __future__ import annotations

from pypdf import PdfReader

from app.metadata.metadata import build_extraction_result, normalize_datetime


def extract_pdf_metadata(path: str):
    try:
        reader = PdfReader(path)
        metadata = reader.metadata or {}
        normalized = {
            "title": metadata.title,
            "author": metadata.author,
            "subject": metadata.subject,
            "creator": metadata.creator,
            "producer": metadata.producer,
            "creation_date": normalize_datetime(getattr(metadata, "/CreationDate", None)),
            "modification_date": normalize_datetime(getattr(metadata, "/ModDate", None)),
            "page_count": len(reader.pages),
        }
        cleaned = {key: value for key, value in normalized.items() if value not in (None, "", "Unknown")}

        status = "success" if cleaned else "partial"
        errors: list[str] = []
        if not cleaned:
            errors.append("PDF metadata is missing or empty.")

        return build_extraction_result(metadata=cleaned, extraction_status=status, extraction_errors=errors)
    except Exception as exc:  # pragma: no cover - defensive error handling
        return build_extraction_result(
            metadata={},
            extraction_status="failed",
            extraction_errors=[f"PDF metadata extraction failed: {exc}"],
        )
