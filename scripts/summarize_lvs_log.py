#!/usr/bin/env python3
"""Summarize Netgen LVS logs/reports without changing the raw evidence."""

from __future__ import annotations

import argparse
from pathlib import Path


KEYWORDS = (
    "match",
    "mismatch",
    "netlists do not match",
    "circuits match",
    "property",
    "device",
    "net",
    "failed",
    "error",
)


def summarize(path: Path) -> None:
    lines = path.read_text(errors="ignore").splitlines()
    print(f"LVS file: {path}")
    print(f"lines: {len(lines)}")
    print("Key lines:")
    count = 0
    for idx, line in enumerate(lines, start=1):
        if any(keyword in line.lower() for keyword in KEYWORDS):
            print(f"{idx}: {line}")
            count += 1
            if count >= 240:
                print("... truncated additional key lines")
                break
    print()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", type=Path, help="Netgen log/report paths")
    args = parser.parse_args()

    for path in args.paths:
        summarize(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
