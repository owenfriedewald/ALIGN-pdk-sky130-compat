#!/usr/bin/env python3
"""Write a Magic-importable verification GDS by dropping known ALIGN helper layers."""

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


def parse_layer(value: str) -> str:
    if ":" not in value:
        raise argparse.ArgumentTypeError(f"Expected LAYER:DATATYPE, got {value!r}")
    layer, datatype = value.split(":", 1)
    try:
        return f"{int(layer)}:{int(datatype)}"
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"Expected integer LAYER:DATATYPE, got {value!r}") from exc


def load_drop_layers(path: Path | None) -> dict[str, str]:
    if path is None or not path.exists():
        return {}
    data = json.loads(path.read_text())
    values = data.get("verification_drop_layers", {})
    if not isinstance(values, dict):
        return {}
    return {parse_layer(str(key)): str(reason) for key, reason in values.items()}


def used_layer_counts(layout) -> dict[str, tuple[int, int, int, int]]:
    counts: dict[str, tuple[int, int, int, int]] = {}
    for layer_index in layout.layer_indices():
        info = layout.get_info(layer_index)
        count = sum(cell.shapes(layer_index).size() for cell in layout.each_cell())
        if count:
            key = f"{info.layer}:{info.datatype}"
            counts[key] = (info.layer, info.datatype, layer_index, count)
    return counts


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_gds", type=Path, help="Source GDS. This file is never modified.")
    parser.add_argument("-o", "--output", type=Path, required=True, help="Sanitized GDS output path.")
    parser.add_argument(
        "--compat-map",
        type=Path,
        default=Path("SKY130_PDK/openpdks_compat.json"),
        help="Compatibility metadata JSON containing verification_drop_layers.",
    )
    parser.add_argument(
        "--drop-layer",
        action="append",
        default=[],
        type=parse_layer,
        help="Extra LAYER:DATATYPE to drop. Repeatable.",
    )
    parser.add_argument(
        "--keep-layer",
        action="append",
        default=[],
        type=parse_layer,
        help="LAYER:DATATYPE to keep even if metadata would drop it. Repeatable.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report kept/dropped layers without writing an output GDS.",
    )
    args = parser.parse_args()

    if not args.input_gds.exists():
        raise SystemExit(f"ERROR: missing input GDS: {args.input_gds}")
    if args.output.resolve() == args.input_gds.resolve():
        raise SystemExit("ERROR: output must not overwrite input GDS")

    drop_reasons = load_drop_layers(args.compat_map)
    for layer in args.drop_layer:
        drop_reasons[layer] = "Requested by --drop-layer."
    keep = set(args.keep_layer)

    layout = load_layout(args.input_gds)
    used = used_layer_counts(layout)
    drop = sorted(key for key in used if key in drop_reasons and key not in keep)

    print(f"Input GDS: {args.input_gds}")
    print(f"Output GDS: {args.output}")
    print(f"Top cells: {', '.join(cell.name for cell in layout.top_cells())}")
    print("Layer decision:")
    for key in sorted(used, key=lambda item: tuple(int(part) for part in item.split(":"))):
        layer, datatype, _layer_index, count = used[key]
        if key in drop:
            print(f"  drop {layer}:{datatype} shapes={count} reason={drop_reasons[key]}")
        else:
            print(f"  keep {layer}:{datatype} shapes={count}")

    if args.dry_run:
        return 0

    for key in sorted(drop, reverse=True):
        _layer, _datatype, layer_index, _count = used[key]
        layout.delete_layer(layer_index)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    layout.write(str(args.output))
    print(f"Wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
