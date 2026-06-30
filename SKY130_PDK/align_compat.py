"""ALIGN runtime compatibility patches for this experimental Sky130 PDK.

The current ALIGN release streams helper/boundary layers into Python GDS and
has a top-level label allow-list bug.  Those are ALIGN exporter issues, but this
workspace is intended to behave like a drop-in PDK, so apply the small verified
patches when ALIGN imports the PDK.  Set ALIGN_SKY130_DISABLE_AUTO_PATCH=1 to
disable this behavior.
"""

from __future__ import annotations

import importlib
import importlib.util
import inspect
import os
import shutil
import warnings
from pathlib import Path


GDS_SENTINEL = "# ALIGN Sky130 compat: honor NoGDS layers"
PNR_SENTINEL = "# ALIGN Sky130 compat: top-level labels and NoGDS outline"
MAIN_SENTINEL = "# ALIGN Sky130 compat: promote Python stream-out to default GDS"
CONVERTER_PATCH_MARKER = "_sky130_compat_python_gds_default"


def _patch_gds_source(text: str) -> str:
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
        raise RuntimeError("Could not patch ALIGN gen_gds_json.py")
    return text


def _patch_pnr_source(text: str) -> str:
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
    text = text.replace(
        "                    if not skipGDS:\n"
        "                        for tag, suffix in [('lef', '.lef'), ('gdsjson', '.gds.json')]:\n"
        "                            path = results_dir / (variant + suffix)\n"
        "                            assert path.exists()\n"
        "                            variants[variant][tag] = path\n",
        "                    if not skipGDS:\n"
        "                        for tag, suffix in [('lef', '.lef'), ('gdsjson', '.gds.json')]:\n"
        "                            path = results_dir / (variant + suffix)\n"
        "                            assert path.exists()\n"
        "                            variants[variant][tag] = path\n"
        "                        if 'python_gds_json' in variants[variant]:\n"
        "                            variants[variant]['gdsjson'] = variants[variant]['python_gds_json']\n",
    )

    if PNR_SENTINEL not in text:
        raise RuntimeError("Could not patch ALIGN pnr/main.py")
    if "variants[variant]['gdsjson'] = variants[variant]['python_gds_json']" not in text:
        raise RuntimeError("Could not patch ALIGN pnr/main.py file-map GDS selection")
    return text


def _patch_main_source(text: str) -> str:
    if MAIN_SENTINEL in text:
        return text

    text = text.replace(
        "            if 'gdsjson' in filemap:\n"
        "                convert_GDSjson_GDS(filemap['gdsjson'], working_dir / f'{variant}.gds')\n"
        "                print(\"Use KLayout to visualize the generated GDS:\", working_dir / f'{variant}.gds')\n",
        f"            {MAIN_SENTINEL}\n"
        "            if 'gdsjson' in filemap:\n"
        "                gds_source = filemap.get('python_gds_json', filemap['gdsjson'])\n"
        "                convert_GDSjson_GDS(gds_source, working_dir / f'{variant}.gds')\n"
        "                print(\"Use KLayout to visualize the generated GDS:\", working_dir / f'{variant}.gds')\n",
    )
    text = text.replace(
        "                convert_GDSjson_GDS(filemap['python_gds_json'], regression_dir / f'{variant}.python.gds')\n"
        "                convert_GDSjson_GDS(filemap['gdsjson'], regression_dir / f'{variant}.gds')\n",
        "                convert_GDSjson_GDS(filemap['python_gds_json'], regression_dir / f'{variant}.python.gds')\n"
        "                convert_GDSjson_GDS(filemap.get('python_gds_json', filemap['gdsjson']), regression_dir / f'{variant}.gds')\n",
    )

    if MAIN_SENTINEL not in text:
        raise RuntimeError("Could not patch ALIGN main.py")
    return text


def _patch_file(path: Path, patcher) -> bool:
    original = path.read_text()
    patched = patcher(original)
    if patched == original:
        return False

    backup = path.with_suffix(path.suffix + ".sky130_compat_bak")
    if not backup.exists():
        shutil.copy2(path, backup)
    path.write_text(patched)
    return True


def _python_gdsjson_candidate(name: str | Path) -> Path | None:
    path = Path(name)
    if path.name.endswith(".python.gds.json"):
        return path
    if path.name.endswith(".gds.json"):
        candidate = path.with_name(path.name[: -len(".gds.json")] + ".python.gds.json")
        if candidate.exists():
            return candidate
    return None


def _patch_runtime_gds_converter(align_main) -> None:
    original = align_main.convert_GDSjson_GDS
    if getattr(original, CONVERTER_PATCH_MARKER, False):
        return

    def convert_python_gdsjson_by_default(name, oname):
        python_gdsjson = _python_gdsjson_candidate(name)
        if python_gdsjson is not None:
            return original(str(python_gdsjson), oname)
        return original(name, oname)

    setattr(convert_python_gdsjson_by_default, CONVERTER_PATCH_MARKER, True)
    align_main.convert_GDSjson_GDS = convert_python_gdsjson_by_default


def _refresh_align_main_bindings(align_main, pnr_main) -> None:
    if hasattr(align_main, "generate_pnr") and hasattr(pnr_main, "generate_pnr"):
        align_main.generate_pnr = pnr_main.generate_pnr


def apply_align_runtime_patches() -> None:
    if os.environ.get("ALIGN_SKY130_DISABLE_AUTO_PATCH"):
        return

    try:
        if importlib.util.find_spec("align") is None:
            return

        import align  # type: ignore
        import align.main as align_main  # type: ignore
        import align.cell_fabric.gen_gds_json as gen_gds_json  # type: ignore
        import align.pnr.main as pnr_main  # type: ignore

        align_root = Path(inspect.getfile(align)).resolve().parent
        main_path = align_root / "main.py"
        gds_path = align_root / "cell_fabric" / "gen_gds_json.py"
        pnr_path = align_root / "pnr" / "main.py"

        changed_main = _patch_file(main_path, _patch_main_source)
        changed_gds = _patch_file(gds_path, _patch_gds_source)
        changed_pnr = _patch_file(pnr_path, _patch_pnr_source)

        if changed_main:
            importlib.reload(align_main)
        if changed_gds:
            importlib.reload(gen_gds_json)
        if changed_pnr:
            importlib.reload(pnr_main)
        _refresh_align_main_bindings(align_main, pnr_main)
        _patch_runtime_gds_converter(align_main)
    except Exception as err:  # pragma: no cover - best-effort runtime bridge.
        warnings.warn(f"ALIGN Sky130 runtime auto-patch failed: {err}", RuntimeWarning)
