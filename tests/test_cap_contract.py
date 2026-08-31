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
        {"layer": "M4", "netName": "MINUS", "netType": "pin", "rect": [10, 70, 90, 80]},
        {"layer": "M4", "netName": None, "netType": "drawing", "rect": [70, 50, 80, 75]},
        {"layer": "M4", "netName": None, "netType": "drawing", "rect": [15, 20, 80, 70]},
        {"layer": "CapMIMLayer", "netName": None, "netType": "drawing", "rect": [20, 25, 75, 65]},
        {"layer": "CapMIMContact", "netName": None, "netType": "drawing", "rect": [20, 30, 30, 40]},
        {"layer": "M5", "netName": "PLUS", "netType": "drawing", "rect": [18, 10, 32, 50]},
        {"layer": "V4", "netName": "PLUS", "netType": "drawing", "rect": [20, 5, 30, 15]},
        {"layer": "M4", "netName": "PLUS", "netType": "pin", "rect": [5, 0, 45, 10]},
    ]


def valid_cap_terminals_with_halo():
    terminals = valid_cap_terminals()
    terminals.extend(
        [
            {"layer": "M4", "netName": None, "netType": "blockage", "rect": [5, 10, 15, 80]},
            {"layer": "M4", "netName": None, "netType": "blockage", "rect": [80, 10, 90, 80]},
            {"layer": "M4", "netName": None, "netType": "blockage", "rect": [15, 10, 80, 20]},
        ]
    )
    terminals.append(
        {"layer": "Boundary", "netName": "Boundary", "netType": "drawing", "rect": [0, 0, 100, 100]}
    )
    return terminals


def test_valid_mim_terminal_topology_passes() -> None:
    MODULE.validate_cap_terminal_topology(valid_cap_terminals(), m4_pitch=5)


def test_valid_mim_terminal_topology_passes_with_exact_unrelated_spacing() -> None:
    MODULE.validate_cap_terminal_topology(
        valid_cap_terminals(), unrelated_m4_spacing=15
    )


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
    terminals[-1]["rect"] = [5, 2, 45, 12]

    with pytest.raises(ValueError, match="M4 routing pin is off grid"):
        MODULE.validate_cap_terminal_topology(terminals, m4_pitch=5)


def test_reversed_official_plate_assignment_is_rejected() -> None:
    terminals = valid_cap_terminals()
    for terminal in terminals:
        if terminal.get("netName") == "PLUS":
            terminal["netName"] = "MINUS"
        elif terminal.get("netName") == "MINUS":
            terminal["netName"] = "PLUS"

    with pytest.raises(ValueError, match="PLUS M5 top-plate strap"):
        MODULE.validate_cap_terminal_topology(terminals)


def test_disconnected_minus_access_chain_is_rejected() -> None:
    terminals = valid_cap_terminals()
    terminals[1]["rect"] = [90, 50, 100, 65]

    with pytest.raises(ValueError, match="MINUS pin does not reach"):
        MODULE.validate_cap_terminal_topology(terminals)


def test_insufficient_capm_to_unrelated_m4_spacing_is_rejected() -> None:
    with pytest.raises(ValueError, match="CAPM clearance to unrelated PLUS M4"):
        MODULE.validate_cap_terminal_topology(
            valid_cap_terminals(), unrelated_m4_spacing=16
        )


def test_complete_routing_halo_passes() -> None:
    MODULE.validate_cap_terminal_topology(
        valid_cap_terminals_with_halo(),
        unrelated_m4_spacing=15,
        require_routing_halo=True,
    )


def test_incomplete_routing_halo_is_rejected() -> None:
    terminals = valid_cap_terminals_with_halo()
    terminals.pop(-2)
    with pytest.raises(ValueError, match="routing-only M4 halo"):
        MODULE.validate_cap_terminal_topology(
            terminals,
            unrelated_m4_spacing=15,
            require_routing_halo=True,
        )
