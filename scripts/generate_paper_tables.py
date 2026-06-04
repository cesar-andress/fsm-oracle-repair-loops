#!/usr/bin/env python3
"""Regenerate LaTeX tables under tables/ from frozen evidence."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _artifact_lib import TABLES_DIR, write_all_tables


def main() -> None:
    paths = write_all_tables()
    print(f"Wrote {len(paths)} table(s) to {TABLES_DIR}/")
    for p in sorted(paths):
        print(f"  {p.name}")


if __name__ == "__main__":
    main()
