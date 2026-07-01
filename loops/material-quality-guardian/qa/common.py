from __future__ import annotations

from pathlib import Path


def repo_root() -> Path:
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / "README.md").is_file() and (parent / "skills").is_dir():
            return parent
    raise RuntimeError(f"Cannot locate repository root from {current}")
