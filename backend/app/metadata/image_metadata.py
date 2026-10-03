from __future__ import annotations

from PIL import Image
from PIL.ExifTags import TAGS

from app.metadata.metadata import build_extraction_result, normalize_datetime


def _safe_exif(exif_data) -> dict:
    if not exif_data:
        return {}

    result: dict[str, object] = {}
    for tag_id, value in exif_data.items():
        name = TAGS.get(tag_id, str(tag_id))
        if isinstance(value, bytes):
            try:
                decoded = value.decode("utf-8", errors="ignore")
            except Exception:
                decoded = value.hex()
            result[str(name)] = decoded
        elif isinstance(value, tuple):
            result[str(name)] = [item for item in value]
        else:
            result[str(name)] = value
    return result


def extract_image_metadata(path: str):
    try:
        with Image.open(path) as image:
            metadata = {
                "format": image.format or "unknown",
                "width": image.width,
                "height": image.height,
                "mode": image.mode,
            }

            info = image.info or {}
            if info.get("dpi"):
                metadata["dpi"] = info["dpi"]
            if info.get("compression"):
                metadata["compression"] = info["compression"]

            exif = image.getexif()
            if exif:
                exif_data = _safe_exif(exif)
                metadata["exif"] = exif_data

                make = exif_data.get("Make")
                model = exif_data.get("Model")
                if make:
                    metadata["camera_make"] = str(make)
                if model:
                    metadata["camera_model"] = str(model)

                for key in ("DateTime", "DateTimeOriginal", "DateTimeDigitized"):
                    value = exif_data.get(key)
                    if value:
                        metadata[key] = normalize_datetime(value)

                gps = exif_data.get("GPSInfo")
                if gps:
                    metadata["gps"] = gps

            return build_extraction_result(
                metadata=metadata,
                extraction_status="success" if metadata else "partial",
                extraction_errors=[],
            )
    except Exception as exc:  # pragma: no cover - defensive error handling
        return build_extraction_result(
            metadata={},
            extraction_status="failed",
            extraction_errors=[f"Image metadata extraction failed: {exc}"],
        )
