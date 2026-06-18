#!/usr/bin/env python3
"""Discover candidate GDS/SPICE/open_pdks inputs and suggest validation commands."""

from __future__ import annotations

import argparse
import re
import shutil
from pathlib import Path


COMMON_ROOTS = [
    ".",
    "~/data",
    "~/share/pdk",
    "~/data/pdk",
    "~/data/open_pdks",
    "~/pdks",
    "/usr/local/share/pdk",
    "/usr/share/pdk",
]

SUBCKT_RE = re.compile(r"^\s*\.subckt\s+(\S+)", re.IGNORECASE)


def existing_roots(values: list[str]) -> list[Path]:
    roots = []
    for value in values:
        path = Path(value).expanduser()
        if path.exists():
            roots.append(path.resolve())
    return roots


def find_files(roots: list[Path], suffixes: tuple[str, ...], limit: int) -> list[Path]:
    found: list[Path] = []
    for root in roots:
        for path in root.rglob("*"):
            if path.is_file() and path.name.lower().endswith(suffixes):
                if "upstream/skywater-pdk/.git" in str(path):
                    continue
                found.append(path)
    return sorted(found, key=rank_candidate)[:limit]


def rank_candidate(path: Path) -> tuple[int, str]:
    text = str(path)
    if "/examples/" in text:
        bucket = 0
    elif "/reports/" in text:
        bucket = 1
    elif "/tests/" in text:
        bucket = 3
    elif "/SKY130_PDK/" in text or "/upstream/" in text:
        bucket = 4
    else:
        bucket = 2
    return bucket, text


def find_open_pdks_roots(roots: list[Path], limit: int) -> list[Path]:
    found: list[Path] = []
    for root in roots:
        for magicrc in root.rglob("libs.tech/magic/sky130A.magicrc"):
            candidate = magicrc.parents[2]
            setup = candidate / "libs.tech/netgen/sky130A_setup.tcl"
            if setup.exists() and candidate not in found:
                found.append(candidate)
                if len(found) >= limit:
                    return found
    return found


def first_subckt(path: Path) -> str | None:
    for line in path.read_text(errors="ignore").splitlines():
        match = SUBCKT_RE.match(line)
        if match:
            return match.group(1)
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", action="append", default=[], help="Root to scan. Repeatable.")
    parser.add_argument("--include-common", action="store_true", help="Scan common local PDK/data roots.")
    parser.add_argument("--limit", type=int, default=20)
    args = parser.parse_args()

    root_values = args.root or ["."]
    if args.include_common:
        root_values.extend(COMMON_ROOTS)
    roots = existing_roots(root_values)

    gdss = find_files(roots, (".gds", ".gds.gz"), args.limit)
    spices = find_files(roots, (".sp", ".spice"), args.limit)
    pdk_roots = find_open_pdks_roots(roots, args.limit)

    print("Tools:")
    for tool in ("magic", "netgen", "schematic2layout.py", "klayout"):
        print(f"  {tool}: {shutil.which(tool) or 'missing'}")

    print("\nRoots scanned:")
    for root in roots:
        print(f"  - {root}")

    print("\nGDS candidates:")
    for path in gdss:
        print(f"  - {path}")
    if not gdss:
        print("  <none>")

    print("\nSPICE candidates:")
    for path in spices:
        top = first_subckt(path)
        print(f"  - {path}" + (f"  top={top}" if top else ""))
    if not spices:
        print("  <none>")

    print("\nopen_pdks sky130A candidates:")
    for path in pdk_roots:
        print(f"  - {path}")
    if not pdk_roots:
        print("  <none>")

    if gdss and spices and pdk_roots:
        spice = spices[0]
        top = first_subckt(spice) or "TOP"
        print("\nSuggested first command:")
        print("scripts/run_one_circuit_validation.sh \\")
        print(f"  --open-pdks-root {pdk_roots[0]} \\")
        print(f"  --gds {gdss[0]} \\")
        print(f"  --schematic {spice} \\")
        print(f"  --top {top} \\")
        print(f"  --out-dir reports/before_after/{top}")
    else:
        print("\nNo complete validation tuple found yet.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
