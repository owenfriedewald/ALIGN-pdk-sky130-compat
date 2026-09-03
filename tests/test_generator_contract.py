import json
from pathlib import Path
import importlib.util
from types import SimpleNamespace

import pytest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "sky130_gen_param_contract", ROOT / "SKY130_PDK" / "gen_param.py"
)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

COMPAT_SPEC = importlib.util.spec_from_file_location(
    "sky130_align_compat_contract", ROOT / "SKY130_PDK" / "align_compat.py"
)
assert COMPAT_SPEC and COMPAT_SPEC.loader
COMPAT = importlib.util.module_from_spec(COMPAT_SPEC)
COMPAT_SPEC.loader.exec_module(COMPAT)

PLACEMENT_SPEC = importlib.util.spec_from_file_location(
    "sky130_placement_contract", ROOT / "SKY130_PDK" / "placement_contract.py"
)
assert PLACEMENT_SPEC and PLACEMENT_SPEC.loader
PLACEMENT = importlib.util.module_from_spec(PLACEMENT_SPEC)
PLACEMENT_SPEC.loader.exec_module(PLACEMENT)


def test_uniform_stack_accepts_homogeneous_group() -> None:
    values = {"M1": {"STACK": "2"}, "M2": {"STACK": "2"}}
    assert MODULE.uniform_int_parameter(values, "STACK", 1, "SCM_PMOS") == 2


def test_uniform_stack_rejects_heterogeneous_group() -> None:
    values = {"M1": {"STACK": "1"}, "M2": {"STACK": "2"}}
    with pytest.raises(ValueError, match="Unsupported heterogeneous STACK"):
        MODULE.uniform_int_parameter(values, "STACK", 1, "SCM_PMOS")


def test_uniform_stack_applies_default_per_member() -> None:
    values = {"M1": {}, "M2": {"STACK": "1"}}
    assert MODULE.uniform_int_parameter(values, "STACK", 1, "SCM_PMOS") == 1


def test_one_sided_body_tap_row_limit_matches_official_latchup_rule() -> None:
    assert MODULE.maximum_one_sided_body_tap_rows(15000, 28, 210) == 2


def test_decimal_mos_width_avoids_binary_float_truncation() -> None:
    assert MODULE.mos_width_to_nfin("4.2E-06", 210, "M1", "PMOS_TEST") == 20
    assert MODULE.mos_width_to_nfin("8.4E-07", 210, "M2", "NMOS_TEST") == 4
    assert (
        MODULE.mos_width_to_nfin(
            "1.6799999999999998E-06", 210, "M3", "PMOS_TEST"
        )
        == 8
    )


def test_decimal_mos_width_rejects_real_off_grid_value() -> None:
    with pytest.raises(ValueError, match="multiple of fin pitch:210"):
        MODULE.mos_width_to_nfin("1.0E-06", 210, "M1", "PMOS_TEST")


def test_mos_height_expands_only_when_wide_device_requires_dummy_fins() -> None:
    assert MODULE.mos_generator_height(4, 28) == 28
    assert MODULE.mos_generator_height(8, 28) == 28
    assert MODULE.mos_generator_height(12, 28) == 28
    assert MODULE.mos_generator_height(20, 28) == 36
    assert (36 - 20) // 2 == 8


def test_wide_mos_height_tightens_one_sided_body_tap_row_limit() -> None:
    height = MODULE.mos_generator_height(20, 28)
    assert MODULE.maximum_one_sided_body_tap_rows(15000, height, 210) == 1


def test_mos_aspect_variants_exclude_rows_beyond_body_tap_reach() -> None:
    primitives = {}
    args = {
        "primitive": "MOS",
        "x_cells": 12,
        "y_cells": 1,
        "parameters": {},
    }

    MODULE.add_primitive(primitives, "PMOS_TEST", args, max_y_cells=2)

    assert sorted(primitives) == ["PMOS_TEST_X12_Y1", "PMOS_TEST_X6_Y2"]
    assert all(value["y_cells"] <= 2 for value in primitives.values())


def test_non_mos_aspect_variants_remain_unfiltered_by_default() -> None:
    primitives = {}
    args = {
        "primitive": "TEST",
        "x_cells": 12,
        "y_cells": 1,
    }

    MODULE.add_primitive(primitives, "GENERIC_TEST", args)

    assert "GENERIC_TEST_X4_Y3" in primitives


def test_native_export_capability_requires_all_three_generic_fixes() -> None:
    def translate_data():
        no_gds_layers = set()
        return no_gds_layers

    native_pnr = SimpleNamespace(
        _top_level_label_names=lambda hierarchy: [],
        _use_python_gds_streamout=lambda pdk: True,
    )
    legacy_pnr = SimpleNamespace(_top_level_label_names=lambda hierarchy: [])
    gds = SimpleNamespace(translate_data=translate_data)

    assert COMPAT._native_export_supported(gds, native_pnr) is True
    assert COMPAT._native_export_supported(gds, legacy_pnr) is False


def test_nwell_half_spacing_halo_is_placement_grid_aligned() -> None:
    assert PLACEMENT.half_spacing_halo(1270, 430) == 860
    assert PLACEMENT.half_spacing_halo(1270, 420) == 840


def test_two_nwell_halos_guarantee_the_official_spacing() -> None:
    halo_x = PLACEMENT.half_spacing_halo(1270, 430)
    halo_y = PLACEMENT.half_spacing_halo(1270, 420)

    assert 2 * halo_x >= 1270
    assert 2 * halo_y >= 1270
    assert PLACEMENT.expand_bbox(
        (0, 0, 2580, 7560), halo_x=halo_x, halo_y=halo_y
    ) == (-860, -840, 3440, 8400)


def test_placement_routing_channels_leave_one_interior_signal_track() -> None:
    with (ROOT / "SKY130_PDK" / "layers.json").open(encoding="utf-8") as stream:
        pdk = json.load(stream)

    design = pdk["design_info"]
    layers = {entry["Layer"]: entry for entry in pdk["Abstraction"]}

    assert design["bottom_signal_routing_layer"] == "M1"
    assert layers["M1"]["Direction"] == "V"
    assert layers["M2"]["Direction"] == "H"
    # A one-pitch boundary-to-boundary gap contains no guaranteed interior
    # centerline once macro obstruction and wire width are considered.  Two
    # pitches preserve one routable track between adjacent hard macros.
    assert design["Hspace"] == 2 * layers["M1"]["Pitch"] == 860
    assert design["Vspace"] == 2 * layers["M2"]["Pitch"] == 840
