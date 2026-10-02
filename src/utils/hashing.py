import hashlib
from pathlib import Path

def hash_text(text: str) -> str:
    """Compute SHA-256 hash of text."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def hash_bytes(data: bytes) -> str:
    """Compute SHA-256 hash of byte sequence."""
    return hashlib.sha256(data).hexdigest()

def hash_file(file_path: str | Path) -> str:
    """Compute SHA-256 hash of a file on disk."""
    p = Path(file_path)
    if not p.is_file():
        return ""
    hasher = hashlib.sha256()
    with open(p, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()
