from __future__ import annotations

import shutil
import subprocess

from app.metadata.metadata import build_extraction_result


def extract_video_metadata(path: str):
    ffprobe_path = shutil.which("ffprobe")
    if not ffprobe_path:
        return build_extraction_result(
            metadata={},
            extraction_status="partial",
            extraction_errors=["ffprobe is not installed; video metadata extraction is unavailable."],
        )

    try:
        result = subprocess.run(
            [
                ffprobe_path,
                "-v",
                "error",
                "-print_format",
                "json",
                "-show_format",
                "-show_streams",
                str(path),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            return build_extraction_result(
                metadata={},
                extraction_status="partial",
                extraction_errors=[result.stderr.strip() or "Video file could not be analyzed."],
            )

        payload = __import__("json").loads(result.stdout or "{}")
        streams = payload.get("streams", []) or []
        format_info = payload.get("format", {}) or {}

        video_stream = next((stream for stream in streams if stream.get("codec_type") == "video"), {})
        audio_stream = next((stream for stream in streams if stream.get("codec_type") == "audio"), {})

        metadata = {
            "format": format_info.get("format_name") or format_info.get("format_long_name"),
            "duration": format_info.get("duration"),
            "width": video_stream.get("width"),
            "height": video_stream.get("height"),
            "video_codec": video_stream.get("codec_name"),
            "audio_codec": audio_stream.get("codec_name"),
            "bitrate": format_info.get("bit_rate"),
            "frame_rate": video_stream.get("r_frame_rate"),
        }
        cleaned = {key: value for key, value in metadata.items() if value not in (None, "", 0)}

        return build_extraction_result(
            metadata=cleaned,
            extraction_status="success" if cleaned else "partial",
            extraction_errors=[] if cleaned else ["Video metadata is empty or missing."],
        )
    except Exception as exc:  # pragma: no cover - defensive error handling
        return build_extraction_result(
            metadata={},
            extraction_status="partial",
            extraction_errors=[f"Video metadata extraction failed: {exc}"],
        )
