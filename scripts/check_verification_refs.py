#!/usr/bin/env python3
"""Check for local Sky130 Magic/Netgen/open_pdks verification references."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path


REFERENCE_PATTERNS = {
    "Magic tech": ["**/sky130A.tech"],
    "Magic rc": ["**/.magicrc", "**/sky130A.magicrc"],
    "Netgen setup Tcl": ["**/sky130A_setup.tcl", "**/*netgen*setup*.tcl", "**/*setup*.tcl"],
    "Magic extraction": ["**/*extract*.tcl", "**/*ext*.tcl", "**/*pex*.tcl"],
    "GDS layer maps": ["**/gds_layers.csv", "**/*gds*layer*.csv", "**/*layers*.map"],
    "SPICE model files": ["**/*.spice", "**/*.sp", "**/*.lib", "**/*.pm3"],
    "Primitive device docs": ["**/device-details/**/*.rst", "**/table-f2a-lvs.tsv"],
    "Rule CSVs/docs": ["**/docs/rules/**/*.csv", "**/docs/rules/**/*.tsv", "**/docs/verification/**/*.rst"],
}

EXPECTED_OPEN_PDKS_SUFFIXES = [
    "libs.tech/magic/sky130A.tech",
    "libs.tech/magic/sky130A.magicrc",
    "libs.tech/netgen/sky130A_setup.tcl",
]

COMMON_SEARCH_ROOTS = [
    "~/data",
    "~/share/pdk",
    "~/data/pdk",
    "~/data/open_pdks",
    "~/pdks",
    "/usr/local/share/pdk",
    "/usr/share/pdk",
]


def find_matches(root: Path, patterns: list[str], limit: int) -> list[Path]:
    matches: list[Path] = []
    if not root.exists():
        return matches
    for pattern in patterns:
        for path in sorted(root.glob(pattern)):
            if path.is_file() and path not in matches:
                matches.append(path)
                if len(matches) >= limit:
                    return matches
    return matches


def rel(path: Path, base: Path) -> str:
    try:
        return str(path.relative_to(base))
    except ValueError:
        return str(path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("."), help="Repository root to inspect")
    parser.add_argument(
        "--open-pdks-root",
        type=Path,
        help="Optional installed open_pdks sky130A root, e.g. .../share/pdk/sky130A",
    )
    parser.add_argument(
        "--search-common",
        action="store_true",
        help="Also scan common local PDK locations such as ~/pdks and /usr/local/share/pdk",
    )
    parser.add_argument("--limit", type=int, default=12, help="Maximum paths to print per category")
    args = parser.parse_args()

    roots = [args.repo_root.resolve()]
    if args.open_pdks_root:
        roots.append(args.open_pdks_root.resolve())
    if args.search_common:
        for candidate in COMMON_SEARCH_ROOTS:
            path = Path(candidate).expanduser()
            if path.exists():
                roots.append(path.resolve())

    print("Sky130 verification reference preflight")
    print(f"repo-root: {args.repo_root.resolve()}")
    if args.open_pdks_root:
        print(f"open-pdks-root: {args.open_pdks_root.resolve()}")
    print("tools:")
    for tool in ("magic", "netgen", "klayout", "schematic2layout.py"):
        print(f"  {tool}: {shutil.which(tool) or 'missing'}")
    if args.search_common:
        print("search roots:")
        for root in roots:
            print(f"  - {root}")
    print()

    missing_required = 0
    for label, patterns in REFERENCE_PATTERNS.items():
        matches: list[Path] = []
        for root in roots:
            matches.extend(find_matches(root, patterns, args.limit - len(matches)))
            if len(matches) >= args.limit:
                break
        status = "found" if matches else "missing"
        print(f"{label}: {status}")
        for path in matches:
            owner = next((root for root in roots if str(path).startswith(str(root))), args.repo_root.resolve())
            print(f"  - {rel(path, owner)}")
        if not matches and label in {"Magic tech", "Magic rc", "Netgen setup Tcl"}:
            missing_required += 1
        print()

    if args.open_pdks_root:
        print("Expected open_pdks sky130A files:")
        for suffix in EXPECTED_OPEN_PDKS_SUFFIXES:
            path = args.open_pdks_root / suffix
            print(f"  {'ok' if path.exists() else 'missing'}  {path}")
            if not path.exists():
                missing_required += 1

    return 1 if missing_required else 0


if __name__ == "__main__":
    raise SystemExit(main())
