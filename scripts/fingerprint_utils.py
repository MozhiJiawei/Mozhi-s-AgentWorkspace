from __future__ import annotations

from pathlib import Path
import subprocess


def canonical_file_hashes(repository_root: Path, paths: list[Path]) -> list[bytes]:
    """Hash files after Git clean filters normalize their checkout representation."""
    relatives = [path.relative_to(repository_root).as_posix() for path in paths]
    if not relatives:
        return []

    result = subprocess.run(
        ["git", "hash-object", "--stdin-paths"],
        cwd=repository_root,
        check=False,
        capture_output=True,
        encoding="utf-8",
        input="\n".join(relatives) + "\n",
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or "unknown git hash-object error"
        raise RuntimeError(f"Cannot fingerprint files in {repository_root}: {detail}")

    hashes = result.stdout.splitlines()
    if len(hashes) != len(relatives):
        raise RuntimeError(
            f"Expected {len(relatives)} file hashes in {repository_root}, got {len(hashes)}"
        )
    return [value.encode("ascii") for value in hashes]
