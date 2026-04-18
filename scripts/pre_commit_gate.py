from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import subprocess
import sys


@dataclass(frozen=True)
class Gate:
    name: str
    command: list[str]


def run_gate(root: Path, gate: Gate) -> int:
    print(f"[gate] {gate.name}")
    result = subprocess.run(gate.command, cwd=root)
    if result.returncode != 0:
        print(f"[fail] {gate.name}")
        return result.returncode
    print(f"[pass] {gate.name}")
    return 0


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    gates = [
        Gate(
            name="agents-registry",
            command=[sys.executable, "scripts/check_agents_registry.py"],
        ),
    ]

    for gate in gates:
        code = run_gate(root, gate)
        if code != 0:
            return code

    print("[pass] all pre-commit gates")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
