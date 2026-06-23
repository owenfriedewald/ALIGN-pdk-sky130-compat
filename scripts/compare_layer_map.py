#!/usr/bin/env python3
"""Compare ALIGN Sky130 layer abstractions against SkyWater reference docs."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


EXPECTED_LAYER_MAP = {
    "Poly": "poly",
    "M1": "li1",
    "V0": "licon1",
    "M2": "met1",
    "V1": "mcon",
    "M3": "met2",
    "V2": "via",
    "M4": "met3",
    "V3": "via2",
    "M5": "met4",
    "V4": "via3",
    "M6": "met5",
    "V5": "via4",
    "Nwell": "nwell",
    "Tap": "tap",
    "Active": "diff",
    "Nselect": "nsdm",
    "Pselect": "psdm",
    "Lvt": "lvtn",
    "Hvt": "hvtp",
    "Npc": "npc",
    "CapMIMLayer": "capm",
}

SPECIAL_LAYERS = {
    "Fin": "ALIGN template artifact; no Sky130 planar GDS equivalent.",
    "Pc": "ALIGN generator parameter layer; mos.py emits the pc wire on Poly.",
    "Rvt": "VT helper/id layer; no direct base drawing layer match in docs.",
    "Slvt": "VT helper/id layer; no direct base drawing layer match in docs.",
    "CapMIMContact": "MIM-contact helper; validate against generated cap topology.",
    "Bbox": "ALIGN boundary/helper layer.",
    "Boundary": "ALIGN boundary/helper layer.",
    "Rboundary": "ALIGN boundary/helper layer.",
    "Cboundary": "ALIGN boundary/helper layer.",
    "Outline": "ALIGN boundary/helper layer.",
    "GuardRing": "Generator config, not a streamed GDS layer entry.",
    "Cap": "Generator config, not a streamed GDS layer entry.",
}


def load_compat(path: Path | None) -> tuple[dict[str, str], dict[str, str]]:
    if path is None or not path.exists():
        return EXPECTED_LAYER_MAP, SPECIAL_LAYERS
    data = json.loads(path.read_text())
    layer_data = data.get("verification_layer_map", {})
    special_data = data.get("special_layers", {})
    layer_map = {
        str(align_name): str(info["official"])
        for align_name, info in layer_data.items()
        if isinstance(info, dict) and "official" in info
    }
    special = {str(key): str(value) for key, value in special_data.items()}
    return layer_map or EXPECTED_LAYER_MAP, special or SPECIAL_LAYERS


def load_align_layers(path: Path) -> dict[str, dict]:
    with path.open() as fp:
        data = json.load(fp)
    return {entry["Layer"]: entry for entry in data["Abstraction"]}


def load_skywater_gds(path: Path) -> dict[str, str]:
    layers: dict[str, str] = {}
    with path.open(newline="") as fp:
        for row in csv.DictReader(fp):
            name = row["Layer name"].strip()
            purpose = row["Purpose"].strip()
            gds = row["GDS layer:datatype"].strip()
            if "drawing" in purpose and name not in layers:
                layers[name] = gds
    return layers


def align_gds(entry: dict) -> str | None:
    if "GdsLayerNo" not in entry:
        return None
    draw = entry.get("GdsDatatype", {}).get("Draw")
    if draw is None:
        return None
    return f"{entry['GdsLayerNo']}:{draw}"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--align-layers", type=Path, default=Path("SKY130_PDK/layers.json"))
    parser.add_argument(
        "--compat-map",
        type=Path,
        default=Path("SKY130_PDK/openpdks_compat.json"),
        help="Compatibility metadata JSON containing verification_layer_map.",
    )
    parser.add_argument(
        "--skywater-gds",
        type=Path,
        default=Path("upstream/skywater-pdk/docs/rules/gds_layers.csv"),
    )
    args = parser.parse_args()

    align = load_align_layers(args.align_layers)
    skywater = load_skywater_gds(args.skywater_gds)
    expected_layer_map, special_layers = load_compat(args.compat_map)

    rows = []
    failures = 0
    for align_name, entry in align.items():
        got = align_gds(entry)
        if align_name in expected_layer_map:
            official_name = expected_layer_map[align_name]
            expected = skywater.get(official_name)
            status = "ok" if got == expected else "mismatch"
            if status != "ok":
                failures += 1
            note = ""
        elif align_name in special_layers:
            official_name = ""
            expected = ""
            status = "skip"
            note = special_layers[align_name]
        else:
            official_name = ""
            expected = ""
            status = "unmapped"
            note = "No mapping encoded in compare script."
            failures += 1
        rows.append((align_name, official_name, got or "", expected or "", status, note))

    widths = [max(len(str(row[i])) for row in rows + [("ALIGN", "SkyWater", "ALIGN GDS", "SkyWater GDS", "Status", "Note")]) for i in range(6)]
    header = ("ALIGN", "SkyWater", "ALIGN GDS", "SkyWater GDS", "Status", "Note")
    print("  ".join(str(header[i]).ljust(widths[i]) for i in range(6)))
    print("  ".join("-" * widths[i] for i in range(6)))
    for row in rows:
        print("  ".join(str(row[i]).ljust(widths[i]) for i in range(6)))

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
