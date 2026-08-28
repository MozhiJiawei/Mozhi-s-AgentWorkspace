from __future__ import annotations

from pathlib import Path


def canonical_file_bytes(path: Path) -> bytes:
    """Return platform-independent bytes for fingerprinting repository files."""
    content = path.read_bytes()
    if b"\0" in content:
        return content

    try:
        content.decode("utf-8")
    except UnicodeDecodeError:
        return content

    return content.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
