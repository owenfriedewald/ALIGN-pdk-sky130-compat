#!/usr/bin/env python3
"""Patch an installed ALIGN runtime so layers.json NoGDS entries are not streamed."""

from __future__ import annotations

import argparse
import inspect
import shutil
from pathlib import Path


SENTINEL = "# ALIGN Sky130 compat: honor NoGDS layers"


def align_exporter_path() -> Path:
    import align  # type: ignore

    return Path(inspect.getfile(align)).resolve().parent / "cell_fabric" / "gen_gds_json.py"


def patch_source(text: str) -> str:
    if SENTINEL in text:
        return text

    text = text.replace(
        "  def createViaSref(via, nm, layers):\n"
        "\n"
        "    strct = {\"time\" : tme, \"strname\" : nm, \"elements\" : []}\n"
        "\n"
        "    for layer, rect in layers.items():\n"
        "      strct[\"elements\"].append ({\"type\": \"boundary\", \"layer\" : j[layer]['GdsLayerNo'], \"datatype\" : j[layer]['GdsDatatype']['Draw'],\n"
        "                                 \"xy\" : flat_rect_to_boundary( rect)})\n",
        "  no_gds_layers = {entry.get('Layer') for entry in j1.get('Abstraction', []) if entry.get('NoGDS')}\n"
        f"  {SENTINEL}\n"
        "  def should_stream_layer(layer):\n"
        "    return layer not in no_gds_layers\n"
        "\n"
        "  def createViaSref(via, nm, layers):\n"
        "\n"
        "    strct = {\"time\" : tme, \"strname\" : nm, \"elements\" : []}\n"
        "\n"
        "    for layer, rect in layers.items():\n"
        "      if not should_stream_layer(layer): continue\n"
        "      strct[\"elements\"].append ({\"type\": \"boundary\", \"layer\" : j[layer]['GdsLayerNo'], \"datatype\" : j[layer]['GdsDatatype']['Draw'],\n"
        "                                 \"xy\" : flat_rect_to_boundary( rect)})\n",
    )
    text = text.replace(
        "      if k in via_gen_tbl: continue\n"
        "      if exclude_based_on_name( obj['netName']): continue    \n",
        "      if k in via_gen_tbl: continue\n"
        "      if not should_stream_layer(k): continue\n"
        "      if exclude_based_on_name( obj['netName']): continue    \n",
    )
    text = text.replace(
        "      if k not in via_gen_tbl: continue\n"
        "      if exclude_based_on_name( obj['netName']): continue\n",
        "      if k not in via_gen_tbl: continue\n"
        "      if not should_stream_layer(k): continue\n"
        "      if exclude_based_on_name( obj['netName']): continue\n",
    )
    text = text.replace(
        "  strct[\"elements\"].append ({\"type\": \"boundary\", \"layer\" : j['Bbox']['GdsLayerNo'], \"datatype\" : j['Bbox']['GdsDatatype']['Draw'],\n"
        "                    \"xy\" : flat_rect_to_boundary( list(map(scale,data['bbox'])))})\n",
        "  if should_stream_layer('Bbox') and 'Bbox' in j:\n"
        "    strct[\"elements\"].append ({\"type\": \"boundary\", \"layer\" : j['Bbox']['GdsLayerNo'], \"datatype\" : j['Bbox']['GdsDatatype']['Draw'],\n"
        "                      \"xy\" : flat_rect_to_boundary( list(map(scale,data['bbox'])))})\n",
    )

    if SENTINEL not in text:
        raise RuntimeError("Could not patch ALIGN gen_gds_json.py; expected source pattern not found")
    return text


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--path",
        type=Path,
        help="Optional explicit gen_gds_json.py path. Defaults to the installed align package.",
    )
    args = parser.parse_args()

    path = args.path or align_exporter_path()
    original = path.read_text()
    patched = patch_source(original)
    if patched == original:
        print(f"already patched: {path}")
        return 0

    backup = path.with_suffix(path.suffix + ".bak")
    if not backup.exists():
        shutil.copy2(path, backup)
    path.write_text(patched)
    print(f"patched: {path}")
    print(f"backup:  {backup}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
