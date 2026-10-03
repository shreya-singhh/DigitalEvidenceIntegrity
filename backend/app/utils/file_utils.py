from pathlib import Path
from typing import BinaryIO


def save_file(destination: Path, content: BinaryIO) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("wb") as file_handle:
        file_handle.write(content.read())
    return destination
