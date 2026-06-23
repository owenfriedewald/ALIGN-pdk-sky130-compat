#!/usr/bin/env python3
"""Report MOS grouped-primitive unit-cell sizing risks.

This is a read-only diagnostic helper for ALIGN Sky130 generated outputs.  It
checks `2_primitives/__primitives__.json` files and highlights grouped MOS
primitives where the current ALIGN Sky130 generator had to round a fractional
unit-cell count.  Those cases are likely to extract with a different physical
device count than the source schematic after `nf * stack` expansion.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _as_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _mos_devices(parameters: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        name: params
        for name, params in parameters.items()
        if isinstance(params, dict) and "NF" in params
    }


def analyze(path: Path) -> int:
    data = json.loads(path.read_text())
    rows: list[dict[str, Any]] = []

    for name, primitive in sorted(data.items()):
        if not isinstance(primitive, dict):
            continue
        params = primitive.get("parameters", {})
        if not isinstance(params, dict):
            continue
        devices = _mos_devices(params)
        if not devices:
            continue

        x_cells = _as_int(primitive.get("x_cells"))
        y_cells = _as_int(primitive.get("y_cells"))
        unit_cells = x_cells * y_cells
        stack = _as_int(primitive.get("stack"), 1) or 1
        nf_values = {
            dev_name: _as_int(dev_params.get("NF"))
            for dev_name, dev_params in devices.items()
        }
        m_values = {
            dev_name: _as_int(dev_params.get("M"), 1) or 1
            for dev_name, dev_params in devices.items()
        }
        total_nf_m = sum(nf_values[d] * m_values[d] for d in devices)
        expanded_devices = total_nf_m * stack
        current_formula_units = total_nf_m / (2 * len(devices))
        fractional = current_formula_units != int(current_formula_units)
        unequal_nf = len(set(nf_values.values())) > 1

        rows.append(
            {
                "name": name,
                "unit_cells": unit_cells,
                "formula_units": current_formula_units,
                "fractional": fractional,
                "unequal_nf": unequal_nf,
                "stack": stack,
                "expanded_devices": expanded_devices,
                "nf_values": nf_values,
            }
        )

    print(f"source: {path}")
    print(
        "primitive, unit_cells, formula_units, expanded_devices, stack, "
        "nf_by_device, risk"
    )
    risky = 0
    for row in rows:
        risks = []
        if row["fractional"]:
            risks.append("fractional_unit_rounding")
        if row["unequal_nf"]:
            risks.append("unequal_nf_group")
        if row["fractional"] and row["unequal_nf"]:
            risks.append("high_lvs_count_risk")
        if risks:
            risky += 1
        risk_text = ",".join(risks) if risks else "none"
        nf_text = ";".join(f"{k}={v}" for k, v in sorted(row["nf_values"].items()))
        print(
            f"{row['name']}, {row['unit_cells']}, "
            f"{row['formula_units']:.3f}, {row['expanded_devices']}, "
            f"{row['stack']}, {nf_text}, {risk_text}"
        )

    print(f"risk_count: {risky}")
    return 1 if risky else 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Analyze ALIGN Sky130 grouped MOS primitive unit-cell sizing."
    )
    parser.add_argument(
        "primitives_json",
        type=Path,
        help="Path to a generated 2_primitives/__primitives__.json file.",
    )
    args = parser.parse_args()
    return analyze(args.primitives_json)


if __name__ == "__main__":
    raise SystemExit(main())
