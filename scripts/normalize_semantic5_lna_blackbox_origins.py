#!/usr/bin/env python3
"""Translate frozen LNA hard macros to ALIGN's lower-left-origin contract.

The semantic-five LNA macros originate from official Magic PCells and are
centered around (0, 0).  ALIGN's black-box GDS-to-LEF path emits a positive
``SIZE`` but preserves those signed coordinates for pins.  This script applies
one rigid translation to every shape, instance, and label so the top-cell
bounds begin at (0, 0).  It does not alter shapes, connectivity, or a completed
layout GDS.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


SOURCE_MANIFEST = "semantic5_lna_blackbox_manifest.json"
OUTPUT_MANIFEST = "semantic5_lna_blackbox_origin_manifest.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _box_list(box) -> list[int]:
    return [int(box.left), int(box.bottom), int(box.right), int(box.top)]


def geometry_signature(layout, top) -> list[tuple[int, int, bool, int, int, int, int]]:
    signature = []
    for layer_index in layout.layer_indices():
        info = layout.get_info(layer_index)
        iterator = top.begin_shapes_rec(layer_index)
        while not iterator.at_end():
            shape = iterator.shape()
            if not shape.is_text():
                box = iterator.trans() * shape.bbox()
                signature.append(
                    (
                        info.layer,
                        info.datatype,
                        shape.is_box(),
                        box.left,
                        box.bottom,
                        box.right,
                        box.top,
                    )
                )
            iterator.next()
    return sorted(signature)


def translated_signature(signature: list[tuple], dx: int, dy: int) -> list[tuple]:
    return sorted(
        (layer, datatype, is_box, left + dx, bottom + dy, right + dx, top + dy)
        for layer, datatype, is_box, left, bottom, right, top in signature
    )


def text_signature(layout, top) -> list[tuple[int, int, str, int, int]]:
    signature = []
    for layer_index in layout.layer_indices():
        info = layout.get_info(layer_index)
        iterator = top.begin_shapes_rec(layer_index)
        while not iterator.at_end():
            shape = iterator.shape()
            if shape.is_text():
                text = shape.text
                point = iterator.trans() * text.trans.disp
                signature.append(
                    (info.layer, info.datatype, text.string, point.x, point.y)
                )
            iterator.next()
    return sorted(signature)


def translated_text_signature(signature: list[tuple], dx: int, dy: int) -> list[tuple]:
    return sorted(
        (layer, datatype, text, x + dx, y + dy)
        for layer, datatype, text, x, y in signature
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()

    try:
        import klayout.db as kdb  # type: ignore
    except ImportError:
        import pya as kdb  # type: ignore

    source_manifest_path = args.source_dir / SOURCE_MANIFEST
    source_manifest = json.loads(source_manifest_path.read_text(encoding="utf-8"))
    if source_manifest.get("schema") != "semantic5_lna_blackboxes_v1":
        raise ValueError("source must be the frozen semantic-five LNA v1 package")

    args.out_dir.mkdir(parents=True, exist_ok=False)
    records = []
    for source_record in source_manifest["records"]:
        source = args.source_dir / source_record["output_file"]
        if sha256(source) != source_record["output_sha256"]:
            raise ValueError(f"source digest mismatch: {source}")

        layout = kdb.Layout()
        layout.read(str(source))
        tops = layout.top_cells()
        if len(tops) != 1:
            raise ValueError(f"{source} has {len(tops)} top cells")
        top = tops[0]
        before_bbox = top.bbox()
        before_geometry = geometry_signature(layout, top)
        before_text = text_signature(layout, top)
        dx, dy = -before_bbox.left, -before_bbox.bottom
        if dx == 0 and dy == 0:
            raise ValueError(f"{source} is already lower-left normalized")

        top.transform(kdb.Trans(dx, dy))
        after_bbox = top.bbox()
        after_geometry = geometry_signature(layout, top)
        after_text = text_signature(layout, top)
        if after_bbox.left != 0 or after_bbox.bottom != 0:
            raise ValueError(f"failed to normalize {source}: {after_bbox}")
        if after_geometry != translated_signature(before_geometry, dx, dy):
            raise ValueError(f"non-rigid geometry change while translating {source}")
        if after_text != translated_text_signature(before_text, dx, dy):
            raise ValueError(f"non-rigid label change while translating {source}")

        output = args.out_dir / source.name
        save_options = kdb.SaveLayoutOptions()
        save_options.gds2_write_timestamps = False
        layout.write(str(output), save_options)
        records.append(
            {
                "target_cell": source_record["target_cell"],
                "source_file": source.name,
                "source_sha256": sha256(source),
                "output_file": output.name,
                "output_sha256": sha256(output),
                "before_bbox_dbu": _box_list(before_bbox),
                "after_bbox_dbu": _box_list(after_bbox),
                "translation_dbu": [dx, dy],
                "nontext_geometry_records": len(before_geometry),
                "text_records": len(before_text),
                "rigid_translation_only": True,
            }
        )

    manifest = {
        "schema": "semantic5_lna_blackbox_origins_v2",
        "classification": (
            "rigid_lower_left_origin_translation_of_frozen_official_magic_pcell_macros"
        ),
        "source_manifest": SOURCE_MANIFEST,
        "source_manifest_sha256": sha256(source_manifest_path),
        "final_gds_postprocessing": False,
        "shape_or_connectivity_change": False,
        "records": records,
    }
    manifest_path = args.out_dir / OUTPUT_MANIFEST
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
