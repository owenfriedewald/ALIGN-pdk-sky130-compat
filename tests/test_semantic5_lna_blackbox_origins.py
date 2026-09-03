from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MACRO_ROOT = ROOT / "SKY130_PDK" / "blackboxes" / "semantic5_lna_v2"
MANIFEST = MACRO_ROOT / "semantic5_lna_blackbox_origin_manifest.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_lna_v2_macros_are_digest_bound_rigid_origin_translations() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert manifest["schema"] == "semantic5_lna_blackbox_origins_v2"
    assert manifest["final_gds_postprocessing"] is False
    assert manifest["shape_or_connectivity_change"] is False
    assert manifest["classification"] == (
        "rigid_lower_left_origin_translation_of_frozen_official_magic_pcell_macros"
    )
    assert len(manifest["records"]) == 4
    for record in manifest["records"]:
        assert record["rigid_translation_only"] is True
        assert record["after_bbox_dbu"][:2] == [0, 0]
        before = record["before_bbox_dbu"]
        after = record["after_bbox_dbu"]
        assert before[2] - before[0] == after[2] - after[0]
        assert before[3] - before[1] == after[3] - after[1]
        assert record["translation_dbu"] == [-before[0], -before[1]]
        assert sha256(MACRO_ROOT / record["output_file"]) == record["output_sha256"]


def test_origin_normalizer_explicitly_verifies_rigid_geometry_and_labels() -> None:
    source = (
        ROOT / "scripts" / "normalize_semantic5_lna_blackbox_origins.py"
    ).read_text(encoding="utf-8")
    assert "after_geometry != translated_signature" in source
    assert "after_text != translated_text_signature" in source
    assert "top.transform(kdb.Trans(dx, dy))" in source
    assert "gds2_write_timestamps = False" in source


def test_lna_mim_cap_top_plate_is_within_signal_routing_stack() -> None:
    layers = json.loads((ROOT / "SKY130_PDK" / "layers.json").read_text())
    assert layers["design_info"]["top_signal_routing_layer"] == "M6"
    abstraction = {entry["Layer"]: entry for entry in layers["Abstraction"]}
    assert abstraction["M6"]["GdsLayerNo"] == 72
    assert abstraction["V5"]["Stack"] == ["M5", "M6"]
