#!/usr/bin/env python3
"""Build fixed LNA macro GDS files from official Magic PCell references.

Only cell and port-label names are changed.  Device geometry and layer shapes
remain geometrically identical to the reference layouts.
The generated macros are consumed by ALIGN's existing ``--blackbox_dir`` flow;
they are not postprocessed into a completed campaign GDS.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


SPECS = (
    {
        "reference": "SKY130_RES_HIGH_PO_1P41_R15EQ_REFERENCE.gds",
        "target": "SKY130_FD_PR__RES_HIGH_PO_0P35_MGFMH8",
        "labels": {
            "B": "W_N201_N2098#",
            "R1": "A_N35_N1932#",
            "R2": "A_N35_1500#",
        },
    },
    {
        "reference": "SKY130_RES_HIGH_PO_1P41_R8EQ_REFERENCE.gds",
        "target": "SKY130_FD_PR__RES_HIGH_PO_0P35_V3QVRN",
        "labels": {
            "B": "W_N201_N1398#",
            "R1": "A_N35_N1232#",
            "R2": "A_N35_800#",
        },
    },
    {
        "reference": "SKY130_CAP_MIM_M3_2_L30W30_REFERENCE.gds",
        "target": "SKY130_FD_PR__CAP_MIM_M3_2_LJ5JLG",
        "labels": {
            "C1": "C2_N3251_N3000#",
            "C2": "M4_N3351_N3100#",
        },
    },
    {
        "reference": "SKY130_DIODE_PD2NW_05V5_A4_REFERENCE.gds",
        "target": "SKY130_FD_PR__DIODE_PD2NW_05V5_WW7YB9",
        "labels": {
            "D1": "A_N200_N200#",
            "D2": "W_N338_N338#",
        },
    },
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def signature_sha256(signature: list[tuple]) -> str:
    payload = json.dumps(signature, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def geometry_signature(layout, top) -> list[tuple]:
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


def rewrite_labels(layout, top, label_map: dict[str, str]) -> None:
    observed = set()
    for layer_index in layout.layer_indices():
        shapes = top.shapes(layer_index)
        for shape in shapes.each():
            if not shape.is_text():
                continue
            text = shape.text
            observed.add(text.string)
            if text.string not in label_map:
                raise ValueError(f"unexpected reference label {text.string!r}")
            text.string = label_map[text.string]
            shape.text = text
    if observed != set(label_map):
        raise ValueError(
            f"reference labels differ: expected={sorted(label_map)} "
            f"observed={sorted(observed)}"
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference-dir", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--openpdks-image-digest", required=True)
    parser.add_argument("--openpdks-sky130a-commit", required=True)
    args = parser.parse_args()

    try:
        import klayout.db as kdb  # type: ignore
    except ImportError:
        import pya as kdb  # type: ignore

    args.out_dir.mkdir(parents=True, exist_ok=True)
    records = []
    for spec in SPECS:
        reference = args.reference_dir / spec["reference"]
        if not reference.is_file():
            raise FileNotFoundError(reference)
        layout = kdb.Layout()
        layout.read(str(reference))
        tops = layout.top_cells()
        if len(tops) != 1:
            raise ValueError(f"{reference} has {len(tops)} top cells")
        top = tops[0]
        before = geometry_signature(layout, top)
        rewrite_labels(layout, top, spec["labels"])
        label_only = geometry_signature(layout, top)
        if before != label_only:
            raise ValueError(f"geometry changed while relabeling {reference}")
        top.name = spec["target"]
        after = geometry_signature(layout, top)
        if before != after:
            raise ValueError(f"nontext geometry changed for {reference}")

        output = args.out_dir / f"{spec['target']}.gds"
        save_options = kdb.SaveLayoutOptions()
        save_options.gds2_write_timestamps = False
        layout.write(str(output), save_options)
        records.append(
            {
                "target_cell": spec["target"],
                "output_file": output.name,
                "output_sha256": sha256(output),
                "reference_file": reference.name,
                "reference_sha256": sha256(reference),
                "reference_geometry_sha256": signature_sha256(before),
                "port_label_map": spec["labels"],
                "nontext_geometry_records": len(before),
                "geometry_changed": False,
            }
        )

    manifest = {
        "schema": "semantic5_lna_blackboxes_v1",
        "classification": "official_magic_pcell_geometry_with_cell_and_port_label_normalization_only",
        "final_gds_postprocessing": False,
        "openpdks_image_digest": args.openpdks_image_digest,
        "openpdks_sky130a_commit": args.openpdks_sky130a_commit,
        "records": records,
    }
    manifest_path = args.out_dir / "semantic5_lna_blackbox_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
