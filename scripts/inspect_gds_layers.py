#!/usr/bin/env python3
"""Inspect layer/datatype usage in a GDS file and compare with ALIGN/open_pdks metadata."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def load_layout(path: Path):
    try:
        import klayout.db as kdb  # type: ignore
    except ImportError:
        try:
            import pya as kdb  # type: ignore
        except ImportError as exc:
            raise SystemExit(
                "ERROR: KLayout Python module not available. Install python3-klayout or run in a KLayout Python environment."
            ) from exc

    layout = kdb.Layout()
    layout.read(str(path))
    return layout


def load_expected(path: Path) -> dict[str, str]:
    data = json.loads(path.read_text())
    expected: dict[str, str] = {}
    for section in ("verification_layer_map", "verification_purpose_layers"):
        for align_name, info in data.get(section, {}).items():
            if isinstance(info, dict) and "gds" in info:
                expected[str(info["gds"])] = f"{align_name}->{info.get('official', '')}"
    for gds, reason in data.get("verification_drop_layers", {}).items():
        expected[str(gds)] = f"<drop candidate: {reason}>"
    return expected


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("gds", type=Path)
    parser.add_argument(
        "--compat-map",
        type=Path,
        default=Path("SKY130_PDK/openpdks_compat.json"),
        help="Compatibility metadata JSON containing verification_layer_map.",
    )
    args = parser.parse_args()

    layout = load_layout(args.gds)
    expected = load_expected(args.compat_map) if args.compat_map.exists() else {}

    used = []
    for layer_index in layout.layer_indices():
        info = layout.get_info(layer_index)
        count = sum(cell.shapes(layer_index).size() for cell in layout.each_cell())
        if count:
            key = f"{info.layer}:{info.datatype}"
            used.append((info.layer, info.datatype, count, expected.get(key, "<unmapped>")))

    print(f"GDS: {args.gds}")
    print(f"top cells: {', '.join(cell.name for cell in layout.top_cells())}")
    print("Used layers:")
    for layer, datatype, count, mapping in sorted(used):
        print(f"  - {layer}:{datatype} shapes={count} mapping={mapping}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
