from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MACRO_ROOT = ROOT / "SKY130_PDK" / "blackboxes" / "semantic5_lna_v1"
MANIFEST = MACRO_ROOT / "semantic5_lna_blackbox_manifest.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_semantic5_lna_macro_manifest_binds_exact_gds() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert manifest["schema"] == "semantic5_lna_blackboxes_v1"
    assert manifest["final_gds_postprocessing"] is False
    assert manifest["classification"] == (
        "official_magic_pcell_geometry_with_cell_and_port_label_normalization_only"
    )
    assert manifest["openpdks_image_digest"] == (
        "sha256:ae380e2b0b96bd57b91f5864623ed488d00f78eaf58caf7f7d9d3754d315df38"
    )
    assert manifest["openpdks_sky130a_commit"] == (
        "54435919abffb937387ec956209f9cf5fd2dfbee"
    )

    expected = {
        "SKY130_FD_PR__RES_HIGH_PO_0P35_MGFMH8.gds": (
            "a90a54179ab3eee29690aae97259ba78bdace9cf7e90cd0740a64a700fda44e5"
        ),
        "SKY130_FD_PR__RES_HIGH_PO_0P35_V3QVRN.gds": (
            "b2877f1be6579b3f6fb6d6733e08f55cacd303343cdf0331bd6f80fe92655a9c"
        ),
        "SKY130_FD_PR__CAP_MIM_M3_2_LJ5JLG.gds": (
            "0049779a42c4d2bd6a366f01680aff0de16abffb804ff3c0fb6db3cbb3a60361"
        ),
        "SKY130_FD_PR__DIODE_PD2NW_05V5_WW7YB9.gds": (
            "45a55692719ffacbb80fe93e60c95deeefe1d9fd7f5156d9a744026910693d23"
        ),
    }
    records = {record["output_file"]: record for record in manifest["records"]}
    assert set(records) == set(expected)
    for filename, digest in expected.items():
        assert records[filename]["output_sha256"] == digest
        assert records[filename]["geometry_changed"] is False
        assert sha256(MACRO_ROOT / filename) == digest


def test_true_lvt_is_an_enabled_mos_generator_variant() -> None:
    layers = json.loads((ROOT / "SKY130_PDK" / "layers.json").read_text())
    assert "LVT" in layers["design_info"]["vt_type"]


def test_reference_builder_uses_drc_capable_compatible_resistor_variant() -> None:
    source = (ROOT / "scripts" / "generate_semantic5_device_references.tcl").read_text(
        encoding="utf-8"
    )
    assert source.count("sky130::sky130_fd_pr__res_high_po_1p41") == 2
    assert "[dict create l 60.43 w 1.41" in source
    assert "[dict create l 32.23 w 1.41" in source
    assert "sky130::sky130_fd_pr__res_high_po_0p35" not in source

    builder = (ROOT / "scripts" / "build_semantic5_lna_blackboxes.py").read_text(
        encoding="utf-8"
    )
    assert "gds2_write_timestamps = False" in builder
    assert "enforce_rpm_min_width" not in builder
