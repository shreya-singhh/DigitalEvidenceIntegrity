from __future__ import annotations

from pathlib import Path
from typing import Any

from app.metadata.audio_metadata import extract_audio_metadata
from app.metadata.docx_metadata import extract_docx_metadata
from app.metadata.image_metadata import extract_image_metadata
from app.metadata.metadata import build_extraction_result
from app.metadata.pdf_metadata import extract_pdf_metadata
from app.metadata.text_metadata import extract_text_metadata
from app.metadata.video_metadata import extract_video_metadata


class MetadataService:
    """Normalize metadata extraction across supported evidence file types."""

    @staticmethod
    def _detect_file_type(filename: str | None, mime_type: str | None = None) -> tuple[str, str | None]:
        name = (filename or "").lower()
        mime = (mime_type or "").lower()

        if name.endswith((".jpg", ".jpeg")):
            return "image/jpeg", mime or "image/jpeg"
        if name.endswith(".png"):
            return "image/png", mime or "image/png"
        if name.endswith(".pdf"):
            return "application/pdf", mime or "application/pdf"
        if name.endswith(".docx"):
            return "application/vnd.openxmlformats-officedocument.wordprocessingml.document", mime or "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        if name.endswith(".txt"):
            return "text/plain", mime or "text/plain"
        if name.endswith((".mp3", ".wav", ".flac", ".aac", ".ogg")):
            return "audio", mime or "audio/mpeg"
        if name.endswith((".mp4", ".m4v", ".mov", ".avi", ".mkv")):
            return "video", mime or "video/mp4"

        if mime:
            if mime.startswith("image/"):
                return "image", mime
            if mime.startswith("audio/"):
                return "audio", mime
            if mime.startswith("video/"):
                return "video", mime
            if mime.startswith("text/"):
                return "text/plain", mime
            if mime.startswith("application/pdf"):
                return "application/pdf", mime
            if "docx" in mime or "word" in mime:
                return "application/vnd.openxmlformats-officedocument.wordprocessingml.document", mime

        return "unsupported", mime

    @staticmethod
    def extract_metadata_for_file(file_path: str | Path, filename: str | None = None, mime_type: str | None = None, sha256_hash: str | None = None) -> dict[str, Any]:
        path = Path(file_path)
        actual_name = filename or path.name
        file_type, resolved_mime = MetadataService._detect_file_type(actual_name, mime_type)

        if not path.exists():
            return {
                "file_type": file_type,
                "mime_type": resolved_mime,
                "metadata": {},
                "extraction_status": "failed",
                "extraction_errors": ["File not found."],
            }

        if file_type == "unsupported":
            return {
                "file_type": "unsupported",
                "mime_type": resolved_mime,
                "metadata": {},
                "extraction_status": "unsupported",
                "extraction_errors": ["Unsupported file type."],
            }

        errors: list[str] = []
        metadata: dict[str, Any] = {}

        try:
            if file_type in {"image/jpeg", "image/png", "image"}:
                result = extract_image_metadata(str(path))
            elif file_type == "application/pdf":
                result = extract_pdf_metadata(str(path))
            elif file_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                result = extract_docx_metadata(str(path))
            elif file_type == "text/plain":
                result = extract_text_metadata(str(path), filename=actual_name, mime_type=resolved_mime, sha256_hash=sha256_hash)
            elif file_type == "audio":
                result = extract_audio_metadata(str(path))
            elif file_type == "video":
                result = extract_video_metadata(str(path))
            else:
                result = {"metadata": {}, "extraction_status": "unsupported", "extraction_errors": ["Unsupported file type."]}

            if isinstance(result, dict):
                metadata = result.get("metadata", {}) or {}
                status = result.get("extraction_status", "success")
                errors = result.get("extraction_errors", []) or []
            else:
                metadata = {}
                status = "failed"
                errors = ["Extractor returned an invalid result."]
        except Exception as exc:  # pragma: no cover - defensive guard
            metadata = {}
            status = "failed"
            errors = [str(exc)]

        metadata.setdefault("filename", actual_name)
        metadata.setdefault("extension", Path(actual_name).suffix or "")
        metadata.setdefault("file_size", path.stat().st_size if path.exists() else 0)
        metadata.setdefault("mime_type", resolved_mime)
        if sha256_hash:
            metadata.setdefault("sha256_hash", sha256_hash)

        return {
            "file_type": file_type,
            "mime_type": resolved_mime,
            "metadata": metadata,
            "extraction_status": status,
            "extraction_errors": errors,
        }
