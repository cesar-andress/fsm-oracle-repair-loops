#!/usr/bin/env python3
"""Verify SHA256 checksums for the frozen evidence bundle."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _artifact_lib import CHECKSUMS_IN_FREEZE, FREEZE_DIR, sha256_file


def main():
    if not CHECKSUMS_IN_FREEZE.is_file():
        print(f"MISSING: {CHECKSUMS_IN_FREEZE}", file=sys.stderr)
        return 1

    errors = 0
    checked = 0
    for line in CHECKSUMS_IN_FREEZE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split(None, 1)
        if len(parts) != 2:
            print(f"BAD LINE: {line}", file=sys.stderr)
            errors += 1
            continue
        expected, rel = parts[0], parts[1]
        path = FREEZE_DIR / rel
        if not path.is_file():
            print(f"MISSING FILE: {rel}", file=sys.stderr)
            errors += 1
            continue
        actual = sha256_file(path)
        checked += 1
        if actual != expected:
            print(f"MISMATCH: {rel}", file=sys.stderr)
            print(f"  expected {expected}", file=sys.stderr)
            print(f"  actual   {actual}", file=sys.stderr)
            errors += 1

    if errors:
        print(f"FAIL: {errors} error(s), {checked} file(s) checked", file=sys.stderr)
        return 1

    print(f"OK: {checked} file(s) verified under {FREEZE_DIR.relative_to(FREEZE_DIR.parent.parent)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
