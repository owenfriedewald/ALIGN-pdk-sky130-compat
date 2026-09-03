from pathlib import Path
import importlib.util
import json

import pytest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "sky130_res_contract", ROOT / "SKY130_PDK" / "res_contract.py"
)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def pdk_layers():
    data = json.loads((ROOT / "SKY130_PDK" / "layers.json").read_text())
    return {entry["Layer"]: entry for entry in data["Abstraction"]}


class IndexOnlyPdk:
    """Minimal stand-in for ALIGN's runtime Pdk facade."""

    def __init__(self, layers):
        self.layers = layers

    def __getitem__(self, layer):
        return self.layers[layer]


def test_resistor_routing_uses_authoritative_sky130_metal_rules() -> None:
    pdk = pdk_layers()
    rules = MODULE.resistor_routing_rules(pdk)
    assert rules == {
        layer: {"pitch": pdk[layer]["Pitch"], "width": pdk[layer]["Width"]}
        for layer in ("M1", "M2", "M3")
    }
    assert not any(key.startswith("m1") for key in pdk["Cap"])


def test_resistor_routing_accepts_align_index_only_pdk_facade() -> None:
    pdk = pdk_layers()
    rules = MODULE.resistor_routing_rules(IndexOnlyPdk(pdk))
    assert rules == {
        layer: {"pitch": pdk[layer]["Pitch"], "width": pdk[layer]["Width"]}
        for layer in ("M1", "M2", "M3")
    }


def test_resistor_routing_rejects_nonphysical_geometry() -> None:
    pdk = pdk_layers()
    pdk["M2"] = dict(pdk["M2"], Width=pdk["M2"]["Pitch"])
    with pytest.raises(ValueError, match="invalid resistor routing geometry for M2"):
        MODULE.resistor_routing_rules(pdk)
