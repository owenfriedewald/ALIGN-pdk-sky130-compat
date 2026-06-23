#!/usr/bin/env python3
"""Patch an installed ALIGN runtime for Sky130 verification stream-out."""

from __future__ import annotations

import argparse
import inspect
import shutil
from pathlib import Path


GDS_SENTINEL = "# ALIGN Sky130 compat: honor NoGDS layers"
PNR_SENTINEL = "# ALIGN Sky130 compat: top-level labels and NoGDS outline"


def align_exporter_path() -> Path:
    import align  # type: ignore

    return Path(inspect.getfile(align)).resolve().parent / "cell_fabric" / "gen_gds_json.py"


def align_pnr_main_path() -> Path:
    import align  # type: ignore

    return Path(inspect.getfile(align)).resolve().parent / "pnr" / "main.py"


def patch_gds_source(text: str) -> str:
    if GDS_SENTINEL in text:
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
        f"  {GDS_SENTINEL}\n"
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

    if GDS_SENTINEL not in text:
        raise RuntimeError("Could not patch ALIGN gen_gds_json.py; expected source pattern not found")
    return text


def patch_pnr_source(text: str) -> str:
    if PNR_SENTINEL in text:
        return text

    text = text.replace(
        "    if gds_json and toplevel:\n"
        "        # Hack in Outline layer\n"
        "        # Should be part of post processor\n"
        "        # insert is slower than append but it improves the visulazation by drawing outline behind the other rectangles\n"
        "        d['terminals'].insert(0, {\"layer\": \"Outline\", \"netName\": None, \"netType\": \"drawing\", \"rect\": d['bbox']})\n",
        f"    {PNR_SENTINEL}\n"
        "    no_gds_layers = {name for name, entry in cnv.pdk.items() if entry.get('NoGDS')}\n"
        "    if gds_json and toplevel and 'Outline' not in no_gds_layers:\n"
        "        # Hack in Outline layer\n"
        "        # Should be part of post processor\n"
        "        # insert is slower than append but it improves the visulazation by drawing outline behind the other rectangles\n"
        "        d['terminals'].insert(0, {\"layer\": \"Outline\", \"netName\": None, \"netType\": \"drawing\", \"rect\": d['bbox']})\n",
    )
    text = text.replace(
        "                labels = None\n"
        "                if toplevel:\n"
        "                    labels = [i.name for i in hN.blockPins].extend([i.name for i in hN.PowerNets])\n"
        "                gen_gds_json.translate(\n",
        "                labels = None\n"
        "                if toplevel:\n"
        "                    labels = [i.name for i in hN.blockPins] + [i.name for i in hN.PowerNets]\n"
        "                gen_gds_json.translate(\n",
    )

    if PNR_SENTINEL not in text:
        raise RuntimeError("Could not patch ALIGN pnr/main.py; expected source pattern not found")
    return text


def patch_file(path: Path, patcher) -> bool:
    original = path.read_text()
    patched = patcher(original)
    if patched == original:
        print(f"already patched: {path}")
        return False

    backup = path.with_suffix(path.suffix + ".bak")
    if not backup.exists():
        shutil.copy2(path, backup)
    path.write_text(patched)
    print(f"patched: {path}")
    print(f"backup:  {backup}")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--path",
        type=Path,
        help="Optional explicit gen_gds_json.py path. Defaults to the installed align package.",
    )
    parser.add_argument(
        "--pnr-main-path",
        type=Path,
        help="Optional explicit pnr/main.py path. Defaults to the installed align package.",
    )
    args = parser.parse_args()

    patch_file(args.path or align_exporter_path(), patch_gds_source)
    patch_file(args.pnr_main_path or align_pnr_main_path(), patch_pnr_source)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
