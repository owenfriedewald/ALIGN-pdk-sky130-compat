from pathlib import Path
import importlib.util

import pytest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "sky130_normalize_netlist", ROOT / "scripts" / "normalize_netlist.py"
)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_only_selected_ideal_capacitor_is_reclassified_as_mim() -> None:
    source = (
        ".subckt top plus minus spare\n"
        "C2 plus minus 500f\n"
        "C3 plus spare 100f\n"
        ".ends top\n"
    )

    normalized = MODULE.normalize_text(
        source,
        uppercase_nets=True,
        mim_cap_instances={"C2"},
    )

    assert (
        "XC2 PLUS MINUS sky130_fd_pr__cap_mim_m3_1 l=15.812 w=15.812"
        in normalized
    )
    assert "C3 plus spare 100f" in normalized


def test_explicit_mim_dimensions_override_value_derived_sizing() -> None:
    normalized = MODULE.normalize_text(
        "C2 top bot 500f l=15.812u w=15.814u\n",
        mim_cap_instances={"c2"},
    )

    assert normalized == (
        "XC2 top bot sky130_fd_pr__cap_mim_m3_1 l=15.812 w=15.814\n"
    )


def test_half_specified_mim_dimensions_are_rejected() -> None:
    with pytest.raises(ValueError, match="both L and W"):
        MODULE.normalize_text(
            "C2 top bot 500f l=15.812u\n",
            mim_cap_instances={"C2"},
        )
