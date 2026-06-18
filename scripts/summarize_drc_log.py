#!/usr/bin/env python3
"""Summarize a Magic DRC log without filtering or modifying the raw log."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


COUNT_RE = re.compile(r"(?:total|Total).*?([0-9]+)")
KEYWORDS = ("error", "drc", "violation", "why", "count", "Illegal")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("log", type=Path, help="Magic DRC log path")
    parser.add_argument("--context-lines", type=int, default=0, help="Reserved for future use")
    args = parser.parse_args()

    lines = args.log.read_text(errors="ignore").splitlines()
    interesting = [
        (idx, line)
        for idx, line in enumerate(lines, start=1)
        if any(keyword.lower() in line.lower() for keyword in KEYWORDS)
    ]
    counts = [match.group(1) for line in lines for match in [COUNT_RE.search(line)] if match]

    print(f"DRC log: {args.log}")
    print(f"lines: {len(lines)}")
    if counts:
        print(f"numeric count candidates: {', '.join(counts)}")
    print()
    print("Key lines:")
    for idx, line in interesting[:200]:
        print(f"{idx}: {line}")
    if len(interesting) > 200:
        print(f"... truncated {len(interesting) - 200} additional key lines")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
