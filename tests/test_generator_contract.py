from pathlib import Path
import importlib.util

import pytest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "sky130_gen_param_contract", ROOT / "SKY130_PDK" / "gen_param.py"
)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


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
