#!/usr/bin/env python3
"""Regenerate PDF figures under figures/ from frozen evidence."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _artifact_lib import FIGURES_DIR, write_all_figures


def main() -> None:
    paths = write_all_figures()
    print(f"Wrote {len(paths)} figure(s) to {FIGURES_DIR}/")
    for p in paths:
        print(f"  {p.name}")


if __name__ == "__main__":
    main()
