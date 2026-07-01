from __future__ import annotations

import argparse
from pathlib import Path
import sys

QA_ROOT = Path(__file__).resolve().parent.parent / "loops" / "material-quality-guardian" / "qa"
sys.path.insert(0, str(QA_ROOT))

from docs_publish_state import write_publish_state


def main() -> int:
    parser = argparse.ArgumentParser(description="Write docs publish-state metadata for the built site.")
    parser.add_argument("--output", required=True, help="Output JSON path for publish-state metadata.")
    args = parser.parse_args()

    output = Path(args.output).resolve()
    state = write_publish_state(output)
    print(output)
    print(state["overall_source_fingerprint"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
