from __future__ import annotations

from mutagen import File

from app.metadata.metadata import build_extraction_result, normalize_datetime


def extract_audio_metadata(path: str):
    try:
        audio = File(path)
        if audio is None:
            return build_extraction_result(
                metadata={},
                extraction_status="failed",
                extraction_errors=["Audio file could not be parsed."],
            )

        info = getattr(audio, "info", None)
        tags = getattr(audio, "tags", {}) or {}

        metadata = {
            "format": getattr(info, "codec", None) or getattr(audio, "mime", [None])[0] or type(audio).__name__,
            "duration": getattr(info, "length", None),
            "bitrate": getattr(info, "bitrate", None),
            "sample_rate": getattr(info, "sample_rate", None),
            "channels": getattr(info, "channels", None),
            "title": getattr(tags.get("TIT2"), "text", [None])[0] if tags.get("TIT2") else None,
            "artist": getattr(tags.get("TPE1"), "text", [None])[0] if tags.get("TPE1") else None,
            "album": getattr(tags.get("TALB"), "text", [None])[0] if tags.get("TALB") else None,
            "genre": getattr(tags.get("TCON"), "text", [None])[0] if tags.get("TCON") else None,
            "year": getattr(tags.get("TDRC"), "text", [None])[0] if tags.get("TDRC") else None,
        }
        metadata = {key: normalize_datetime(value) if key in {"year"} and value else value for key, value in metadata.items()}
        cleaned = {key: value for key, value in metadata.items() if value not in (None, "", 0)}

        return build_extraction_result(
            metadata=cleaned,
            extraction_status="success" if cleaned else "partial",
            extraction_errors=[] if cleaned else ["Audio metadata is empty or missing."],
        )
    except Exception as exc:  # pragma: no cover - defensive error handling
        return build_extraction_result(
            metadata={},
            extraction_status="failed",
            extraction_errors=[f"Audio metadata extraction failed: {exc}"],
        )
