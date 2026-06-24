from pathlib import Path
import hashlib


def calculate_file_sha256(file_path: str | Path) -> str:
    path = Path(file_path)

    sha256 = hashlib.sha256()

    with path.open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            sha256.update(block)

    return sha256.hexdigest()

#This gives every uploaded ebook a stable fingerprint. Same file = same hash.