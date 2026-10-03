import hashlib
from pathlib import Path


def compute_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def compute_sha256_file(path: str | Path, chunk_size: int = 65536) -> str:
    digest = hashlib.sha256()
    file_path = Path(path)

    with file_path.open("rb") as file_handle:
        while True:
            chunk = file_handle.read(chunk_size)
            if not chunk:
                break
            digest.update(chunk)

    return digest.hexdigest()
