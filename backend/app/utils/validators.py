from pathlib import Path
from typing import Any

from app.core.constants import ALLOWED_FILE_EXTENSIONS, MAX_UPLOAD_SIZE_BYTES


def is_valid_extension(file_name: str) -> bool:
    extension = Path(file_name).suffix.lower().lstrip('.')
    return extension in ALLOWED_FILE_EXTENSIONS


def is_valid_upload_size(file_size: int) -> bool:
    return 0 < file_size <= MAX_UPLOAD_SIZE_BYTES


def is_non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())
