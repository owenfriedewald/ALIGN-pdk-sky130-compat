from pathlib import Path
import importlib.util

import pytest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "sky130_cap_contract", ROOT / "SKY130_PDK" / "cap_contract.py"
)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def valid_cap_terminals():
    return [
        {"layer": "M4", "netName": "PLUS", "netType": "pin", "rect": [10, 70, 90, 80]},
        {"layer": "M4", "netName": None, "netType": "drawing", "rect": [70, 50, 80, 75]},
        {"layer": "M4", "netName": None, "netType": "drawing", "rect": [15, 20, 80, 70]},
        {"layer": "CapMIMLayer", "netName": None, "netType": "drawing", "rect": [20, 25, 75, 65]},
        {"layer": "CapMIMContact", "netName": None, "netType": "drawing", "rect": [20, 30, 30, 40]},
        {"layer": "M5", "netName": "MINUS", "netType": "drawing", "rect": [18, 10, 32, 50]},
        {"layer": "V4", "netName": "MINUS", "netType": "drawing", "rect": [20, 5, 30, 15]},
        {"layer": "M4", "netName": "MINUS", "netType": "pin", "rect": [5, 0, 45, 10]},
    ]


def test_valid_mim_terminal_topology_passes() -> None:
    MODULE.validate_cap_terminal_topology(valid_cap_terminals(), m4_pitch=5)


def test_cross_net_m4_overlap_is_rejected() -> None:
    terminals = valid_cap_terminals()
    terminals[-1]["rect"] = [5, 65, 45, 75]

    with pytest.raises(ValueError, match="PLUS and MINUS M4 conductors overlap"):
        MODULE.validate_cap_terminal_topology(terminals)


def test_named_capm_device_layer_is_rejected() -> None:
    terminals = valid_cap_terminals()
    terminals[3]["netName"] = "MINUS"

    with pytest.raises(ValueError, match="independent routing net"):
        MODULE.validate_cap_terminal_topology(terminals)


def test_disconnected_mim_contact_is_rejected() -> None:
    terminals = valid_cap_terminals()
    terminals[4]["rect"] = [100, 100, 110, 110]

    with pytest.raises(ValueError, match="does not overlap CAPM"):
        MODULE.validate_cap_terminal_topology(terminals)


def test_off_grid_plus_pin_is_rejected() -> None:
    terminals = valid_cap_terminals()
    terminals[0]["rect"] = [10, 72, 90, 82]

    with pytest.raises(ValueError, match="M4 routing pin is off grid"):
        MODULE.validate_cap_terminal_topology(terminals, m4_pitch=5)


def test_disconnected_plus_access_chain_is_rejected() -> None:
    terminals = valid_cap_terminals()
    terminals[1]["rect"] = [90, 50, 100, 65]

    with pytest.raises(ValueError, match="PLUS pin does not reach"):
        MODULE.validate_cap_terminal_topology(terminals)
